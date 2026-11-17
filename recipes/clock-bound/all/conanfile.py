import shutil
from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import cross_building
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class ClockBoundConan(ConanFile):
    name = "clock-bound"
    description = ("AWS ClockBound: the clockbound daemon, which disciplines the system clock and publishes "
                   "a bound on its error, and libclockbound, the C client library that reads that bound.")
    license = "Apache-2.0 OR MIT"
    url = "https://github.com/scylladb/scylladb-conan-index"
    homepage = "https://github.com/aws/clock-bound"
    topics = ("clock", "time", "ntp", "aws", "clockbound")
    package_type = "library"
    # Rust code behind a plain C ABI, always built with cargo's release profile (as ScyllaDB
    # does in every build mode), so neither the C/C++ compiler nor build_type affect the binary
    settings = "os", "arch"
    options = {
        "shared": [True, False],
        "daemon": [True, False],
    }
    # Static by default: ScyllaDB links libclockbound.a into its binaries
    default_options = {
        "shared": False,
        "daemon": True,
    }
    exports_sources = "clockbound-install-service"

    def export_sources(self):
        export_conandata_patches(self)

    # The release profile of the clock-bound workspace is tuned for its daemon: fat LTO, one
    # codegen unit, panic=abort, stripped. With fat LTO libclockbound.a is a single object that
    # carries the Rust runtime, which clashes (duplicate symbols) with any other Rust static
    # library in the same link, such as ScyllaDB's librust_combined.a. The library is built with
    # cargo's defaults for those settings instead, which keeps the runtime in archive members of
    # its own. Same flags as ScyllaDB's configure.py / rust/CMakeLists.txt.
    # libclockbound.so has no such problem: it keeps its Rust runtime to itself and exports
    # only the clockbound_* symbols, so it is built with upstream's profile.
    _lib_cargo_config = ("--config profile.release.strip=false "
                         "--config profile.release.lto=false "
                         "--config profile.release.codegen-units=16 "
                         "--config 'profile.release.panic=\"unwind\"'")

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("ClockBound only supports Linux")

    def validate_build(self):
        if cross_building(self):
            raise ConanInvalidConfiguration("Cross-building clock-bound is not supported by this recipe")
        if shutil.which("cargo") is None:
            raise ConanInvalidConfiguration(
                "Building clock-bound needs a Rust toolchain (cargo, Rust >= 1.85) in PATH")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def _cargo(self, command, args, rustc_args=""):
        # --locked: resolve exactly what the workspace's Cargo.lock pins. cargo downloads the
        # crates from crates.io on the first build.
        self.run(f"cargo {command} --locked --release {args} "
                 f"--manifest-path={Path(self.source_folder) / 'Cargo.toml'} "
                 f"--target-dir={self.build_folder} {rustc_args}",
                 env="conanbuild")

    def build(self):
        if self.options.shared:
            # rustc sets no SONAME on a cdylib. Without one, a consumer that links the library
            # by its full path (as CMake does) records that path, a Conan cache path, as its
            # DT_NEEDED entry.
            self._cargo("rustc", "-p clock-bound-ffi --crate-type cdylib",
                        "-- -C link-arg=-Wl,-soname,libclockbound.so")
        else:
            self._cargo("rustc", f"{self._lib_cargo_config} -p clock-bound-ffi --crate-type staticlib")
        if self.options.daemon:
            # The daemon keeps upstream's release profile
            self._cargo("build", "-p clock-bound --features daemon --bins")

    def package(self):
        source = Path(self.source_folder)
        release = Path(self.build_folder) / "release"
        package = Path(self.package_folder)

        copy(self, "LICENSE", source / "clock-bound-ffi", package / "licenses")
        copy(self, "NOTICE", source / "clock-bound-ffi", package / "licenses")
        copy(self, "LICENSE.*", source / "clock-bound", package / "licenses")

        # Client
        copy(self, "clockbound.h", source / "clock-bound-ffi" / "include", package / "include")
        copy(self, "libclockbound.so" if self.options.shared else "libclockbound.a", release, package / "lib")

        # Service: the files of upstream's clockbound RPM, plus the sample configuration.
        # The unit expects /usr/bin/clockbound and /etc/clockbound.toml, so the daemon has to
        # be installed on the host to run: bin/clockbound-install-service does that.
        if self.options.daemon:
            assets = source / "clock-bound" / "assets"
            copy(self, "clockbound", release, package / "bin")
            copy(self, "cbctl", release, package / "bin")
            copy(self, "configure_phc", assets, package / "bin")
            # 0644 in the repository; upstream's RPM installs it 0755
            (package / "bin" / "configure_phc").chmod(0o755)
            copy(self, "clockbound-install-service", self.export_sources_folder, package / "bin")
            (package / "bin" / "clockbound-install-service").chmod(0o755)
            copy(self, "clockbound.service", assets, package / "res" / "systemd")
            copy(self, "clockbound.logrotate", assets, package / "res" / "logrotate")
            copy(self, "example-config*.toml", assets, package / "res" / "config")

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "clockbound")
        self.cpp_info.set_property("cmake_target_name", "clockbound::clockbound")
        self.cpp_info.set_property("pkg_config_name", "clockbound")
        self.cpp_info.libs = ["clockbound"]
        if not self.options.shared:
            # What `rustc --print native-static-libs` asks for
            self.cpp_info.system_libs = ["gcc_s", "util", "rt", "pthread", "m", "dl"]
        if self.options.daemon:
            self.cpp_info.resdirs = ["res"]

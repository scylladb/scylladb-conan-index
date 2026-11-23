from pathlib import Path

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, get
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class SccacheConan(ConanFile):
    name = "sccache"
    description = ("sccache: a ccache-like compiler cache with local disk and cloud storage "
                   "backends, supporting C/C++ (gcc, clang, MSVC), Rust and CUDA.")
    license = "Apache-2.0"
    url = "https://github.com/scylladb/scylladb-conan-index"
    homepage = "https://github.com/mozilla/sccache"
    topics = ("cache", "compiler", "ccache", "build", "pre-built")
    package_type = "application"
    # Upstream's prebuilt release binaries; they depend on neither the compiler nor build_type
    settings = "os", "arch"

    def layout(self):
        basic_layout(self, src_folder="src")

    def validate(self):
        if self.settings.os != "Linux":
            raise ConanInvalidConfiguration("This recipe only supports Linux")
        if str(self.settings.arch) not in self.conan_data["sources"][self.version]["Linux"]:
            raise ConanInvalidConfiguration(
                f"No upstream sccache {self.version} binary for {self.settings.os}/{self.settings.arch}")

    def source(self):
        # Prebuilt binaries are per platform: downloaded in build()
        pass

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.os)][str(self.settings.arch)],
            destination=self.source_folder, strip_root=True)

    def package(self):
        source = Path(self.source_folder)
        package = Path(self.package_folder)
        copy(self, "LICENSE", source, package / "licenses")
        copy(self, "sccache", source, package / "bin")

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = ["bin"]

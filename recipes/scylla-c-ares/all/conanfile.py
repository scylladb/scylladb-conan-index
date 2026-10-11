from pathlib import Path

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir

required_conan_version = ">=2.0"


class ScyllaCAresConan(ConanFile):
    name = "scylla-c-ares"
    description = ("A C library for asynchronous DNS requests: upstream c-ares plus the fixes "
                   "ScyllaDB carries in its c-ares submodule (github.com/scylladb/c-ares).")
    license = "MIT"
    url = "https://github.com/scylladb/c-ares"
    homepage = "https://c-ares.org"
    topics = ("dns", "resolver", "async")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "tools": [True, False],
    }
    # ScyllaDB links c-ares statically (and position-independent) into Seastar, without the tools
    default_options = {
        "shared": False,
        "fPIC": True,
        "tools": False,
    }
    # A drop-in replacement for ConanCenter's c-ares: the two can't coexist in one graph
    provides = "c-ares"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["CARES_STATIC"] = not self.options.shared
        tc.cache_variables["CARES_SHARED"] = bool(self.options.shared)
        tc.cache_variables["CARES_STATIC_PIC"] = bool(self.options.get_safe("fPIC", True))
        tc.cache_variables["CARES_BUILD_TOOLS"] = bool(self.options.tools)
        tc.cache_variables["CARES_BUILD_TESTS"] = False
        tc.cache_variables["CARES_BUILD_CONTAINER_TESTS"] = False
        tc.cache_variables["CARES_THREADS"] = True
        # c-ares 1.34 declares cmake_minimum_required(VERSION 3.5.0...3.10.0), which CMake 4 rejects
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.10"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        package = Path(self.package_folder)
        copy(self, "LICENSE.md", self.source_folder, package / "licenses")
        cmake = CMake(self)
        cmake.install()
        for folder in (package / "lib" / "cmake", package / "lib" / "pkgconfig", package / "share"):
            rmdir(self, folder)

    def package_info(self):
        # Same names as ConanCenter's c-ares and c-ares' own config, which Seastar's
        # find_package(c-ares) expects
        self.cpp_info.set_property("cmake_file_name", "c-ares")
        self.cpp_info.set_property("cmake_target_name", "c-ares::cares")
        self.cpp_info.set_property("pkg_config_name", "libcares")
        self.cpp_info.libs = ["cares"]
        if not self.options.shared:
            self.cpp_info.defines.append("CARES_STATICLIB")
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs.extend(["rt", "pthread"])

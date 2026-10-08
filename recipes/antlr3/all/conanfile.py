import textwrap

from conan import ConanFile
from conan.tools.files import copy, save
from conan.tools.layout import basic_layout

required_conan_version = ">=2.0"


class Antlr3Conan(ConanFile):
    name = "antlr3"
    version = "3.5.3"
    description = ("ANTLR v3 parser generator: the antlr-complete tool jar (with an 'antlr3' "
                   "launcher) and the header-only C++ runtime, patched as used by ScyllaDB.")
    license = "BSD-3-Clause"
    url = "https://github.com/scylladb/scylladb"
    homepage = "https://www.antlr3.org"
    topics = ("antlr", "parser", "generator", "grammar", "header-only")
    package_type = "header-library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_openjdk": [True, False],
    }
    default_options = {
        # By default the launcher uses the system 'java' (or $JAVA_HOME/bin/java).
        "with_openjdk": False,
    }
    no_copy_source = True

    # ANTLR 3 is unmaintained upstream, so everything is vendored here instead of downloaded:
    # - include/: C++ runtime headers from antlr3 3.5.3 (runtime/Cpp/include), with
    #   antlr3memory.hpp and antlr3cyclicdfa.hpp patched for C++20 / gcc >= 14
    # - share/java/: antlr-complete-3.5.3.jar from Maven Central
    #   (sha256 e781de9b3e2cc1297dfdaf656da946a1fd22f449bd9e0ce1e12d488976887f83)
    # - licenses/: tool/LICENSE.txt from antlr3 3.5.3
    exports_sources = "include/*", "share/java/*", "licenses/*"

    def layout(self):
        basic_layout(self)

    def requirements(self):
        if self.options.with_openjdk:
            self.requires("openjdk/21.0.2", run=True, headers=False, libs=False)

    def package_id(self):
        # Headers + jar + shell launcher: nothing depends on the host configuration.
        self.info.clear()

    @property
    def _jar_name(self) -> str:
        return f"antlr-complete-{self.version}.jar"

    def package(self):
        for folder in ("include", "share", "licenses"):
            copy(self, "*", self.source_path / folder, self.package_path / folder)

        launcher = self.package_path / "bin" / "antlr3"
        save(self, launcher, textwrap.dedent(f"""\
            #!/bin/sh
            # ANTLR {self.version} tool launcher (relocatable: the jar is located relative to this script)
            here="$(cd "$(dirname "$0")" && pwd)"
            jar="$here/../share/java/{self._jar_name}"
            if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]; then
                java="$JAVA_HOME/bin/java"
            else
                java=java
            fi
            exec "$java" -cp "$jar" org.antlr.Tool "$@"
            """))
        launcher.chmod(0o755)

    def package_info(self):
        # Matches ScyllaDB's cmake/FindANTLR3.cmake (ANTLR3::antlr3)
        self.cpp_info.set_property("cmake_file_name", "ANTLR3")
        self.cpp_info.set_property("cmake_target_name", "ANTLR3::antlr3")
        self.cpp_info.libdirs = []

        jar = str(self.package_path / "share" / "java" / self._jar_name)
        self.buildenv_info.define_path("ANTLR3_JAR", jar)
        self.runenv_info.define_path("ANTLR3_JAR", jar)
        self.conf_info.define_path("user.antlr3:jar", jar)
        self.conf_info.define_path("user.antlr3:executable", str(self.package_path / "bin" / "antlr3"))

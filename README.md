# scylladb-conan-index

Conan 2 recipes for ScyllaDB dependencies, laid out like
[conan-center-index](https://github.com/conan-io/conan-center-index).

## Using the index

Add a clone of this repository as a Conan remote:

```sh
git clone https://github.com/scylladb/scylladb-conan-index
conan remote add scylladb ./scylladb-conan-index --type local-recipes-index
```

Packages are then built from these recipes on demand (`--build=missing`).

## Layout

```
recipes/<name>/
├── config.yml        # version -> recipe folder
└── all/
    ├── conanfile.py
    └── test_package/
```

## Recipes

| Package | Version | Notes |
|---------|---------|-------|
| `antlr3` | 3.5.3 | ANTLR 3 tool (`antlr3` launcher + jar) and the header-only C++ runtime, with ScyllaDB's C++20 / gcc 14 header fixes. Fully vendored, since ANTLR 3 is no longer maintained upstream. Requires `openjdk` (Java ≥ 8 runs the tool) from ConanCenter, so the `conancenter` remote, or a mirror of `openjdk`, must be available. CMake: `find_package(ANTLR3)` → `ANTLR3::antlr3`. |
| `clock-bound` | 3.0.0-rc.0 | [AWS ClockBound](https://github.com/aws/clock-bound) at the commit ScyllaDB's `clock-bound` submodule points to. Client: `clockbound.h` and `libclockbound.a`, or `libclockbound.so` with `-o shared=True`. Service: the `clockbound` daemon, `cbctl`, systemd unit and sample configuration. **The package does not install the service**: the daemon must be installed and running on every host that uses the library, with the packaged `clockbound-install-service` script. See [recipes/clock-bound/README.md](recipes/clock-bound/README.md). Needs `cargo` (Rust ≥ 1.85) in `PATH` and access to crates.io when building. CMake: `find_package(clockbound)` → `clockbound::clockbound`. |
| `sccache` | 0.20.0 | [sccache](https://github.com/mozilla/sccache) compiler cache, packaged from upstream's prebuilt, statically linked (musl) release binaries, so no Rust toolchain is needed. Linux only, x86_64 and armv8. An application: use it as a `tool_requires`, which puts `sccache` in `PATH`. |
| `scylla-c-ares` | 1.34.8 | Built from [scylladb/c-ares](https://github.com/scylladb/c-ares) at the commit ScyllaDB's `c-ares` submodule points to (upstream 1.34.8 plus ScyllaDB's fixes). Static, PIC, no tools by default, as ScyllaDB links it into Seastar. `provides = "c-ares"`, so it replaces ConanCenter's `c-ares` in a graph. CMake: `find_package(c-ares)` → `c-ares::cares`. |

## Adding or testing a recipe

```sh
cd recipes/<name>/all
conan create . --version <version> --build=missing
```

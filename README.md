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

<<<<<<< HEAD
=======
## Recipes

| Package | Version | Notes |
|---------|---------|-------|
| `antlr3` | 3.5.3 | ANTLR 3 tool (`antlr3` launcher + jar) and the header-only C++ runtime, with ScyllaDB's C++20 / gcc 14 header fixes. Fully vendored, since ANTLR 3 is no longer maintained upstream. Needs Java at runtime (or `-o antlr3/*:with_openjdk=True`). CMake: `find_package(ANTLR3)` → `ANTLR3::antlr3`. |

>>>>>>> 22fcdcb (Add antlr3/3.5.3 recipe)
## Adding or testing a recipe

```sh
cd recipes/<name>/all
conan create . --version <version> --build=missing
```

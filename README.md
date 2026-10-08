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

## Adding or testing a recipe

```sh
cd recipes/<name>/all
conan create . --version <version> --build=missing
```

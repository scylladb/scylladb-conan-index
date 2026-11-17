# clock-bound

[AWS ClockBound](https://github.com/aws/clock-bound), at the commit ScyllaDB's `clock-bound`
submodule points to. ScyllaDB uses it as the clock source of LeaseGuard leader leases
(`strong_consistency_lease_clock_source: clockbound`).

The package has two parts:

| Part | Files | Used |
|------|-------|------|
| Client | `lib/libclockbound.a` (or `lib/libclockbound.so` with `-o shared=True`), `include/clockbound.h` | at build time, linked into ScyllaDB |
| Service | `bin/clockbound`, `bin/cbctl`, `bin/configure_phc`, `bin/clockbound-install-service`, `res/` | at run time, on every node |

## The service has to be installed

**Building or installing the Conan package does not install the service.** Conan only
puts the files in its cache; nothing is copied to the system and nothing is started.

The client library does no time synchronization of its own. It only reads the error bound
that the `clockbound` daemon publishes in shared memory (`/var/run/clockbound/shm1`). So on
every host that runs a binary using the library, the daemon must be installed and running:

- If the daemon has never run on the host, `clockbound_open()` fails. ScyllaDB refuses to
  start when the `clockbound` clock source is selected.
- If the daemon ran and stopped, the clock status degrades to free-running and then to
  unknown, and ScyllaDB falls back to quorum reads.

The daemon disciplines the system clock itself, so it **replaces** chrony, ntpd and
systemd-timesyncd: its systemd unit conflicts with them, and only one of them can run.

## Installing the service

The package ships a script, `bin/clockbound-install-service`, that installs the daemon
with the same layout as upstream's `clockbound` RPM. It needs systemd and root.

1. Get the package out of the Conan cache:

   ```sh
   conan install --requires=clock-bound/3.0.0-rc.0 --build=missing \
       --deployer=direct_deploy --deployer-folder=/tmp/clockbound
   ```

2. Install the service, and start it:

   ```sh
   sudo /tmp/clockbound/direct_deploy/clock-bound/bin/clockbound-install-service --enable
   ```

3. Check it:

   ```sh
   systemctl status clockbound
   cbctl status        # clock status and error bound
   cbctl waitsync      # block until the clock is synchronized
   ```

The script installs:

| Path | What |
|------|------|
| `/usr/bin/clockbound` | the daemon |
| `/usr/bin/cbctl` | control and status tool |
| `/usr/sbin/configure_phc` | sets up the ENA PTP hardware clock on EC2 |
| `/usr/lib/systemd/system/clockbound.service` | systemd unit |
| `/etc/logrotate.d/clockbound` | rotation of the daemon's logs |
| `/etc/clockbound.toml` | configuration (logging-only sample). An existing file is kept. |
| `/var/log/clockbound/` | log directory |

Options:

- `--enable`: disable and stop `chronyd`, `ntpd` and `systemd-timesyncd` if present, then
  enable and start `clockbound.service`.
- no option: install the files and leave the service stopped. Starting it later with
  `systemctl enable --now clockbound` stops the other time daemons but does not disable
  them, so disable them too, or they compete with clockbound at the next boot.
- `--uninstall`: stop and disable the service and remove the files. `/etc/clockbound.toml`
  and `/var/log/clockbound` are kept. No other time daemon is re-enabled; enable one
  yourself (`systemctl enable --now chronyd`).
- `DESTDIR=<root>`: install under another root without touching systemd, for building an
  image or a distribution package. Does not need root.

## Configuration

The unit runs `clockbound -c /etc/clockbound.toml`, and the daemon does not start without
that file. The installed sample only enables logging; the time sources are detected
automatically: on EC2 the Amazon Time Sync Service and, where available, the PTP hardware
clock, elsewhere the public `time.aws.com` servers. A fuller sample, with additional NTP
sources, is in the package at `res/config/example-config.toml`. Restart the service after
editing the configuration.

On EC2, `configure_phc` enables the ENA PTP hardware clock, which gives a tighter bound.
See upstream's [daemon documentation](https://github.com/aws/clock-bound/blob/main/docs/clockbound-daemon.md).

## Using the client library

```cmake
find_package(clockbound REQUIRED CONFIG)
target_link_libraries(my_target PRIVATE clockbound::clockbound)
```

Upstream's `clockbound.h` is a C header without `extern "C"` guards, and it has a struct
field named `errno`, which is a macro in C++. The packaged header is patched for both
(`all/patches`), so C++ includes it directly:

```cpp
#include <clockbound.h>
```

The `errno` field of `clockbound_err` cannot be named in code where `errno` is a macro;
`kind` and `detail` are unaffected.

## Static or shared

The `shared` option selects which client library the package holds:

```sh
conan create . --version 3.0.0-rc.0                           # libclockbound.a (default)
conan create . --version 3.0.0-rc.0 -o "&:shared=True"        # libclockbound.so
```

A consumer picks one with `-o "clock-bound/*:shared=True"`; the CMake target is the same
either way. The two are separate packages of the same recipe and live side by side in the
Conan cache.

- `libclockbound.a` is built with cargo's default LTO, codegen-unit and panic settings
  rather than upstream's release profile, as ScyllaDB does, so that it links next to other
  Rust static libraries (`librust_combined.a`) without duplicate symbols.
- `libclockbound.so` is built with upstream's release profile. It exports only the
  `clockbound_*` functions and has the SONAME `libclockbound.so`. A binary linked against
  it needs the library at run time: ship `libclockbound.so` with the binary, on its
  library path. `clockbound-install-service` installs the daemon only, not the library.

## Building

The recipe builds with `cargo`, which must be in `PATH` (Rust ≥ 1.85) and downloads crates
from crates.io. `-o daemon=False` builds only the client; that package cannot install the
service.

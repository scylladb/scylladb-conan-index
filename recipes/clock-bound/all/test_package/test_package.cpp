#include <cerrno>
#include <cstdio>
#include <cstring>

// Included after <cerrno> on purpose: the packaged clockbound.h is patched to cope with the
// errno macro and to carry its own `extern "C"` guards
#include <clockbound.h>

int main() {
    clockbound_err err = {};
    clockbound_ctx* ctx = clockbound_open(&err);
    if (ctx == nullptr) {
        // Expected wherever the clockbound daemon has never run: the library works, the
        // shared-memory segment is just not there
        std::printf("clockbound_open: no daemon (%.*s)\n",
                static_cast<int>(::strnlen(err.detail, CLOCKBOUND_ERROR_DETAIL_SIZE)), err.detail);
        return 0;
    }

    clockbound_now_result res = {};
    if (clockbound_now(ctx, &res, &err) == nullptr) {
        std::printf("clockbound_now: [%lld.%09ld, %lld.%09ld], status %d\n",
                static_cast<long long>(res.earliest.tv_sec), res.earliest.tv_nsec,
                static_cast<long long>(res.latest.tv_sec), res.latest.tv_nsec,
                static_cast<int>(res.clock_status));
    }
    clockbound_close(ctx, &err);
    return 0;
}

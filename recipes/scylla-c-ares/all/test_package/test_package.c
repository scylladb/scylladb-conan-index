#include <ares.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    ares_channel_t *channel = NULL;
    struct ares_options options;
    memset(&options, 0, sizeof(options));

    int status = ares_library_init(ARES_LIB_INIT_ALL);
    if (status != ARES_SUCCESS) {
        fprintf(stderr, "ares_library_init: %s\n", ares_strerror(status));
        return 1;
    }

    status = ares_init_options(&channel, &options, 0);
    if (status != ARES_SUCCESS) {
        fprintf(stderr, "ares_init_options: %s\n", ares_strerror(status));
        return 1;
    }

    printf("c-ares %s, thread-safe: %s\n", ares_version(NULL), ares_threadsafety() ? "yes" : "no");
    ares_destroy(channel);
    ares_library_cleanup();
    return 0;
}

#define _GNU_SOURCE
#include <sched.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <string.h>
#include <arpa/inet.h>
#include <assert.h>

void error(const char *msg) {
    perror(msg);
    exit(0);
}

void parse_host_port(char *s, int is_port_default, char *parsed_host, short *host_ok, int *parsed_port, short *port_ok) {
    if (s[0] == ':') {
        *parsed_port = atoi(s+1);
        *port_ok = 1; *host_ok = 0;
    }
    else if (!strchr(s, ':')) {
        if (is_port_default) {
            *parsed_port = atoi(s);
            *port_ok = 1; *host_ok = 0;
        }
        else {
            strcpy(parsed_host, s);
            *port_ok = 0; *host_ok = 1;
        }

    }
    else if (sscanf(s, "%[^:]:%d", parsed_host, parsed_port) == 2) {
        *port_ok = 1; *host_ok = 1;
    }
    else {
        *port_ok = 0; *host_ok = 0;
    }
}


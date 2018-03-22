#define _GNU_SOURCE
#include <sched.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <string.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <assert.h>

#define GOTTHARD_MAX_OP  7

#define TYPE_REQ   0
#define TYPE_RES   1

#define STATUS_OK                   0
#define STATUS_ABORT                1
#define STATUS_OPTIMISTIC_ABORT     2
#define STATUS_BADREQ               3

#define TXN_NOP       0
#define TXN_READ      1 // request: I would like to get the value of this obj
#define TXN_WRITE     2 // request: write this value to the object
#define TXN_VALUE     3 // fact: this is what (I think) the value is
#define TXN_UPDATED   4 // response: the object was just updated to this value
#define TXN_CPU_PCT   5 // request/response for CPU usage since last measurement

#define MAX_KEYS      65536 // 2^16
#define VALUE_SIZE    16
#define STORE_SIZE    MAX_KEYS * VALUE_SIZE

struct __attribute__((__packed__)) gotthard_hdr {
    uint8_t flags; // msg_type, from_switch, reset, store_commit
    uint32_t cl_id;
    uint32_t req_id;
    uint8_t frag_seq;
    uint8_t frag_cnt;
    uint8_t status;
    uint8_t op_cnt;
};

struct __attribute__((__packed__)) gotthard_op {
    uint8_t op_type;
    uint32_t key;
    char value[VALUE_SIZE];
};


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


double gettimestamp() {
    struct timeval tv;
    if (gettimeofday(&tv, NULL) != 0)
        error("gettimeofday");
    return tv.tv_sec + tv.tv_usec / 1000000.0;
}




#include "common.c"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <libgen.h>
#include <pthread.h>

#define BUFSIZE 2048

char *progname;
void usage(int rc) {
    fprintf(rc == 0 ? stdout : stderr,
            "Usage: %s [-c NUM_CLIENTS] [-d DURATION] [-w WRITE_RATIO] [-v VERBOSITY] [-s STATS_OUT_FILE] STORE_HOST STORE_PORT\n\
\n\
", progname);
    exit(rc);
}


struct sockaddr_in store_addr;
int num_clients = 1;
float duration = 1;
int verbosity = 0;
float write_ratio = 0.2;

float get_store_cpu_usage() {
    struct sockaddr_in sock_addr;
    struct sockaddr_in remote_addr;
    int remote_addr_len = sizeof(remote_addr);
    char buf[BUFSIZE];
    int size, sent_size;

	int sock_fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);

	sock_addr.sin_family = AF_INET;
	sock_addr.sin_addr.s_addr = 0;
    sock_addr.sin_port = 0;
	if (bind(sock_fd, (struct sockaddr *)&sock_addr, sizeof(sock_addr)) == -1)
        error("bind()");

    size = sizeof(struct gotthard_hdr) + sizeof(struct gotthard_op);
    struct gotthard_hdr *h = (struct gotthard_hdr *)buf;
    struct gotthard_op *op = (struct gotthard_op *)(buf + sizeof(struct gotthard_hdr));

    h->flags = 0;
    h->cl_id = htonl(1);
    h->req_id = htonl(1);
    h->frag_cnt = 1;
    h->frag_seq = 1;
    h->status = STATUS_OK;
    h->op_cnt = 1;
    op->op_type = TXN_CPU_PCT;

    sent_size = sendto(sock_fd, buf, size, 0, (struct sockaddr *)&store_addr, sizeof(store_addr));
    if (sent_size < 0)
        error("sendto");
    assert(sent_size == size && "All of the bytes should be sent");

    size = recvfrom(sock_fd, buf, BUFSIZE, 0,
            (struct sockaddr *)&remote_addr, &remote_addr_len);
    if (size < 0)
        error("recvfrom");

    char msg_type = h->flags >> 7 & 1;
    assert(msg_type == TYPE_RES);
    assert(h->status == STATUS_OK);
    assert(h->op_cnt == 1);
    assert(op->op_type == TXN_CPU_PCT);

    uint32_t pct_data = ntohl(*(uint32_t*)op->value);
    float pct = *(float*)&pct_data;

    return pct;
}

int make_req(char *buf, uint32_t cl_id, uint32_t req_id, uint32_t key, uint32_t cur_val) {
    int pkt_size = sizeof(struct gotthard_hdr);
    struct gotthard_hdr *req = (struct gotthard_hdr *)buf;
    struct gotthard_op *op1, *op2;
    uint32_t new_val = cur_val + 1;

    req->flags = 0;
    req->cl_id = htonl(cl_id);
    req->req_id = htonl(req_id);
    req->frag_cnt = 1;
    req->frag_seq = 1;
    req->status = STATUS_OK;

    if ((rand() % 1000) / 1000.0 < write_ratio) {
        req->op_cnt = 2;

        op1 = (struct gotthard_op *)(buf + sizeof(struct gotthard_hdr));
        op1->op_type = TXN_VALUE;
        op1->key = htonl(key);
        bzero(op1->value, VALUE_SIZE);
        *(uint32_t *)op1->value = htonl(*(uint32_t*)&cur_val);

        op2 = (struct gotthard_op *)(buf + sizeof(struct gotthard_hdr) + sizeof(struct gotthard_op));
        op2->op_type = TXN_WRITE;
        op2->key = htonl(key);
        bzero(op2->value, VALUE_SIZE);
        *(uint32_t *)op2->value = htonl(*(uint32_t*)&new_val);
    }
    else {
        req->op_cnt = 1;

        op1 = (struct gotthard_op *)(buf + sizeof(struct gotthard_hdr));
        op1->op_type = TXN_READ;
        op1->key = htonl(key);
        bzero(op1->value, VALUE_SIZE);
    }

    pkt_size += req->op_cnt*sizeof(struct gotthard_op);

    return pkt_size;
}

int parse_res(char *buf, size_t size, uint32_t cl_id, uint32_t req_id, uint32_t key, uint32_t *cur_val, char *from_switch) {
    int i;
    struct gotthard_hdr *res = (struct gotthard_hdr *)buf;
    struct gotthard_op *op;

    uint8_t msg_type = res->flags >> 7 & 1;
    *from_switch = res->flags >> 6 & 1;
    assert(msg_type == TYPE_RES);

    uint32_t res_cl_id = htonl(res->cl_id);
    uint32_t res_req_id = htonl(res->req_id);
    assert(res_cl_id == cl_id && "Expecting response to be to my cl_id");
    assert(res_req_id == req_id && "Expecting response to the req we sent");

    assert(res->op_cnt <= GOTTHARD_MAX_OP);

    for (i = 0; i < res->op_cnt; i++) {
        op = (struct gotthard_op *)(buf + sizeof(struct gotthard_hdr) + i*sizeof(struct gotthard_op));
        if (op->op_type == TXN_VALUE || op->op_type == TXN_UPDATED) {
            uint32_t op_key = ntohl(op->key);
            assert(op_key == key && "Got an unexpected key");
            *cur_val = ntohl(*(uint32_t *)op->value);
        }
    }

    return res->status;
}


struct client_stats {
    unsigned client_num;
    unsigned req_cnt;
    unsigned txn_cnt;
    unsigned abort_cnt;
    unsigned switch_abort_cnt;
    double elapsed;
    double avg_lat;
};


void *client_thread(void *arg) {
    struct client_stats *st = (struct client_stats *)arg;
    struct sockaddr_in sock_addr;
    struct sockaddr_in remote_addr;
    int remote_addr_len = sizeof(remote_addr);
    char buf[BUFSIZE];
    uint32_t cl_id = st->client_num;
    uint32_t req_id = 0;
    uint32_t val = 0;
    uint32_t key = 1;
    double start, txn_start = 0, txn_lat;
    int size, sent_size;
    char from_switch;

    st->txn_cnt = 0; st->abort_cnt = 0; st->switch_abort_cnt = 0;  st->avg_lat = 0;

	int sock_fd = socket(PF_INET, SOCK_DGRAM, IPPROTO_IP);

	sock_addr.sin_family = AF_INET;
	sock_addr.sin_addr.s_addr = 0;
    sock_addr.sin_port = 0;
	if (bind(sock_fd, (struct sockaddr *)&sock_addr, sizeof(sock_addr)) == -1)
        error("bind()");

    start = gettimestamp();
    txn_start = gettimestamp();
    do {
        req_id++;
        size = make_req(buf, cl_id, req_id, key, val);

        sent_size = sendto(sock_fd, buf, size, 0, (struct sockaddr *)&store_addr, sizeof(store_addr));
        if (sent_size < 0)
            error("sendto");
        assert(sent_size == size && "All of the bytes should be sent");

        size = recvfrom(sock_fd, buf, BUFSIZE, 0,
                (struct sockaddr *)&remote_addr, &remote_addr_len);
        if (size < 0)
            error("recvfrom");


        uint8_t status = parse_res(buf, size, cl_id, req_id, key, &val, &from_switch);

        if (status == STATUS_OK) {
            txn_start = gettimestamp();
            st->txn_cnt++;
        }
        else {
            st->abort_cnt++;
            if (from_switch)
                st->switch_abort_cnt++;
        }
	} while (txn_start < start + duration);

    st->req_cnt = req_id;
    st->elapsed = gettimestamp() - start;
    float txn_rate = st->txn_cnt / st->elapsed;

    if (verbosity > 0)
        printf("Client %2d incremented counter %d times to %d (%.2f TXN/s)\n", st->client_num, st->txn_cnt, val, txn_rate);

    close(sock_fd);
}

#define MAX_THREADS 256
pthread_t client_threads[MAX_THREADS];

int main(int argc, char *argv[]) {
    int opt, i;
    char *stats_filename = 0;

    progname = basename(argv[0]);
    while ((opt = getopt(argc, argv, "hc:d:s:w:v:")) != -1) {
        switch (opt) {
            case 'c':
                num_clients = atoi(optarg);
                break;
            case 'v':
                verbosity = atoi(optarg);
                break;
            case 'd':
                duration = atof(optarg);
                break;
            case 's':
                stats_filename = optarg;
                break;
            case 'w':
                write_ratio = atof(optarg);
                break;
            case 'h':
                usage(0);
            default: /* '?' */
                usage(-1);
        }
    }

	if (argc - optind != 2) {
		usage(-1);
	}

    char *store_host = argv[optind+0];
    char *store_port = argv[optind+1];

	store_addr.sin_addr.s_addr = inet_addr(store_host);
    store_addr.sin_port = htons(atoi(store_port));

    assert(num_clients <= MAX_THREADS);

    struct client_stats st[MAX_THREADS];

    if (verbosity > 0)
        printf("Running %d clients for %.2f seconds with %.2f write ratio.\n", num_clients, duration, write_ratio);

    get_store_cpu_usage();
    for (i = 0; i < num_clients; i++) {
        st[i].client_num = i+1;
        if (pthread_create(&client_threads[i], NULL, client_thread, (void *)&st[i]))
            error("pthread_create()");
    }
    for (i = 0; i < num_clients; i++) {
        if (pthread_join(client_threads[i], NULL))
            error("pthread_join()");
    }
    float store_cpu_pct = get_store_cpu_usage();

    if (stats_filename) {
        FILE *fh = fopen(stats_filename, "w");

        fprintf(fh, "{\"abort_counts\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "%d", st[i].abort_cnt);
        }

        fprintf(fh, "], \"switch_abort_counts\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "%d", st[i].switch_abort_cnt);
        }
        fprintf(fh, "], \"req_counts\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "%d", st[i].req_cnt);
        }

        fprintf(fh, "], \"txn_counts\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "%d", st[i].txn_cnt);
        }
        fprintf(fh, "], \"txn_lats\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "[]");
        }

        fprintf(fh, "], \"elapseds\": [");
        for (i = 0; i < num_clients; i++) {
            if (i != 0) fprintf(fh, ",");
            fprintf(fh, "%f", st[i].elapsed);
        }
        fprintf(fh, "], \"write_ratio\": %f, \"store_cpu_pct\": %f,\n", write_ratio, store_cpu_pct);
        fprintf(fh, "\"zipf\": 0, \"pop_size\": 1,\n");
        fprintf(fh, "\"duration\": %f, \"num_clients\": %d}\n", duration, num_clients);

        fclose(fh);
    }

}

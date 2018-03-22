
CC=gcc
CFLAGS+=-O3

all: store-server client

store-server: src/store-server.c src/common.c
	$(CC) -o $@ $< -lm $(CFLAGS)

client: src/client.c src/common.c
	$(CC) -o $@ $< -lpthread -lm $(CFLAGS)

tidy:
	rm -f *.o

clean: tidy
	rm -f store-server client

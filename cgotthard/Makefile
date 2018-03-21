
CC=gcc
CFLAGS+=-O3

all: store-server

store-server: src/store-server.c src/common.c
	$(CC) -o $@ $< -lm $(CFLAGS)

tidy:
	rm -f *.o

clean: tidy
	rm -f store-server

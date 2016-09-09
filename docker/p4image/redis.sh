#!/bin/sh
exec /sbin/setuser redis /usr/bin/redis-server /etc/redis/redis.conf

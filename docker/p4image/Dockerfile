FROM phusion/baseimage

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

ADD ./gitconfig /root/.gitconfig
ADD ./p4_startup.sh /etc/my_init.d/p4_startup.sh

WORKDIR /root
RUN apt-get update && apt-get install -y zsh git vim htop build-essential sudo wget net-tools netcat-openbsd iputils-ping
RUN git clone https://github.com/p4lang/tutorials
ADD ./env.sh /root/tutorials/p4v1_1/env.sh
RUN git clone https://github.com/p4lang/p4factory && cd p4factory && git submodule update --init --recursive
WORKDIR /root/p4factory
RUN grep -v -E "doxygen|ipython-notebook|python-sympy|wireshark" install_deps.sh > install_deps.sh.2 && chmod +x ./install_deps.sh.2 && ./install_deps.sh.2
RUN ./autogen.sh && ./configure
RUN pip install -r submodules/p4c-bm/requirements_v1_1.txt && cd submodules/bm && make -j2

RUN sed -i 's/daemonize \+yes/daemonize no/' /etc/redis/redis.conf
RUN mkdir /etc/service/redis
ADD ./redis.sh /etc/service/redis/run

WORKDIR /root

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

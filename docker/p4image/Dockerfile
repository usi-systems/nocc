FROM phusion/baseimage

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

ARG BUILD_CORES=2
ENV BUILD_CORES $BUILD_CORES

ADD ./gitconfig /root/.gitconfig
ADD ./p4_startup.sh /etc/my_init.d/p4_startup.sh
ADD ./env.sh /root/env.sh

WORKDIR /root
RUN apt-get update && apt-get install -y zsh git vim htop build-essential sudo wget net-tools netcat-openbsd iputils-ping ethtool mininet
RUN git clone https://github.com/p4lang/p4factory
RUN git clone https://github.com/p4lang/p4c
RUN git clone https://github.com/p4lang/behavioral-model

# Install Protobuf >=3.0.0
#RUN apt-get install -y autoconf automake libtool curl make g++ unzip
#RUN git clone --depth 1 -b v3.0.2 https://github.com/google/protobuf
#RUN cd protobuf && ./autogen.sh && ./configure && make -j$BUILD_CORES && make install && ldconfig

WORKDIR /root/p4c
RUN git checkout 5ac1559984c7b75b29fda8a9d1ae6ed5e3a30cd9
RUN apt-get install -y g++ git automake libtool libgc-dev bison flex libgmp-dev libboost-dev python2.7 python-scapy python-ipaddr tcpdump
RUN ./bootstrap.sh && cd build && make -j$BUILD_CORES

WORKDIR /root/behavioral-model
RUN ./install_deps.sh && ./autogen.sh && ./configure && make -j$BUILD_CORES

WORKDIR /root

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

FROM ubuntu:20.04

# Suppress interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt-get update && apt-get install -y \
    python3-pip python3-setuptools python3-wheel ninja-build build-essential flex bison \
    git cmake meson libsctp-dev libgnutls28-dev libgcrypt-dev libssl-dev libidn11-dev \
    libmongoc-dev libbson-dev libyaml-dev libmicrohttpd-dev libcurl4-gnutls-dev libnghttp2-dev \
    libtins-dev libtalloc-dev iproute2 ca-certificates netbase pkg-config libpthread-stubs0-dev \
    libpthread-workqueue-dev libunwind-dev \
    || { echo 'Dependency installation failed'; apt-get install -y --fix-broken; exit 1; }

# Clone and build Open5GS
RUN git clone https://github.com/open5gs/open5gs.git && \
    cd open5gs && \
    meson build --prefix=/usr && \
    ninja -C build && \
    ninja -C build install \
    || { echo 'Open5GS build failed'; exit 1; }

# Expose necessary ports
EXPOSE 3000 8080 2152

# Start Open5GS by default (can be overridden)
CMD ["/usr/bin/open5gs"]

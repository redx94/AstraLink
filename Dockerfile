FROM ubuntu:20.04

# Suppress interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt-get update && apt-get install -y \
    git build-essential cmake libsctp-dev lksctp-tools iproute2 tzdata \
    meson ninja-build pkg-config libtalloc-dev postgresql-client \
    libmongoc-1.0-0 libmongoc-dev libyaml-dev libmicrohttpd-dev \
    libidn11-dev libcurl4-openssl-dev flex bison \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone and build Open5GS
RUN git clone https://github.com/open5gs/open5gs.git && \
    cd open5gs && \
    meson build --prefix=/usr && \
    ninja -C build && \
    ninja -C build install

# Expose necessary ports
EXPOSE 3000 8080 2152

# Start Open5GS by default (can be overridden)
CMD ["/usr/bin/open5gs"]

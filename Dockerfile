FROM ubuntu:20.04

# Suppress asked prompts for tzdata and other packages
ENV DEBIAN_FRONTEND=noninteractive

# Install required dependencies
RUN apt-get update && apt-get install -y \
    git build-essential cmake libsctp-dev lksctp-tools iproute2 tzdata \
    meson ninja-build pkg-config libtalloc-dev postgresql-client \
    libmongoc-1.0-0 libmongoc-dev libyaml-dev libmicrohttpd-dev flex bison libidn11 libidn-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone and build Open5GS
RUN git clone https://github.com/open5GS/open5GS.git && \
    cd open5GS && \
    meson build --prefix=/usr && \
    ninja -C build && \
    ninja -C build install

# Expose necessary ports
EXPOSE 2152 3000 8080

# Start Open5GS
SMX ["/usr/bin/open5GS"]

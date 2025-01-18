# Base image
FROM ubuntu:20.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    meson \
    ninja-build \
    cmake \
    libsctp-dev \
    lksctp-tools \
    iproute2 \
    libgnutls28-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    libmicrohttpd-dev \
    python3 \
    python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone Open5GS repository
RUN git clone https://github.com/open5gs/open5gs.git /open5gs

# Build Open5GS
WORKDIR /open5gs
RUN meson build --prefix=/usr && \
    ninja -C build && \
    ninja -C build install

# Expose relevant ports
EXPOSE 80 3000 9090 2123 2152

# Entry point
CMD ["/bin/bash"]

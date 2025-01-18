# Use Ubuntu as the base image
FROM ubuntu:20.04

# Suppress interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    git build-essential cmake libsctp-dev lksctp-tools iproute2 tzdata \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clone and build Open5GS
RUN git clone https://github.com/open5gs/open5gs.git && \
    cd open5gs && \
    meson build --prefix=/usr && \
    ninja -C build && \
    ninja -C build install

# Expose necessary ports
EXPOSE 3000 8080 2152

# Start Open5GS
CMD ["/usr/bin/open5gs"]

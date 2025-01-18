FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    git build-essential cmake libsctp-dev lksctp-tools iproute2 \
    && apt-get clean

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

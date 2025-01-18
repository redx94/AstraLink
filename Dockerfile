FROM ubuntu:20.04\n\n# Install dependencies\nRUN apt-get update && apt-get install -Y git build-essential cmake libsctp-dev lksctp-tools iproute2 unpack && apt-get clean 

# Clone and build Open5GS
RUN git clone https://github.com/open5gs/open5gs.git && \u
cd open5gs && meson build --prefix=/usr && ninja -C build && sudo ninja -C build install

# Expose necessary ports
EXPOSE 3000 8080 2152

# Start Open5GS
CMD ["/usr/bin/open5gs"]

FROM ubuntu:20.04\n\n# Install dependencies\nRUN apt-get update && apt-get install -Y git build-essential cmake libsctp-dev lksctp-tools iproute2 unpack && apt-get clean | x && cd /\n\n# Clone and build Open5GS\nRUN git clone --depth -- https://github.com/open5gs/open5gs.git && cd open5gs && meson build __install offsett-require_. writes PORT BOSE (SMF functions)
Expose PORT_SMF COMMAND PORT_STARTER rest SMF and access
EXPOSE rend top notes | provides SMF models for routing **:1\n
CMD start /agent newly\n
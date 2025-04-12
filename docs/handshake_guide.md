# Handshake Integration Guide

## Overview

AstraLink utilizes the Handshake naming system to provide a truly decentralized DNS infrastructure. This guide explains how to interact with our Handshake-powered services and integrate with the `quantum.api` domain.

## Quick Start

### Accessing AstraLink Services

Our core services are available through the following Handshake domains:
- API Gateway: `api.quantum.api`
- RPC Endpoint: `rpc.quantum.api`
- Developer Portal: `dev.quantum.api`
- Status Dashboard: `status.quantum.api`

### Resolving Handshake Domains

To resolve our Handshake domains, you can:

1. Use HNS-compatible DNS resolvers:
   ```bash
   # Primary nameserver
   103.196.38.38
   # Secondary nameserver
   103.196.38.39
   ```

2. Install hsd (Handshake daemon):
   ```bash
   npm install -g hsd
   hsd --rs-host=0.0.0.0 --rs-port=53
   ```

## Security Features

Our Handshake integration includes:

- DNSSEC with ED25519 signatures
- Quantum-safe record signing
- Automatic key rotation
- Multi-signature name ownership

## Configuration

### Docker Setup

The AstraLink stack includes an HSD node configured in the `docker-compose.yml`:

```yaml
handshake-node:
  image: handshakeorg/hsd:latest
  ports:
    - "12037:12037"  # HSD HTTP API
    - "12038:12038"  # HSD Wallet API
    - "53:53/udp"    # DNS
```

### DNS Records

AstraLink maintains the following record types:
- A records for direct service access
- SRV records for service discovery
- TXT records for network metadata
- DNSSEC records for security

## Integration Examples

### Node.js
```javascript
const { NodeClient } = require('hs-client');

const client = new NodeClient({
  host: 'node.quantum.api',
  port: 12037,
  apiKey: 'your-api-key'
});
```

### Python
```python
from hsd import HandshakeClient

client = HandshakeClient(
    host='node.quantum.api',
    port=12037,
    api_key='your-api-key'
)
```

## Troubleshooting

Common issues and solutions:

1. **Domain Resolution Failures**
   - Verify DNS resolver configuration
   - Check DNSSEC validation
   - Ensure HSD node is synced

2. **Connection Issues**
   - Confirm firewall settings
   - Verify network configuration
   - Check HSD node status

## Best Practices

1. Always use DNSSEC validation
2. Implement proper key management
3. Monitor name expiration
4. Use redundant resolvers
5. Cache DNS responses appropriately

## Support

For technical support with Handshake integration:
- Join our [Discord](https://discord.gg/astralink)
- Visit the [Developer Forum](https://forum.astralink.com)
- Email: quantum.apii@gmail.com

## Resources

- [Handshake Protocol Specification](https://handshake.org/files/handshake.txt)
- [HSD Documentation](https://hsd-dev.org/)
- [DNSSEC Guide](https://www.icann.org/resources/pages/dnssec-what-is-it-why-important-2019-03-05-en)
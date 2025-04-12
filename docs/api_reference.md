# AstraLink API Reference

## Overview

AstraLink provides both REST and GraphQL APIs for integrating with the platform's core features. This document details all available endpoints, authentication methods, and usage examples.

## Authentication

### API Keys
All requests must include an API key in the Authorization header:
```
Authorization: Bearer <api_key>
```

### Rate Limiting
- Standard tier: 1000 requests/hour
- Enterprise tier: Unlimited requests

## REST API v1

### Base URL
```
https://api.astralink.com/v1
```

### eSIM Management

#### Create eSIM
```http
POST /esim
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "user_id": "string",
  "plan_type": "string",
  "bandwidth": "number",
  "security_level": "string"
}
```

Response:
```json
{
  "esim_id": "string",
  "profile_data": "string",
  "activation_token": "string",
  "quantum_signature": "string",
  "created_at": "timestamp"
}
```

#### Update eSIM
```http
PUT /esim/{esim_id}
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "bandwidth": "number",
  "security_level": "string"
}
```

Response:
```json
{
  "esim_id": "string",
  "update_status": "string",
  "quantum_signature": "string",
  "updated_at": "timestamp"
}
```

### Network Management

#### Get Network Status
```http
GET /network/status
Authorization: Bearer <api_key>
```

Response:
```json
{
  "node_count": "number",
  "active_connections": "number",
  "bandwidth_usage": "number",
  "quantum_security_status": "string",
  "error_rate": "number"
}
```

#### Allocate Bandwidth
```http
POST /network/bandwidth
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "connection_id": "string",
  "bandwidth": "number",
  "priority": "string"
}
```

Response:
```json
{
  "allocation_id": "string",
  "status": "string",
  "qos_metrics": {
    "latency": "number",
    "throughput": "number",
    "reliability": "number"
  }
}
```

### Smart Contracts

#### Deploy Contract
```http
POST /contracts/deploy
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "contract_type": "string",
  "parameters": "object",
  "initial_state": "object"
}
```

Response:
```json
{
  "contract_address": "string",
  "transaction_hash": "string",
  "gas_used": "number",
  "status": "string"
}
```

#### Execute Contract Method
```http
POST /contracts/{address}/execute
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "method": "string",
  "parameters": "array",
  "gas_limit": "number"
}
```

Response:
```json
{
  "transaction_hash": "string",
  "result": "object",
  "gas_used": "number",
  "status": "string"
}
```

## GraphQL API

### Endpoint
```
https://api.astralink.com/graphql
```

### Queries

#### Get Node Information
```graphql
query NodeInfo($nodeId: ID!) {
  node(id: $nodeId) {
    id
    status
    version
    uptime
    metrics {
      cpu_usage
      memory_usage
      bandwidth_usage
      connection_count
    }
    quantum_metrics {
      error_rate
      key_generation_rate
      entanglement_fidelity
    }
  }
}
```

#### Get Network Statistics
```graphql
query NetworkStats {
  network {
    total_nodes
    active_connections
    bandwidth_usage
    error_rate
    quantum_security_status
    performance_metrics {
      average_latency
      throughput
      packet_loss
    }
  }
}
```

### Mutations

#### Provision eSIM
```graphql
mutation ProvisionESIM($input: ESIMProvisionInput!) {
  provisionESIM(input: $input) {
    esim_id
    profile_data
    activation_token
    quantum_signature
    created_at
  }
}
```

#### Update Bandwidth Allocation
```graphql
mutation UpdateBandwidth($input: BandwidthUpdateInput!) {
  updateBandwidth(input: $input) {
    allocation_id
    status
    qos_metrics {
      latency
      throughput
      reliability
    }
  }
}
```

### Subscriptions

#### Monitor Network Events
```graphql
subscription NetworkEvents {
  networkEvents {
    event_type
    node_id
    timestamp
    details
  }
}
```

#### Track Connection Status
```graphql
subscription ConnectionStatus($connectionId: ID!) {
  connectionStatus(id: $connectionId) {
    status
    latency
    bandwidth_usage
    error_rate
    quantum_security_level
  }
}
```

## WebSocket API

### Connection
```
wss://api.astralink.com/ws
```

### Events

#### Connection Events
```json
{
  "type": "connection",
  "event": "status_change",
  "data": {
    "connection_id": "string",
    "status": "string",
    "timestamp": "number"
  }
}
```

#### Network Events
```json
{
  "type": "network",
  "event": "metric_update",
  "data": {
    "metric": "string",
    "value": "number",
    "timestamp": "number"
  }
}
```

## Error Handling

### Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error
- 503: Service Unavailable

### Error Response Format
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object",
    "correlation_id": "string"
  }
}
```

## Best Practices

### Rate Limiting
- Implement exponential backoff
- Cache responses when possible
- Use bulk operations
- Monitor rate limits

### Security
- Rotate API keys regularly
- Use HTTPS for all requests
- Validate responses
- Monitor for anomalies

### Performance
- Use compression
- Implement connection pooling
- Optimize query patterns
- Cache frequently used data

## Support

### Documentation
- API Reference (this document)
- Integration Guide
- Example Code
- SDKs

### Resources
- Developer Portal: https://developers.astralink.com
- Support Email: quantum.apii@gmail.com
- API Status: https://status.astralink.com
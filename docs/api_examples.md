# AstraLink API Examples Guide

## Overview

This guide provides practical code examples for integrating with AstraLink's APIs. Each example includes complete code samples, configuration details, and best practices.

## Quick Start Examples

### 1. eSIM Provisioning

#### Python Example
```python
import asyncio
from astralink import ESIMClient, QuantumSecurity

async def provision_esim():
    # Initialize clients
    esim_client = ESIMClient(
        api_key="your_api_key",
        environment="production"
    )
    
    quantum = QuantumSecurity()
    
    # Generate quantum signature
    signature = await quantum.generate_signature({
        "user_id": "user123",
        "timestamp": int(time.time())
    })
    
    # Create eSIM
    try:
        esim = await esim_client.create_esim({
            "user_id": "user123",
            "plan_type": "standard",
            "bandwidth": 1000,
            "quantum_signature": signature
        })
        print(f"eSIM created: {esim.id}")
        
    except ESIMError as e:
        print(f"Error: {e}")

# Run the example
asyncio.run(provision_esim())
```

#### TypeScript Example
```typescript
import { ESIMClient, QuantumSecurity } from '@astralink/sdk';

async function provisionESIM() {
  // Initialize clients
  const esimClient = new ESIMClient({
    apiKey: 'your_api_key',
    environment: 'production'
  });
  
  const quantum = new QuantumSecurity();
  
  // Generate quantum signature
  const signature = await quantum.generateSignature({
    userId: 'user123',
    timestamp: Date.now()
  });
  
  try {
    // Create eSIM
    const esim = await esimClient.createESIM({
      userId: 'user123',
      planType: 'standard',
      bandwidth: 1000,
      quantumSignature: signature
    });
    console.log(`eSIM created: ${esim.id}`);
    
  } catch (error) {
    console.error('Error:', error);
  }
}

provisionESIM();
```

### 2. Quantum Security Integration

#### Python Example
```python
from astralink import QuantumSecurityClient
import asyncio

async def secure_communication():
    # Initialize quantum security
    quantum = QuantumSecurityClient(
        node_id="node123",
        error_threshold=0.001
    )
    
    # Generate quantum keys
    try:
        keys = await quantum.generate_keys(
            bit_length=256,
            entropy_check=True
        )
        
        # Establish secure channel
        channel = await quantum.create_secure_channel(
            remote_node="node456",
            keys=keys,
            error_correction=True
        )
        
        # Send encrypted message
        message = "Hello Quantum World!"
        result = await channel.send_message(message)
        print(f"Message sent: {result.status}")
        
    except QuantumError as e:
        print(f"Quantum error: {e}")

asyncio.run(secure_communication())
```

#### TypeScript Example
```typescript
import { QuantumSecurity, SecureChannel } from '@astralink/quantum';

async function secureChannelExample() {
  const quantum = new QuantumSecurity({
    nodeId: 'node123',
    errorThreshold: 0.001
  });
  
  try {
    // Generate quantum keys
    const keys = await quantum.generateKeys({
      bitLength: 256,
      entropyCheck: true
    });
    
    // Create secure channel
    const channel = await quantum.createSecureChannel({
      remoteNode: 'node456',
      keys,
      errorCorrection: true
    });
    
    // Send message
    const result = await channel.sendMessage('Hello Quantum World!');
    console.log(`Message sent: ${result.status}`);
    
  } catch (error) {
    console.error('Quantum error:', error);
  }
}

secureChannelExample();
```

### 3. Network Management

#### Python Example
```python
from astralink import NetworkManager
import asyncio

async def manage_network():
    # Initialize network manager
    network = NetworkManager(
        api_key="your_api_key",
        region="us-east"
    )
    
    # Monitor network metrics
    async def monitor_metrics():
        async for metric in network.stream_metrics():
            print(f"Metric: {metric.name} = {metric.value}")
    
    # Allocate bandwidth
    async def allocate_resources():
        allocation = await network.allocate_bandwidth({
            "connection_id": "conn123",
            "bandwidth": 1000,
            "priority": "high"
        })
        print(f"Allocation: {allocation.id}")
    
    # Run operations
    await asyncio.gather(
        monitor_metrics(),
        allocate_resources()
    )

asyncio.run(manage_network())
```

#### TypeScript Example
```typescript
import { NetworkManager } from '@astralink/network';

async function networkExample() {
  const network = new NetworkManager({
    apiKey: 'your_api_key',
    region: 'us-east'
  });
  
  // Monitor metrics
  network.streamMetrics().subscribe(metric => {
    console.log(`Metric: ${metric.name} = ${metric.value}`);
  });
  
  // Allocate resources
  try {
    const allocation = await network.allocateBandwidth({
      connectionId: 'conn123',
      bandwidth: 1000,
      priority: 'high'
    });
    console.log(`Allocation: ${allocation.id}`);
    
  } catch (error) {
    console.error('Network error:', error);
  }
}

networkExample();
```

### 4. Smart Contract Integration

#### Solidity Example
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@astralink/contracts/QuantumESIM.sol";
import "@astralink/contracts/security/QuantumVerifier.sol";

contract ESIMManager {
    QuantumESIM private esim;
    QuantumVerifier private verifier;
    
    constructor(address esimAddress, address verifierAddress) {
        esim = QuantumESIM(esimAddress);
        verifier = QuantumVerifier(verifierAddress);
    }
    
    function provisionESIM(
        address user,
        bytes memory quantumSignature
    ) public returns (uint256) {
        // Verify quantum signature
        require(
            verifier.verifySignature(quantumSignature),
            "Invalid quantum signature"
        );
        
        // Mint eSIM
        return esim.mintESIM(user, quantumSignature);
    }
}
```

#### Web3.js Example
```typescript
import Web3 from 'web3';
import { QuantumSecurity } from '@astralink/quantum';

async function contractExample() {
  const web3 = new Web3('https://rpc.astralink.com');
  const quantum = new QuantumSecurity();
  
  // Contract setup
  const contract = new web3.eth.Contract(
    ESIMManagerABI,
    'contract_address'
  );
  
  try {
    // Generate quantum signature
    const signature = await quantum.generateSignature({
      user: 'user_address',
      timestamp: Date.now()
    });
    
    // Call contract
    const result = await contract.methods
      .provisionESIM('user_address', signature)
      .send({ from: 'sender_address' });
      
    console.log(`eSIM provisioned: ${result.events.ESIMProvisioned.returnValues.tokenId}`);
    
  } catch (error) {
    console.error('Contract error:', error);
  }
}

contractExample();
```

### 5. AI Integration

#### Python Example
```python
from astralink import AIOptimizer, NetworkMetrics
import asyncio

async def optimize_network():
    # Initialize AI optimizer
    ai = AIOptimizer(
        model="quantum_enhanced",
        learning_rate=0.01
    )
    
    # Collect network metrics
    metrics = NetworkMetrics()
    
    async def collect_data():
        async for data in metrics.stream():
            # Process network data
            prediction = await ai.predict_optimization(data)
            
            # Apply optimization
            if prediction.confidence > 0.95:
                await ai.apply_optimization(prediction)
    
    # Run optimization loop
    try:
        await collect_data()
    except AIError as e:
        print(f"AI error: {e}")

asyncio.run(optimize_network())
```

#### TypeScript Example
```typescript
import { AIOptimizer, NetworkMetrics } from '@astralink/ai';

async function aiExample() {
  const ai = new AIOptimizer({
    model: 'quantum_enhanced',
    learningRate: 0.01
  });
  
  const metrics = new NetworkMetrics();
  
  // Stream network data
  metrics.stream().subscribe(async data => {
    try {
      // Generate prediction
      const prediction = await ai.predictOptimization(data);
      
      // Apply optimization
      if (prediction.confidence > 0.95) {
        await ai.applyOptimization(prediction);
      }
      
    } catch (error) {
      console.error('AI error:', error);
    }
  });
}

aiExample();
```

## Best Practices

### 1. Error Handling
```typescript
try {
  // API calls
} catch (error) {
  if (error instanceof QuantumError) {
    // Handle quantum errors
  } else if (error instanceof NetworkError) {
    // Handle network errors
  } else {
    // Handle other errors
  }
}
```

### 2. Rate Limiting
```python
from astralink import RateLimiter

limiter = RateLimiter(
    max_requests=1000,
    time_window="1h"
)

async with limiter:
    # API calls
```

### 3. Logging
```python
import logging
from astralink import setup_logging

logger = setup_logging(
    level="INFO",
    quantum_logs=True
)

logger.info("Operation started")
try:
    # API calls
except Exception as e:
    logger.error(f"Error: {e}")
```

## Configuration Examples

### 1. Environment Setup
```yaml
astralink:
  environment: production
  api_key: your_api_key
  region: us-east
  
  quantum:
    error_threshold: 0.001
    key_rotation: 12h
    
  network:
    retry_attempts: 3
    timeout: 30s
    
  monitoring:
    metrics_interval: 1s
    log_level: info
```

### 2. Client Configuration
```typescript
const config = {
  apiKey: 'your_api_key',
  environment: 'production',
  quantum: {
    errorThreshold: 0.001,
    keyRotation: '12h'
  },
  network: {
    retryAttempts: 3,
    timeout: 30000
  }
};

const client = new AstraLinkClient(config);
```

## Testing Examples

### 1. Unit Testing
```python
import pytest
from astralink.testing import MockQuantumSystem

@pytest.fixture
def quantum_mock():
    return MockQuantumSystem(
        error_rate=0.001,
        key_generation="simulated"
    )

async def test_quantum_security(quantum_mock):
    keys = await quantum_mock.generate_keys()
    assert len(keys) == 256
    assert quantum_mock.verify_keys(keys)
```

### 2. Integration Testing
```typescript
import { TestEnvironment } from '@astralink/testing';

describe('Network Integration', () => {
  let testEnv: TestEnvironment;
  
  beforeAll(async () => {
    testEnv = await TestEnvironment.create();
  });
  
  it('should allocate bandwidth', async () => {
    const result = await testEnv.network.allocateBandwidth({
      connectionId: 'test',
      bandwidth: 1000
    });
    
    expect(result.status).toBe('success');
  });
});
```

## Support Resources

### Documentation
- API Reference
- Integration Guide
- Security Guide
- Best Practices

### Community
- Discord: [AstraLink Community](https://discord.gg/astralink)
- Forum: [Developer Forum](https://forum.astralink.com)
- GitHub: [Example Repository](https://github.com/astralink/examples)
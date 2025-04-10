#!/usr/bin/env python3

"""
AstraLink Node Manager CLI
========================

Command-line interface for managing AstraLink nodes through quantum.api

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

import argparse
import asyncio
import json
import sys
import yaml
import aiohttp
from datetime import datetime
from typing import Dict, Optional
from quantum.quantum_error_correction import QuantumErrorCorrection
from logging_config import get_logger

logger = get_logger(__name__)

class NodeManagerCLI:
    def __init__(self, api_url: str = "https://api.quantum.api"):
        self.api_url = api_url
        self.quantum_correction = QuantumErrorCorrection()
        self._load_config()

    def _load_config(self):
        """Load CLI configuration"""
        try:
            with open('config/node_manager.yaml', 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {
                'auth_token': None,
                'default_node': None
            }

    async def _get_auth_token(self) -> str:
        """Get quantum-safe authentication token"""
        if not self.config.get('auth_token'):
            # Generate new token
            token = await self.quantum_correction.generate_key()
            self.config['auth_token'] = token
            
            # Save to config
            with open('config/node_manager.yaml', 'w') as f:
                yaml.dump(self.config, f)
                
        return self.config['auth_token']

    async def list_nodes(self) -> None:
        """List all registered nodes"""
        async with aiohttp.ClientSession() as session:
            token = await self._get_auth_token()
            async with session.get(
                f"{self.api_url}/nodes",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    nodes = await response.json()
                    print("\nRegistered Nodes:")
                    print("================")
                    for node in nodes:
                        print(f"\nNode ID: {node['node_id']}")
                        print(f"Domain: {node['domain']}")
                        print(f"Environment: {node['environment']}")
                        print("-" * 40)
                else:
                    print(f"Error: {response.status} - {await response.text()}")

    async def get_node_status(self, node_id: str) -> None:
        """Get status of specific node"""
        async with aiohttp.ClientSession() as session:
            token = await self._get_auth_token()
            async with session.get(
                f"{self.api_url}/nodes/{node_id}/status",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    print(f"\nStatus for Node: {node_id}")
                    print("====================" + "=" * len(node_id))
                    print(f"Status: {status['status']}")
                    print(f"Last Seen: {status['last_seen']}")
                    print("\nMetrics:")
                    print(json.dumps(status['metrics'], indent=2))
                    print("\nQuantum State:")
                    print(json.dumps(status['quantum_state'], indent=2))
                    print("\nNetwork Status:")
                    print(json.dumps(status['network'], indent=2))
                else:
                    print(f"Error: {response.status} - {await response.text()}")

    async def update_config(self, node_id: str, config_file: str) -> None:
        """Update node configuration"""
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            async with aiohttp.ClientSession() as session:
                token = await self._get_auth_token()
                async with session.post(
                    f"{self.api_url}/nodes/{node_id}/config",
                    headers={"Authorization": f"Bearer {token}"},
                    json=config
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"\nConfiguration updated for Node: {node_id}")
                        print(f"Timestamp: {result['timestamp']}")
                        print(f"Config Hash: {result['config_hash']}")
                    else:
                        print(f"Error: {response.status} - {await response.text()}")
        except Exception as e:
            print(f"Error: {str(e)}")

    async def restart_node(self, node_id: str) -> None:
        """Restart node services"""
        async with aiohttp.ClientSession() as session:
            token = await self._get_auth_token()
            async with session.post(
                f"{self.api_url}/nodes/{node_id}/restart",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"\nRestarting Node: {node_id}")
                    print(f"Status: {result['status']}")
                    print(f"Timestamp: {result['timestamp']}")
                else:
                    print(f"Error: {response.status} - {await response.text()}")

    async def get_logs(self, node_id: str, service: Optional[str] = None, lines: int = 100) -> None:
        """Get node logs"""
        async with aiohttp.ClientSession() as session:
            token = await self._get_auth_token()
            params = {"service": service, "lines": lines} if service else {"lines": lines}
            async with session.get(
                f"{self.api_url}/nodes/{node_id}/logs",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    logs = await response.json()
                    print(f"\nLogs for Node: {node_id}")
                    if service:
                        print(f"Service: {service}")
                    print("=" * 40)
                    for log in logs['logs']:
                        print(log)
                else:
                    print(f"Error: {response.status} - {await response.text()}")

    async def get_metrics(self, node_id: str, metric_type: Optional[str] = None) -> None:
        """Get node metrics"""
        async with aiohttp.ClientSession() as session:
            token = await self._get_auth_token()
            params = {"type": metric_type} if metric_type else {}
            async with session.get(
                f"{self.api_url}/nodes/{node_id}/metrics",
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                if response.status == 200:
                    metrics = await response.json()
                    print(f"\nMetrics for Node: {node_id}")
                    if metric_type:
                        print(f"Type: {metric_type}")
                    print("=" * 40)
                    print(json.dumps(metrics['metrics'], indent=2))
                else:
                    print(f"Error: {response.status} - {await response.text()}")

async def main():
    parser = argparse.ArgumentParser(description='AstraLink Node Manager CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List nodes
    subparsers.add_parser('list', help='List all registered nodes')

    # Node status
    status_parser = subparsers.add_parser('status', help='Get node status')
    status_parser.add_argument('node_id', help='Node ID')

    # Update config
    config_parser = subparsers.add_parser('config', help='Update node configuration')
    config_parser.add_argument('node_id', help='Node ID')
    config_parser.add_argument('config_file', help='Configuration file path')

    # Restart node
    restart_parser = subparsers.add_parser('restart', help='Restart node services')
    restart_parser.add_argument('node_id', help='Node ID')

    # Get logs
    logs_parser = subparsers.add_parser('logs', help='Get node logs')
    logs_parser.add_argument('node_id', help='Node ID')
    logs_parser.add_argument('--service', help='Service name')
    logs_parser.add_argument('--lines', type=int, default=100, help='Number of lines')

    # Get metrics
    metrics_parser = subparsers.add_parser('metrics', help='Get node metrics')
    metrics_parser.add_argument('node_id', help='Node ID')
    metrics_parser.add_argument('--type', help='Metric type')

    # Run audit
    audit_parser = subparsers.add_parser('audit', help='Run security audit')
    audit_parser.add_argument('node_id', help='Node ID')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    cli = NodeManagerCLI()
    
    try:
        if args.command == 'list':
            await cli.list_nodes()
        elif args.command == 'status':
            await cli.get_node_status(args.node_id)
        elif args.command == 'config':
            await cli.update_config(args.node_id, args.config_file)
        elif args.command == 'restart':
            await cli.restart_node(args.node_id)
        elif args.command == 'logs':
            await cli.get_logs(args.node_id, args.service, args.lines)
        elif args.command == 'metrics':
            await cli.get_metrics(args.node_id, args.type)
        elif args.command == 'audit':
            await cli.run_audit(args.node_id)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
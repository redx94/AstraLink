#!/usr/bin/env python3

"""
AstraLink Remote Deployment through quantum.api
============================================

Handles secure remote node deployment using quantum.api domain and
quantum-safe authentication.

Developer: Reece Dixon
Copyright © 2025 AstraLink. All rights reserved.
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import aiohttp
import paramiko
from cryptography.fernet import Fernet
from quantum.quantum_error_correction import QuantumErrorCorrection
from network.handshake_integration import HandshakeIntegration
from logging_config import get_logger

logger = get_logger(__name__)

class RemoteDeployer:
    def __init__(self, domain: str = "quantum.api"):
        self.domain = domain
        self.handshake = HandshakeIntegration(domain)
        self.quantum_correction = QuantumErrorCorrection()
        self.nodes = {}
        self._load_config()

    def _load_config(self):
        """Load deployment configuration"""
        try:
            with open('config/templates/mainnet.yaml', 'r') as f:
                self.mainnet_config = yaml.safe_load(f)
            with open('config/templates/testnet.yaml', 'r') as f:
                self.testnet_config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configurations: {e}")
            raise

    async def register_node(self, node_ip: str, environment: str) -> Dict:
        """Register new node with quantum.api"""
        try:
            # Generate quantum-safe credentials
            node_id = await self._generate_node_id()
            auth_token = await self._generate_auth_token()

            # Create DNS records
            node_domain = f"{node_id}.{environment}.{self.domain}"
            await self.handshake.update_dns_records([
                {
                    "type": "A",
                    "name": node_domain,
                    "value": node_ip
                },
                {
                    "type": "SRV",
                    "name": f"_node._tcp.{node_domain}",
                    "target": node_domain,
                    "port": 22
                }
            ])

            # Register with network
            node_info = {
                "node_id": node_id,
                "ip": node_ip,
                "domain": node_domain,
                "environment": environment,
                "auth_token": auth_token
            }
            self.nodes[node_id] = node_info

            logger.info(
                f"Node registered successfully",
                extra={
                    'node_id': node_id,
                    'domain': node_domain
                }
            )

            return node_info

        except Exception as e:
            logger.error(f"Node registration failed: {e}")
            raise

    async def deploy_node(self, node_info: Dict) -> bool:
        """Deploy AstraLink to remote node"""
        try:
            # Establish SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                node_info['ip'],
                username='root',
                key_filename=os.path.expanduser('~/.ssh/id_rsa')
            )

            # Create temporary working directory
            stdin, stdout, stderr = ssh.exec_command('mktemp -d')
            temp_dir = stdout.read().decode().strip()

            # Copy deployment files
            sftp = ssh.open_sftp()
            remote_files = [
                ('deploy/install.sh', f'{temp_dir}/install.sh'),
                ('tools/quantum_readiness.py', f'{temp_dir}/tools/quantum_readiness.py'),
                ('tools/requirements.txt', f'{temp_dir}/tools/requirements.txt')
            ]

            for local_path, remote_path in remote_files:
                remote_dir = os.path.dirname(remote_path)
                stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}')
                sftp.put(local_path, remote_path)

            # Generate node-specific configuration
            config = self.mainnet_config if node_info['environment'] == 'mainnet' else self.testnet_config
            config['network']['node_id'] = node_info['node_id']
            config['network']['domain'] = node_info['domain']
            config['security']['auth_token'] = node_info['auth_token']

            config_path = f'{temp_dir}/config.yaml'
            with sftp.open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Make install script executable
            ssh.exec_command(f'chmod +x {temp_dir}/install.sh')

            # Run installation
            cmd = f'cd {temp_dir} && ./install.sh --remote --config config.yaml'
            stdin, stdout, stderr = ssh.exec_command(cmd)

            # Monitor installation
            while not stdout.channel.exit_status_ready():
                output = stdout.readline()
                if output:
                    logger.info(
                        f"Remote installation output",
                        extra={
                            'node_id': node_info['node_id'],
                            'output': output.strip()
                        }
                    )

            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                error = stderr.read().decode()
                logger.error(
                    f"Remote installation failed",
                    extra={
                        'node_id': node_info['node_id'],
                        'error': error
                    }
                )
                return False

            # Cleanup
            ssh.exec_command(f'rm -rf {temp_dir}')
            ssh.close()

            logger.info(
                f"Node deployed successfully",
                extra={'node_id': node_info['node_id']}
            )

            return True

        except Exception as e:
            logger.error(f"Node deployment failed: {e}")
            return False

    async def _generate_node_id(self) -> str:
        """Generate quantum-safe node identifier"""
        random_bytes = await self.quantum_correction.generate_random_bytes(32)
        return random_bytes.hex()[:16]

    async def _generate_auth_token(self) -> str:
        """Generate quantum-safe authentication token"""
        return await self.quantum_correction.generate_key()

async def main():
    parser = argparse.ArgumentParser(description='AstraLink Remote Deployment')
    parser.add_argument('--ip', required=True, help='Node IP address')
    parser.add_argument('--env', choices=['testnet', 'mainnet'], required=True,
                      help='Deployment environment')
    args = parser.parse_args()

    deployer = RemoteDeployer()

    try:
        # Register node
        node_info = await deployer.register_node(args.ip, args.env)
        print(f"\n✅ Node registered as {node_info['domain']}")

        # Deploy node
        if await deployer.deploy_node(node_info):
            print(f"\n✅ Node deployed successfully!")
            print(f"Domain: {node_info['domain']}")
            print(f"Environment: {args.env}")
            sys.exit(0)
        else:
            print(f"\n❌ Node deployment failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
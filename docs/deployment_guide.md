# AstraLink Node Deployment Guide
===============================

This guide provides step-by-step instructions for deploying AstraLink nodes, covering both local and remote deployment scenarios.

## Prerequisites
- A Linux-based system (Ubuntu, Debian, CentOS)
- Root privileges
- Python 3.7+
- Basic knowledge of command-line operations
- (For remote deployment) SSH access to the target node

## 1. Local Deployment
---------------------

### 1.1. Clone the AstraLink Repository
```bash
git clone https://github.com/redx94/AstraLink.git
cd AstraLink
```

### 1.2. Run the Installation Script
```bash
sudo bash deploy/install.sh
```

### 1.3. Select Deployment Environment
The script will prompt you to select a deployment environment:
1. Development (local testing, mock hardware)
2. Testnet (real hardware, test network)
3. Mainnet (production deployment)

Choose the appropriate option based on your needs.

### 1.4. Configure Environment Variables (if Mainnet)
If you selected Mainnet, the script will prompt you for:
- Node IPv4 address
- Node IPv6 address

Enter the correct values for your node.

### 1.5. Review Installation Summary
The script will display a summary of the installation, including:
- Environment
- Configuration file location
- Service status
- AppArmor profiles

### 1.6. Access Grafana Dashboards
Once the installation is complete, access the Grafana dashboards by opening your web browser and navigating to:
```
http://<node_ip>:3000
```
(Replace `<node_ip>` with the IP address of your node)

## 2. Remote Deployment
----------------------

### 2.1. Prepare the Remote Node
Ensure the remote node meets the prerequisites and has SSH access enabled.

### 2.2. Copy the AstraLink Repository
Copy the AstraLink repository to the remote node using `scp` or a similar tool:
```bash
scp -r AstraLink root@<node_ip>:/opt/
```
(Replace `<node_ip>` with the IP address of the remote node)

### 2.3. Create a Configuration File
Create a configuration file for the remote node based on the templates in `config/templates/`. For example, to create a mainnet configuration:
```bash
cp config/templates/mainnet.yaml remote_config.yaml
```
Edit the `remote_config.yaml` file and replace the placeholder values (e.g., `${NODE_IP}`, `${NODE_IPV6}`) with the correct values for the remote node.

### 2.4. Run the Remote Deployment Script
Run the `deploy/install.sh` script on the remote node using SSH:
```bash
ssh root@<node_ip> "bash /opt/AstraLink/deploy/install.sh --remote --config /opt/AstraLink/remote_config.yaml"
```
(Replace `<node_ip>` with the IP address of the remote node)

### 2.5. Monitor the Installation
The installation script will output progress information to the console. Monitor the output for any errors.

### 2.6. Access Grafana Dashboards
Once the installation is complete, access the Grafana dashboards by opening your web browser and navigating to:
```
http://<node_ip>:3000
```
(Replace `<node_ip>` with the IP address of the remote node)

## 3. Post-Deployment Configuration
--------------------------------

### 3.1. Configure Grafana Data Source
Configure Grafana to use Prometheus as a data source. This typically involves:
- Installing Prometheus
- Configuring Prometheus to scrape metrics from the AstraLink nodes
- Adding Prometheus as a data source in Grafana

### 3.2. Customize AppArmor Profiles
Customize the AppArmor profiles in `/etc/apparmor.d/local/astralink` to further restrict the capabilities of the AstraLink services.

### 3.3. Monitor System Logs
Monitor the system logs for any errors or warnings related to the AstraLink services. Use the following command to view the logs:
```bash
journalctl -u astralink-node
```

## 4. Troubleshooting
--------------------

### 4.1. Installation Errors
If you encounter any errors during the installation process, check the following:
- Ensure you have root privileges
- Verify that all dependencies are installed
- Check the installation script output for error messages

### 4.2. Service Startup Failures
If any of the AstraLink services fail to start, check the system logs for error messages. Use the following command to view the logs for a specific service:
```bash
journalctl -u <service_name>
```
(Replace `<service_name>` with the name of the service, e.g., `astralink-quantum`)

### 4.3. Network Connectivity Issues
If you experience any network connectivity issues, check the following:
- Ensure that the node has a valid IP address and can connect to the internet
- Verify that the firewall is configured correctly
- Check the DNS settings

### 4.4. Quantum Operations Failures
If you encounter any issues with quantum operations, check the following:
- Ensure that the system meets the quantum requirements
- Verify that the TPM is functioning correctly
- Check the quantum service logs for error messages

## 5. Security Best Practices
--------------------------

### 5.1. Keep the System Up-to-Date
Regularly update the system with the latest security patches.

### 5.2. Use Strong Passwords
Use strong, unique passwords for all user accounts.

### 5.3. Enable Two-Factor Authentication
Enable two-factor authentication for all user accounts.

### 5.4. Monitor System Logs
Regularly monitor the system logs for any suspicious activity.

### 5.5. Restrict Network Access
Restrict network access to the AstraLink services to only the necessary ports and IP addresses.

### 5.6. Securely Store Keys and Certificates
Securely store all keys and certificates used by the AstraLink services.

## 6. Contact Information
-----------------------

For any questions or issues, please contact the AstraLink support team at support@quantum.api.
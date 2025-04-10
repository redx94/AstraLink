#!/bin/bash

# AstraLink Network Node Installation Script
# ========================================
# This script installs and configures an AstraLink network node with all required
# services and dependencies for bare metal deployment.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Default settings
DEPLOY_ENV="development"
REMOTE_MODE=false
CONFIG_FILE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remote)
            REMOTE_MODE=true
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}AstraLink Network Node Installation${NC}"
echo "============================================"

# Check root privileges and AppArmor status
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Check AppArmor status
check_apparmor() {
    echo -e "\n${BLUE}Checking AppArmor status...${NC}"
    if ! command -v apparmor_status >/dev/null 2>&1; then
        echo -e "${RED}AppArmor is not installed${NC}"
        return 1
    fi
    
    if ! apparmor_status | grep -q "apparmor module is loaded"; then
        echo -e "${RED}AppArmor module is not loaded${NC}"
        return 1
    fi
    
    echo -e "${GREEN}AppArmor is active${NC}"
    return 0
}

# Create astralink user and group
create_user() {
    echo -e "\n${BLUE}Creating AstraLink user and group...${NC}"
    if ! getent group astralink >/dev/null; then
        groupadd astralink
    fi
    if ! getent passwd astralink >/dev/null; then
        useradd -r -g astralink -d /opt/astralink -s /bin/false astralink
    fi
}

# Install system dependencies
install_dependencies() {
    echo -e "\n${BLUE}Installing system dependencies...${NC}"
    apt-get update
    apt-get install -y \
        python3 python3-pip \
        libusb-1.0-0-dev \
        uhd-host \
        libfftw3-dev \
        libtpm2-0 \
        libcrypto++-dev \
        libssl-dev \
        net-tools \
        bind9 \
        tpm2-tools \
        python3-numpy \
        python3-psutil \
        python3-cpuinfo
}

# Create directory structure
create_directories() {
    echo -e "\n${BLUE}Creating directory structure...${NC}"
    mkdir -p /opt/astralink
    mkdir -p /etc/astralink
    mkdir -p /var/lib/astralink-{quantum,blockchain,cellular,handshake}
    mkdir -p /var/log/astralink
    
    # Set permissions
    chown -R astralink:astralink /opt/astralink
    chown -R astralink:astralink /etc/astralink
    chown -R astralink:astralink /var/lib/astralink-*
    chown -R astralink:astralink /var/log/astralink
    
    chmod 700 /var/lib/astralink-*
}

# Install Python dependencies
install_python_deps() {
    echo -e "\n${BLUE}Installing Python dependencies...${NC}"
    pip3 install -r requirements.txt
}

# Install Grafana and provision dashboards
install_monitoring() {
echo -e "\n${BLUE}Installing Grafana and provisioning dashboards...${NC}"

# Install Grafana
apt-get update
apt-get install -y grafana

# Enable and start Grafana
systemctl enable grafana-server
systemctl start grafana-server

# Create Grafana data source (replace with actual Prometheus data source)
# grafana-cli datasources add --name 'Prometheus' --type prometheus --url http://localhost:9090

# Copy dashboard templates
mkdir -p /var/lib/grafana/dashboards
cp deploy/grafana/*.json /var/lib/grafana/dashboards/

# Configure Grafana to load dashboards
cat > /etc/grafana/provisioning/dashboards/all.yml << EOF
apiVersion: 1

providers:
- name: 'default'
orgId: 1
folder: ''
type: file
disableSecurity: true
updateIntervalSeconds: 10
options:
  path: /var/lib/grafana/dashboards
EOF

# Restart Grafana to load dashboards
systemctl restart grafana-server

echo -e "${GREEN}Grafana installed and dashboards provisioned${NC}"
}

# Configure systemd services and AppArmor profiles
install_services() {
echo -e "\n${BLUE}Installing systemd services and AppArmor profiles...${NC}"
    
    # Install systemd services
    cp deploy/systemd/astralink-*.service /etc/systemd/system/
    
    # Install AppArmor profiles
    mkdir -p /etc/apparmor.d
    cp deploy/apparmor/astralink-* /etc/apparmor.d/
    
    # Parse and load AppArmor profiles
    for profile in /etc/apparmor.d/astralink-*; do
        echo -e "${BLUE}Loading AppArmor profile: ${profile}${NC}"
        apparmor_parser -r "$profile"
    done
    
    # Configure environment files
    cat > /etc/astralink/node.env << EOF
NODE_ENV=production
LOG_LEVEL=info
EOF

    cat > /etc/astralink/quantum.env << EOF
QUANTUM_ERROR_THRESHOLD=0.001
QUANTUM_MEMORY_LIMIT=8G
EOF

    cat > /etc/astralink/cellular.env << EOF
CELL_STACK_TYPE=3GPP
SDR_ENABLED=true
SAT_ENABLED=true
EOF

    cat > /etc/astralink/blockchain.env << EOF
CHAIN_ID=22625
NETWORK_NAME=AstraLink_Private_Network
EOF

    cat > /etc/astralink/handshake.env << EOF
HNS_DOMAIN=quantum.api
HNS_NETWORK=mainnet
EOF

    # Set permissions
    chmod 600 /etc/astralink/*.env
    chown astralink:astralink /etc/astralink/*.env
    
    # Reload systemd
    systemctl daemon-reload
}

# Configure system limits
configure_limits() {
    echo -e "\n${BLUE}Configuring system limits...${NC}"
    cat > /etc/security/limits.d/astralink.conf << EOF
astralink soft nofile 65535
astralink hard nofile 65535
astralink soft memlock unlimited
astralink hard memlock unlimited
EOF
}

# Enable and start services
start_services() {
    echo -e "\n${BLUE}Starting AstraLink services...${NC}"
    systemctl enable astralink-node.service
    systemctl enable astralink-quantum.service
    systemctl enable astralink-cellular.service
    systemctl enable astralink-blockchain.service
    systemctl enable astralink-handshake.service
    
    systemctl start astralink-node.service
}

# Check service status
check_services() {
    echo -e "\n${BLUE}Checking service status...${NC}"
    services=("astralink-node" "astralink-quantum" "astralink-cellular" "astralink-blockchain" "astralink-handshake")
    
    for service in "${services[@]}"; do
        status=$(systemctl is-active "$service")
        if [ "$status" = "active" ]; then
            echo -e "${GREEN}$service: Active${NC}"
        else
            echo -e "${RED}$service: Failed${NC}"
            echo "Check logs with: journalctl -u $service"
        fi
    done
}

# Configure AppArmor
configure_apparmor() {
    echo -e "\n${BLUE}Configuring AppArmor...${NC}"
    
    # Ensure AppArmor directories exist
    mkdir -p /etc/apparmor.d/local
    mkdir -p /etc/apparmor.d/disable
    mkdir -p /var/lib/apparmor
    
    # Set up local overrides
    cat > /etc/apparmor.d/local/astralink << EOF
# Local AppArmor overrides for AstraLink services
# Add any site-specific additions here
EOF
    
    # Enable AppArmor profiles
    aa-enforce /etc/apparmor.d/astralink-*
    
    echo -e "${GREEN}AppArmor configured successfully${NC}"
}

# Select deployment environment
select_environment() {
    if [[ $REMOTE_MODE == true ]]; then
        if [[ -z "$CONFIG_FILE" ]]; then
            echo -e "${RED}Remote deployment requires --config parameter${NC}"
            exit 1
        fi
        
        # Extract environment from config
        if grep -q "network: mainnet" "$CONFIG_FILE"; then
            DEPLOY_ENV="mainnet"
        elif grep -q "network: testnet" "$CONFIG_FILE"; then
            DEPLOY_ENV="testnet"
        else
            echo -e "${RED}Invalid network configuration in $CONFIG_FILE${NC}"
            exit 1
        fi
        
        echo -e "${YELLOW}Using ${DEPLOY_ENV} configuration from $CONFIG_FILE${NC}"
        
    else
        echo -e "\n${BLUE}Select deployment environment:${NC}"
        echo "1) Development (local testing, mock hardware)"
        echo "2) Testnet (real hardware, test network)"
        echo "3) Mainnet (production deployment)"
        
        read -p "Select environment [1-3]: " env_choice
        
        case $env_choice in
            1)
                DEPLOY_ENV="development"
                echo -e "${YELLOW}Using development configuration${NC}"
                ;;
            2)
                DEPLOY_ENV="testnet"
                echo -e "${YELLOW}Using testnet configuration${NC}"
                ;;
            3)
                DEPLOY_ENV="mainnet"
                read -p "Are you sure you want to deploy to mainnet? (y/N) " confirm
                if [[ $confirm =~ ^[Yy]$ ]]; then
                    DEPLOY_ENV="mainnet"
                    echo -e "${YELLOW}Using mainnet configuration${NC}"
                else
                    echo "Aborting mainnet deployment"
                    exit 1
                fi
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                exit 1
                ;;
        esac
    fi
}

# Apply environment configuration
apply_configuration() {
    echo -e "\n${BLUE}Applying ${DEPLOY_ENV} configuration...${NC}"
    
    # Create config directory
    mkdir -p /etc/astralink/config
    
    if [[ $REMOTE_MODE == true ]]; then
        # Use provided config file
        cp "$CONFIG_FILE" /etc/astralink/config/config.yaml
    else
        # Use template and process variables
        cp "config/templates/${DEPLOY_ENV}.yaml" /etc/astralink/config/config.yaml
        
        # Replace environment variables
        if [[ $DEPLOY_ENV == "mainnet" ]]; then
            # Prompt for mainnet-specific variables
            read -p "Enter Node IPv4 address: " node_ip
            read -p "Enter Node IPv6 address: " node_ipv6
            
            sed -i "s/\${NODE_IP}/$node_ip/" /etc/astralink/config/config.yaml
            sed -i "s/\${NODE_IPV6}/$node_ipv6/" /etc/astralink/config/config.yaml
        elif [[ $DEPLOY_ENV == "testnet" ]]; then
            # Set testnet defaults
            sed -i "s/\${TEST_NODE_IP}/127.0.0.1/" /etc/astralink/config/config.yaml
        fi
    fi
    
    # Set permissions
    chown -R astralink:astralink /etc/astralink/config
    chmod 600 /etc/astralink/config/config.yaml
    
    echo -e "${GREEN}Configuration applied successfully${NC}"
}

# Update AppArmor profiles based on environment
update_apparmor_profiles() {
    echo -e "\n${BLUE}Updating AppArmor profiles for ${DEPLOY_ENV}...${NC}"
    
    # Add environment-specific rules
    if [[ $DEPLOY_ENV == "development" ]]; then
        echo "  # Development mode additions" >> /etc/apparmor.d/local/astralink
        echo "  /opt/astralink/** rw," >> /etc/apparmor.d/local/astralink
        echo "  /tmp/** rw," >> /etc/apparmor.d/local/astralink
    elif [[ $DEPLOY_ENV == "mainnet" ]]; then
        echo "  # Production hardening" >> /etc/apparmor.d/local/astralink
        echo "  deny /tmp/** w," >> /etc/apparmor.d/local/astralink
        echo "  deny /home/** rwx," >> /etc/apparmor.d/local/astralink
    fi
    
    # Reload profiles
    apparmor_parser -r /etc/apparmor.d/astralink-*
}

# Check quantum readiness
check_quantum_readiness() {
    echo -e "\n${BLUE}Checking quantum capabilities...${NC}"
    
    if ! python3 tools/quantum_readiness.py; then
        if [[ $DEPLOY_ENV == "mainnet" ]]; then
            echo -e "${RED}System does not meet quantum requirements for mainnet deployment${NC}"
            echo "See above for specific requirements that were not met"
            exit 1
        else
            echo -e "${YELLOW}Warning: System does not meet all quantum requirements${NC}"
            echo "Some features may not work or may have reduced security"
            read -p "Continue anyway? (y/N) " confirm
            if [[ ! $confirm =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo -e "${GREEN}System meets quantum requirements${NC}"
    fi
}

# Main installation process
main() {
    # Check AppArmor first
    if ! check_apparmor; then
        echo -e "${RED}Please install and enable AppArmor before proceeding${NC}"
        exit 1
    fi
    
    # Select deployment environment
    select_environment
    
    # Check quantum capabilities
    check_quantum_readiness
    
    # Install basic dependencies first for quantum check
    install_dependencies
    install_python_deps
    
    # Check quantum capabilities
    check_quantum_readiness
    
    create_user
    configure_apparmor
    create_directories
    install_python_deps
    install_services
    configure_limits
    apply_configuration
    update_apparmor_profiles
    start_services
    check_services
    
    echo -e "\n${GREEN}Installation complete!${NC}"
    echo "Environment: ${DEPLOY_ENV}"
    echo "Configuration: /etc/astralink/config/config.yaml"
    echo "Check services: systemctl status astralink-node"
    echo "Check AppArmor: aa-status | grep astralink"
    echo "View logs: journalctl -u astralink-node"
    
    if [[ $DEPLOY_ENV == "development" ]]; then
        echo -e "\n${YELLOW}Development Notes:${NC}"
        echo "- Mock hardware is enabled"
        echo "- Security restrictions are relaxed"
        echo "- Debug logging is enabled"
    elif [[ $DEPLOY_ENV == "testnet" ]]; then
        echo -e "\n${YELLOW}Testnet Notes:${NC}"
        echo "- Using real hardware with test network"
        echo "- Enhanced monitoring enabled"
        echo "- Test tokens available"
    elif [[ $DEPLOY_ENV == "mainnet" ]]; then
        echo -e "\n${YELLOW}Mainnet Notes:${NC}"
        echo "- Maximum security enabled"
        echo "- Production monitoring active"
        echo "- Compliance logging enabled"
    fi
}

# Run installation
main
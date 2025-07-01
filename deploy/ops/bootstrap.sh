#!/usr/bin/env bash
# filepath: /home/haduong/CNRS/projets/actifs/CIRED.digital/cired.digital/deploy/ops/bootstrap.sh
# Bootstrap script for setting up a bare server for Cired.digital deployment

# HOW TO USE after renting a new server:
# 1. Connect to the server
#    ssh <username>@<server-ip>
# 2. Create an admin user
#    sudo adduser admin
#    sudo usermod -aG sudo admin
# 3. Switch to the admin user
#    su - admin
# 4. Configure SSH
#    sudo nano /etc/ssh/sshd_config # And set: PermitRootLogin no
#    sudo systemctl restart sshd
# 5. Copy the bootstrap script to the server
#    scp bootstrap.sh <username>@<server-ip>:~
# 6. Make the script executable
#    chmod +x bootstrap.sh
# 7. Run this bootstrap script
#    ./bootstrap.sh

set -euo pipefail

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] [INFO] $*\033[0m" >&2
}

log_error() {
    echo -e "\033[0;31m[$(date +'%Y-%m-%d %H:%M:%S')] [ERROR] $*\033[0m" >&2
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root for security reasons"
   exit 1
fi

# Disable password authentication for sudo
log "🔒 Hardening SSH configuration..."
sudo sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/^#PermitEmptyPasswords yes/PermitEmptyPasswords no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
log "✅ SSH configuration hardened."

# Update system packages
log "🔄 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install essential tools
log "📦 Installing essential tools..."
sudo apt install -y curl wget git build-essential ufw pipx htop iotop iftop

if ! command -v pipx &> /dev/null; then
    log_error "❌ pipx installation failed. Please install pipx manually."
    exit 1
fi

# Install Docker
log "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Install Docker using official script
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh

    # Add current user to docker group
    sudo usermod -aG docker $USER
    log "✅ Docker installed. You may need to log out and back in for group changes to take effect."
else
    log "✅ Docker already installed."
fi

if ! docker compose version &> /dev/null; then
    log "📦 Installing Docker Compose plugin..."
    sudo apt install -y docker-compose-plugin
    log "✅ Docker Compose plugin installed."
else
    log "✅ Docker Compose plugin already installed."
fi

# Install uv
log "📦 Installing uv..."
if ! command -v uv &> /dev/null; then
    pipx install uv --force
    pipx ensurepath
    log "✅ uv installed."
else
    log "✅ uv already installed."
fi

# Create swap file (from HOWTO-deploy.md)
log "💾 Setting up swap file..."
if ! swapon --show | grep -q "/swapfile"; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    log "✅ 2GB swap file created and enabled."
else
    log "✅ Swap file already exists."
fi

# Setup firewall (from HOWTO-deploy.md and SECURING.md)
log "🔥 Configuring firewall..."
sudo ufw default deny incoming  # Deny all incoming traffic by default
sudo ufw default deny outgoing  # Deny all outgoing traffic by default
sudo ufw allow 22
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose
log "✅ Firewall configured (SSH, HTTP and HTTPS only)."

# Add protection against brute-force attacks
log "🔒 Installing Fail2Ban..."
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
log "✅ Fail2Ban installed and enabled."

# Clone the repository if not already present
REPO_URL="https://github.com/MinhHaDuong/cired.digital.git"  # Update this URL
PROJECT_DIR="$HOME/cired.digital"

if [[ ! -d "$PROJECT_DIR" ]]; then
    log "📥 Cloning repository..."
    git clone "$REPO_URL" "$PROJECT_DIR"
    log "✅ Repository cloned to $PROJECT_DIR"
else
    log "✅ Repository already exists at $PROJECT_DIR"
    cd "$PROJECT_DIR"
    git pull
    log "✅ Repository updated"
fi

# Setup secrets directory structure (from SECURING.md)
log "🔐 Setting up secrets directory structure..."
SECRETS_DIR="$HOME/secrets"
if [[ ! -d "$SECRETS_DIR" ]]; then
    mkdir -p "$SECRETS_DIR/env"
    chmod 700 "$SECRETS_DIR"
    log "✅ Secrets directory created at $SECRETS_DIR"
 else
    log "✅ Secrets directory already exists"
fi

if [[ ! "$(ls -A $SECRETS_DIR/env)" ]]; then
    log_error "❌ Secrets directory is empty. Please populate $SECRETS_DIR/env/ with your environment files."
    exit 1
fi

# Secure secrets directory permissions
chmod 700 "$SECRETS_DIR" 2>/dev/null || true
find "$SECRETS_DIR" -name "*.env" -exec chmod 600 {} \; 2>/dev/null || true

# Add user to docker group (already done but ensure it's effective)
if ! groups $USER | grep -q docker; then
    log "⚠️  Adding user to docker group. You'll need to log out and back in."
    sudo usermod -aG docker $USER
fi

# Run the install script
log "🚀 Running install script..."
cd "$PROJECT_DIR/deploy/ops"
./install.sh

log "🎉 Bootstrap completed successfully!"
log "📍 Project location: $PROJECT_DIR"
log "🔐 Secrets location: $SECRETS_DIR"
log "🔧 To deploy: cd $PROJECT_DIR/deploy/ops && ./deploy.sh"
log "⚠️  IMPORTANT: You need to:"
log "   1. Log out and back in (for Docker group membership)"
log "   2. Populate $SECRETS_DIR/env/ with your environment files"
log "   3. Set proper permissions: find $SECRETS_DIR -name '*.env' -exec chmod 600 {} \\;"
log "   4. Create .env file in deploy/ directory pointing to your secrets"
// ...existing code...

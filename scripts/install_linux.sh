#!/bin/bash
# 24/7 Global Stock Market Monitor - Linux Desktop Installer
# This script sets up the monitoring system on Linux desktop environments

set -e  # Exit on any error

echo "================================================================"
echo "  24/7 Global Stock Market Monitor - Linux Desktop Setup"
echo "================================================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}[$1] $2${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Detect Linux distribution
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        echo "$ID"
    elif [[ -f /etc/redhat-release ]]; then
        echo "rhel"
    elif [[ -f /etc/debian_version ]]; then
        echo "debian"
    else
        echo "unknown"
    fi
}

# Get installation directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$INSTALL_DIR"

echo "Installation Directory: $INSTALL_DIR"
echo

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script is designed for Linux only"
    exit 1
fi

# Detect distribution
DISTRO=$(detect_distro)
echo "Detected distribution: $DISTRO"
echo

# Check if running as root (not recommended)
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root is not recommended"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python installation
print_step "1/8" "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION detected"
    
    # Check if version is 3.8+
    if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_success "Python version is compatible"
    else
        print_error "Python 3.8+ required"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.8+"
    exit 1
fi
echo

# Install system dependencies based on distribution
print_step "2/8" "Installing system dependencies..."

case "$DISTRO" in
    "ubuntu"|"debian"|"pop"|"elementary"|"linuxmint")
        print_step "2a" "Updating package lists..."
        sudo apt-get update
        
        print_step "2b" "Installing packages for Ubuntu/Debian..."
        sudo apt-get install -y \
            postgresql postgresql-contrib \
            redis-server \
            python3-pip python3-venv python3-dev \
            git curl wget \
            build-essential \
            pkg-config \
            libpq-dev \
            libffi-dev \
            libssl-dev \
            libjpeg-dev \
            libpng-dev \
            libfreetype6-dev \
            nodejs npm \
            software-properties-common \
            apt-transport-https \
            ca-certificates \
            gnupg \
            lsb-release
        
        # Start and enable services
        sudo systemctl enable postgresql
        sudo systemctl start postgresql
        sudo systemctl enable redis-server
        sudo systemctl start redis-server
        ;;
        
    "fedora"|"centos"|"rhel"|"rocky"|"almalinux")
        print_step "2a" "Installing packages for Fedora/RHEL..."
        if command -v dnf &> /dev/null; then
            PKG_MANAGER="dnf"
        else
            PKG_MANAGER="yum"
        fi
        
        sudo $PKG_MANAGER install -y \
            postgresql postgresql-server postgresql-contrib \
            redis \
            python3-pip python3-virtualenv python3-devel \
            git curl wget \
            gcc gcc-c++ \
            pkgconfig \
            postgresql-devel \
            libffi-devel \
            openssl-devel \
            libjpeg-turbo-devel \
            libpng-devel \
            freetype-devel \
            nodejs npm
        
        # Initialize PostgreSQL
        sudo postgresql-setup --initdb 2>/dev/null || true
        
        # Start and enable services
        sudo systemctl enable postgresql
        sudo systemctl start postgresql
        sudo systemctl enable redis
        sudo systemctl start redis
        ;;
        
    "arch"|"manjaro")
        print_step "2a" "Installing packages for Arch Linux..."
        sudo pacman -S --noconfirm \
            postgresql \
            redis \
            python-pip python-virtualenv \
            git curl wget \
            base-devel \
            pkgconfig \
            postgresql-libs \
            libffi \
            openssl \
            libjpeg-turbo \
            libpng \
            freetype2 \
            nodejs npm
        
        # Initialize PostgreSQL
        sudo -u postgres initdb -D /var/lib/postgres/data 2>/dev/null || true
        
        # Start and enable services
        sudo systemctl enable postgresql
        sudo systemctl start postgresql
        sudo systemctl enable redis
        sudo systemctl start redis
        ;;
        
    "opensuse"|"suse")
        print_step "2a" "Installing packages for openSUSE..."
        sudo zypper install -y \
            postgresql postgresql-server postgresql-contrib \
            redis \
            python3-pip python3-virtualenv python3-devel \
            git curl wget \
            gcc gcc-c++ \
            pkg-config \
            postgresql-devel \
            libffi-devel \
            openssl-devel \
            libjpeg8-devel \
            libpng16-devel \
            freetype2-devel \
            nodejs npm
        
        # Start and enable services
        sudo systemctl enable postgresql
        sudo systemctl start postgresql
        sudo systemctl enable redis
        sudo systemctl start redis
        ;;
        
    *)
        print_warning "Unknown distribution. Please install the following manually:"
        echo "- PostgreSQL 13+"
        echo "- Redis"
        echo "- Python 3.8+ with pip and venv"
        echo "- Git, curl, wget"
        echo "- Build tools (gcc, make, etc.)"
        echo "- Development libraries (libpq-dev, libffi-dev, etc.)"
        ;;
esac

print_success "System dependencies installed"
echo

# Check Docker
print_step "3/8" "Checking Docker..."
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null 2>&1; then
        print_success "Docker is running"
    else
        print_warning "Docker is installed but not running or you don't have permission"
        echo "Try: sudo usermod -aG docker $USER"
        echo "Then logout and login again"
    fi
else
    print_warning "Docker not found. Installing Docker..."
    
    # Install Docker
    case "$DISTRO" in
        "ubuntu"|"debian")
            curl -fsSL https://download.docker.com/linux/$DISTRO/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$DISTRO $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        "fedora")
            sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
            ;;
        "arch")
            sudo pacman -S docker docker-compose
            ;;
        *)
            print_warning "Please install Docker manually for your distribution"
            ;;
    esac
    
    # Start Docker service
    sudo systemctl enable docker
    sudo systemctl start docker
    
    # Add user to docker group
    sudo usermod -aG docker $USER
    print_success "Docker installed. Please logout and login again to use Docker without sudo"
fi
echo

# Create virtual environment
print_step "4/8" "Setting up Python environment..."
if [[ -d "venv" ]]; then
    print_success "Virtual environment already exists"
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip

if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    print_success "Core Python dependencies installed"
else
    print_warning "requirements.txt not found"
fi

# Install desktop-specific requirements
if [[ -f "requirements.desktop.txt" ]]; then
    pip install -r requirements.desktop.txt || print_warning "Some desktop-specific packages failed to install"
    print_success "Desktop-specific packages installed"
fi
echo

# Setup database
print_step "5/8" "Setting up database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 3

# Create database and user
echo "Creating database and user..."
sudo -u postgres createdb stock_monitor 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER stock_user WITH PASSWORD 'stock_password';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER USER stock_user CREATEDB;" 2>/dev/null || true

print_success "Database setup completed"
echo

# Create configuration
print_step "6/8" "Creating configuration..."
if [[ ! -f "config/config.yaml" ]]; then
    if [[ -f "config/config.example.yaml" ]]; then
        cp config/config.example.yaml config/config.yaml
        print_success "Configuration file created from example"
    else
        print_warning "config.example.yaml not found"
    fi
else
    print_success "Configuration file already exists"
fi

# Run desktop setup script
python scripts/setup_desktop.py --skip-system --skip-db 2>/dev/null || true
echo

# Create shortcuts and launchers
print_step "7/8" "Creating desktop shortcuts..."

# Create scripts directory
mkdir -p scripts/linux

# Create start script
cat > scripts/linux/start_monitor.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
source venv/bin/activate
python src/main.py
EOF
chmod +x scripts/linux/start_monitor.sh

# Create dashboard launcher
cat > scripts/linux/open_dashboard.sh << 'EOF'
#!/bin/bash
xdg-open http://localhost:8080
EOF
chmod +x scripts/linux/open_dashboard.sh

# Create Grafana launcher
cat > scripts/linux/open_grafana.sh << 'EOF'
#!/bin/bash
xdg-open http://localhost:3000
EOF
chmod +x scripts/linux/open_grafana.sh

# Create Docker launcher
cat > scripts/linux/start_docker.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
docker-compose -f docker-compose.desktop.yml up -d
echo "Docker services started"
echo "Dashboard: http://localhost:8080"
echo "Grafana: http://localhost:3000"
EOF
chmod +x scripts/linux/start_docker.sh

# Create desktop entries
mkdir -p ~/.local/share/applications

# Stock Monitor desktop entry
cat > ~/.local/share/applications/stock-monitor.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Market Monitor
Comment=24/7 Global Stock Market Monitoring System
Exec=$INSTALL_DIR/scripts/linux/start_monitor.sh
Icon=utilities-system-monitor
Terminal=true
Categories=Office;Finance;
EOF

# Dashboard launcher desktop entry
cat > ~/.local/share/applications/stock-dashboard.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Monitor Dashboard
Comment=Open Stock Monitor Web Dashboard
Exec=$INSTALL_DIR/scripts/linux/open_dashboard.sh
Icon=web-browser
Terminal=false
Categories=Office;Finance;Network;
EOF

# Add shell aliases
SHELL_RC=""
if [[ -f "$HOME/.bashrc" ]]; then
    SHELL_RC="$HOME/.bashrc"
elif [[ -f "$HOME/.zshrc" ]]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [[ -n "$SHELL_RC" ]]; then
    echo "" >> "$SHELL_RC"
    echo "# Stock Monitor Aliases" >> "$SHELL_RC"
    echo "alias stock-monitor='cd \"$INSTALL_DIR\" && source venv/bin/activate && python src/main.py'" >> "$SHELL_RC"
    echo "alias stock-dashboard='xdg-open http://localhost:8080'" >> "$SHELL_RC"
    echo "alias stock-grafana='xdg-open http://localhost:3000'" >> "$SHELL_RC"
    echo "alias stock-docker='cd \"$INSTALL_DIR\" && docker-compose -f docker-compose.desktop.yml up -d'" >> "$SHELL_RC"
    print_success "Shell aliases added to $SHELL_RC"
fi

print_success "Desktop shortcuts and launchers created"
echo

# Setup systemd service (optional)
print_step "8/8" "Setting up systemd service (optional)..."

cat > ~/.config/systemd/user/stock-monitor.service << EOF
[Unit]
Description=Stock Market Monitor
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

# Enable user systemd directory
mkdir -p ~/.config/systemd/user
systemctl --user daemon-reload

print_success "Systemd service created (use 'systemctl --user enable stock-monitor' to enable)"
echo

echo
echo "================================================================"
echo "  INSTALLATION COMPLETED SUCCESSFULLY!"
echo "================================================================"
echo
echo "Next Steps:"
echo
echo "1. Edit configuration file with your API keys:"
echo "   config/config.yaml"
echo
echo "2. Start the monitoring system:"
echo "   - Run: ./scripts/linux/start_monitor.sh"
echo "   - Or from Applications menu: Stock Market Monitor"
echo "   - Or use alias: stock-monitor (after restarting terminal)"
echo
echo "3. Alternative - Use Docker (recommended):"
echo "   - Run: ./scripts/linux/start_docker.sh"
echo "   - Or use alias: stock-docker"
echo
echo "4. Run as background service:"
echo "   - Enable: systemctl --user enable stock-monitor"
echo "   - Start: systemctl --user start stock-monitor"
echo "   - Status: systemctl --user status stock-monitor"
echo
echo "5. Access the applications:"
echo "   - Main Dashboard: http://localhost:8080"
echo "   - Grafana Dashboard: http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo
echo "6. Quick access commands (after restarting terminal):"
echo "   - stock-monitor    # Start the monitoring system"
echo "   - stock-dashboard  # Open dashboard in browser"
echo "   - stock-grafana    # Open Grafana in browser"
echo "   - stock-docker     # Start with Docker"
echo
echo "7. For help and documentation:"
echo "   - See README.md and docs/ folder"
echo "   - Desktop-specific guide: docs/DESKTOP_SETUP.md"
echo
echo "Enjoy monitoring the global stock markets 24/7!"
echo
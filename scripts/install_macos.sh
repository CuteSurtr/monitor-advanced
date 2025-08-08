#!/bin/bash
# 24/7 Global Stock Market Monitor - macOS Desktop Installer
# This script sets up the monitoring system on macOS desktop environments

set -e  # Exit on any error

echo "================================================================"
echo "  24/7 Global Stock Market Monitor - macOS Desktop Setup"
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

# Get installation directory
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$INSTALL_DIR"

echo "Installation Directory: $INSTALL_DIR"
echo

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS only"
    exit 1
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
        print_error "Python 3.8+ required. Please install from: https://www.python.org/downloads/"
        exit 1
    fi
else
    print_error "Python not found. Please install Python 3.8+ from:"
    echo "https://www.python.org/downloads/"
    exit 1
fi
echo

# Check for Homebrew
print_step "2/8" "Checking package manager..."
if command -v brew &> /dev/null; then
    print_success "Homebrew detected"
else
    print_warning "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    if command -v brew &> /dev/null; then
        print_success "Homebrew installed successfully"
    else
        print_error "Failed to install Homebrew"
        exit 1
    fi
fi
echo

# Install system dependencies
print_step "3/8" "Installing system dependencies..."

echo "Installing PostgreSQL..."
if brew list postgresql@15 &> /dev/null; then
    print_success "PostgreSQL already installed"
else
    brew install postgresql@15
    print_success "PostgreSQL installed"
fi

echo "Installing Redis..."
if brew list redis &> /dev/null; then
    print_success "Redis already installed"
else
    brew install redis
    print_success "Redis installed"
fi

echo "Installing Node.js..."
if brew list node &> /dev/null; then
    print_success "Node.js already installed"
else
    brew install node
    print_success "Node.js installed"
fi

echo "Installing additional tools..."
brew install git curl wget || true

# Start services
echo "Starting database services..."
brew services start postgresql@15 2>/dev/null || true
brew services start redis 2>/dev/null || true

print_success "System dependencies installed"
echo

# Check Docker
print_step "4/8" "Checking Docker..."
if command -v docker &> /dev/null; then
    if docker ps &> /dev/null; then
        print_success "Docker is running"
    else
        print_warning "Docker is installed but not running"
        echo "Please start Docker Desktop from Applications"
    fi
else
    print_warning "Docker not found. Installing Docker Desktop..."
    if brew list --cask docker &> /dev/null; then
        print_success "Docker Desktop already installed"
    else
        brew install --cask docker
        print_success "Docker Desktop installed"
        echo "Please start Docker Desktop from Applications and run this script again"
        exit 0
    fi
fi
echo

# Create virtual environment
print_step "5/8" "Setting up Python environment..."
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
print_step "6/8" "Setting up database..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to start..."
sleep 3

# Create database and user
echo "Creating database and user..."
createdb stock_monitor 2>/dev/null || true
psql postgres -c "CREATE USER stock_user WITH PASSWORD 'stock_password';" 2>/dev/null || true
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE stock_monitor TO stock_user;" 2>/dev/null || true
psql postgres -c "ALTER USER stock_user CREATEDB;" 2>/dev/null || true

print_success "Database setup completed"
echo

# Create configuration
print_step "7/8" "Creating configuration..."
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
print_step "8/8" "Creating desktop shortcuts..."

# Create scripts directory
mkdir -p scripts/macos

# Create start script
cat > scripts/macos/start_monitor.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
source venv/bin/activate
python src/main.py
EOF
chmod +x scripts/macos/start_monitor.sh

# Create dashboard launcher
cat > scripts/macos/open_dashboard.sh << 'EOF'
#!/bin/bash
open http://localhost:8080
EOF
chmod +x scripts/macos/open_dashboard.sh

# Create Grafana launcher
cat > scripts/macos/open_grafana.sh << 'EOF'
#!/bin/bash
open http://localhost:3000
EOF
chmod +x scripts/macos/open_grafana.sh

# Create Docker launcher
cat > scripts/macos/start_docker.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/../.."
docker-compose -f docker-compose.desktop.yml up -d
echo "Docker services started"
echo "Dashboard: http://localhost:8080"
echo "Grafana: http://localhost:3000"
EOF
chmod +x scripts/macos/start_docker.sh

# Create desktop aliases in shell profile
SHELL_PROFILE=""
if [[ -f "$HOME/.zshrc" ]]; then
    SHELL_PROFILE="$HOME/.zshrc"
elif [[ -f "$HOME/.bash_profile" ]]; then
    SHELL_PROFILE="$HOME/.bash_profile"
fi

if [[ -n "$SHELL_PROFILE" ]]; then
    echo "" >> "$SHELL_PROFILE"
    echo "# Stock Monitor Aliases" >> "$SHELL_PROFILE"
    echo "alias stock-monitor='cd \"$INSTALL_DIR\" && source venv/bin/activate && python src/main.py'" >> "$SHELL_PROFILE"
    echo "alias stock-dashboard='open http://localhost:8080'" >> "$SHELL_PROFILE"
    echo "alias stock-grafana='open http://localhost:3000'" >> "$SHELL_PROFILE"
    echo "alias stock-docker='cd \"$INSTALL_DIR\" && docker-compose -f docker-compose.desktop.yml up -d'" >> "$SHELL_PROFILE"
    print_success "Shell aliases added to $SHELL_PROFILE"
fi

print_success "Desktop shortcuts created"
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
echo "   - Run: ./scripts/macos/start_monitor.sh"
echo "   - Or use alias: stock-monitor (after restarting terminal)"
echo
echo "3. Alternative - Use Docker (recommended):"
echo "   - Run: ./scripts/macos/start_docker.sh"
echo "   - Or use alias: stock-docker"
echo
echo "4. Access the applications:"
echo "   - Main Dashboard: http://localhost:8080"
echo "   - Grafana Dashboard: http://localhost:3000"
echo "   - Prometheus: http://localhost:9090"
echo
echo "5. Quick access commands (after restarting terminal):"
echo "   - stock-monitor    # Start the monitoring system"
echo "   - stock-dashboard  # Open dashboard in browser"
echo "   - stock-grafana    # Open Grafana in browser"
echo "   - stock-docker     # Start with Docker"
echo
echo "6. For help and documentation:"
echo "   - See README.md and docs/ folder"
echo "   - Desktop-specific guide: docs/DESKTOP_SETUP.md"
echo
echo "Enjoy monitoring the global stock markets 24/7!"
echo
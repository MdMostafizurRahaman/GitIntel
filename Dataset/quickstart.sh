#!/bin/bash
# Dataset Management System - Quick Start Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Dataset Management System - Quick Start                 ║"
echo "║   সিস্টেম দ্রুত শুরুর স্ক্রিপ্ট                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check Python
print_step "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if in correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from Dataset directory."
    exit 1
fi

print_success "In correct directory"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    print_step "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Install requirements
print_step "Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "Packages installed"

# Verify installation
print_step "Verifying installation..."
python3 verify_installation.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Installation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "📚 Next steps:"
    echo "   1. Read: docs/SETUP.md (configuration & Neo4j setup)"
    echo "   2. Configure Neo4j (create .env file with credentials)"
    echo "   3. Test: python -m cli.main status"
    echo ""
    echo "🚀 Choose your interface:"
    echo "   • CLI:  python -m cli.main --help"
    echo "   • GUI:  python -m gui.app"
    echo "   • API:  python -m api.server"
    echo ""
    echo "📖 Documentation:"
    echo "   • Setup:       docs/SETUP.md"
    echo "   • Examples:    docs/EXAMPLES.md"
    echo "   • Architecture: docs/ARCHITECTURE.md"
    echo "   • Reference:   SUMMARY.md"
    echo ""
else
    echo ""
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}✗ Installation Verification Failed${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "⚠️  Please fix the issues above and try again."
    echo ""
    exit 1
fi

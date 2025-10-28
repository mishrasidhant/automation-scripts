#!/bin/bash
# Smart development environment setup (UV Migration)
# Usage: source scripts/setup-dev.sh [module|all|dev]

# Use AUTOMATION_SCRIPTS_DIR if set, otherwise auto-detect
PROJECT_ROOT="${AUTOMATION_SCRIPTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: source scripts/setup-dev.sh [module|all|dev]"
    echo ""
    echo "Options:"
    echo "  dictation   Install dictation module dependencies"
    echo "  all         Install all module dependencies"
    echo "  dev         Install dev tools (pytest, ruff, mypy)"
    echo "  (none)      Just check UV installation"
    echo ""
    echo "Examples:"
    echo "  source scripts/setup-dev.sh dictation  # Install dictation deps"
    echo "  source scripts/setup-dev.sh dev        # Install dev tools"
    echo "  source scripts/setup-dev.sh            # Check UV only"
    echo ""
    echo "Note: UV manages dependencies automatically. No manual venv activation needed!"
}

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV not found${NC}"
    echo ""
    echo "UV is required for this project. Install with:"
    echo ""
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Then restart your shell or run:"
    echo "  source \$HOME/.local/bin/env"
    echo ""
    return 1
fi

echo -e "${GREEN}✅ UV installed: $(uv --version)${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Verify pyproject.toml exists
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml not found at $PROJECT_ROOT${NC}"
    return 1
fi

# Check system dependencies
check_system_deps() {
    echo -e "${BLUE}🔍 Checking system dependencies...${NC}"
    MISSING=""
    
    # Check for portaudio (required by sounddevice)
    if ! pacman -Q portaudio &>/dev/null; then
        echo -e "${YELLOW}⚠️  portaudio not found (required for audio recording)${NC}"
        MISSING="$MISSING portaudio"
    else
        echo -e "${GREEN}  ✓ portaudio${NC}"
    fi
    
    # Check for xdotool (required for text injection)
    if ! command -v xdotool &>/dev/null; then
        echo -e "${YELLOW}⚠️  xdotool not found (required for text injection)${NC}"
        MISSING="$MISSING xdotool"
    else
        echo -e "${GREEN}  ✓ xdotool${NC}"
    fi
    
    # Check for notify-send (required for notifications)
    if ! command -v notify-send &>/dev/null; then
        echo -e "${YELLOW}⚠️  libnotify not found (required for notifications)${NC}"
        MISSING="$MISSING libnotify"
    else
        echo -e "${GREEN}  ✓ libnotify${NC}"
    fi
    
    if [ -n "$MISSING" ]; then
        echo ""
        echo -e "${YELLOW}📦 Install missing system dependencies:${NC}"
        echo "  sudo pacman -S$MISSING"
        echo ""
        echo -e "${YELLOW}⚠️  Python dependencies will install, but may not work without system packages${NC}"
        echo ""
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
}

# Install dependencies if module specified
MODULE="$1"

if [ -n "$MODULE" ]; then
    case "$MODULE" in
        dictation)
            # Check system dependencies before installing
            check_system_deps
            if [ $? -ne 0 ]; then
                return 1
            fi
            
            echo -e "${BLUE}📥 Installing dictation dependencies with UV...${NC}"
            uv sync --extra dictation
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Dictation dependencies installed${NC}"
            else
                echo -e "${RED}❌ Failed to install dictation dependencies${NC}"
                return 1
            fi
            ;;
        all)
            echo -e "${BLUE}📥 Installing all module dependencies with UV...${NC}"
            uv sync --all-extras
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ All dependencies installed${NC}"
            else
                echo -e "${RED}❌ Failed to install dependencies${NC}"
                return 1
            fi
            ;;
        dev)
            echo -e "${BLUE}📥 Installing dev tools with UV...${NC}"
            uv sync --group dev --extra dictation
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Development environment ready${NC}"
            else
                echo -e "${RED}❌ Failed to install dev dependencies${NC}"
                return 1
            fi
            ;;
        help|--help|-h)
            show_usage
            return 0
            ;;
        *)
            echo -e "${YELLOW}⚠️  Unknown module: $MODULE${NC}"
            show_usage
            return 1
            ;;
    esac
fi

echo ""
echo -e "${GREEN}🎯 UV Development Environment Ready${NC}"
echo "UV: $(which uv)"
echo "Version: $(uv --version)"
echo ""
echo "📍 Project: $PROJECT_ROOT"
echo ""
echo "Available UV commands:"
echo "  uv run dictation-toggle --start       # Run dictation directly"
echo "  uv run python -m automation_scripts.dictation --toggle"
echo "  uv run pytest                         # Run tests (if dev installed)"
echo "  uv pip list                           # Show installed packages"
echo "  uv sync --extra dictation            # Reinstall dependencies"
echo ""
echo "Legacy commands (still work):"
echo "  cd modules/dictation                  # Go to original module"
echo ""

if [ -z "$MODULE" ]; then
    echo -e "${YELLOW}💡 Tip: Install dependencies with:${NC}"
    echo "   source scripts/setup-dev.sh dictation"
    echo ""
    echo "Or use UV directly:"
    echo "   uv sync --extra dictation"
    echo ""
fi

# Note: No need to activate venv - UV handles it automatically
echo -e "${GREEN}📝 Note: UV manages virtual environments automatically${NC}"
echo "   No need to activate/deactivate - just use 'uv run <command>'"
echo ""

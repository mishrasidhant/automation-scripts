#!/bin/bash
# Smart development environment setup
# Usage: source scripts/setup-dev.sh [module|all|dev]

# Use AUTOMATION_SCRIPTS_DIR if set, otherwise auto-detect
PROJECT_ROOT="${AUTOMATION_SCRIPTS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
VENV_DIR="$PROJECT_ROOT/.venv"

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
    echo "  dev         Install dev tools + all dependencies"
    echo "  (none)      Just activate virtual environment"
    echo ""
    echo "Examples:"
    echo "  source scripts/setup-dev.sh dictation"
    echo "  source scripts/setup-dev.sh all"
    echo "  source scripts/setup-dev.sh"
}

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        return 1
    fi
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Verify activation worked
if [ "$VIRTUAL_ENV" != "$VENV_DIR" ]; then
    echo -e "${RED}❌ Failed to activate virtual environment${NC}"
    return 1
fi

# Upgrade pip quietly (use explicit path to be sure)
"$VENV_DIR/bin/pip" install --upgrade pip > /dev/null 2>&1

echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install dependencies if module specified
MODULE="$1"

if [ -n "$MODULE" ]; then
    case "$MODULE" in
        dictation|backup|monitoring)
            if [ -f "$PROJECT_ROOT/requirements/$MODULE.txt" ]; then
                echo -e "${BLUE}📥 Installing $MODULE dependencies...${NC}"
                "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements/$MODULE.txt"
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}✅ $MODULE dependencies installed${NC}"
                else
                    echo -e "${RED}❌ Failed to install $MODULE dependencies${NC}"
                    return 1
                fi
            else
                echo -e "${YELLOW}⚠️  Requirements file not found: requirements/$MODULE.txt${NC}"
                return 1
            fi
            ;;
        all)
            echo -e "${BLUE}📥 Installing all module dependencies...${NC}"
            "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements/all.txt"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ All dependencies installed${NC}"
            else
                echo -e "${RED}❌ Failed to install dependencies${NC}"
                return 1
            fi
            ;;
        dev)
            echo -e "${BLUE}📥 Installing dev tools + all dependencies...${NC}"
            "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements/dev.txt"
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
echo -e "${GREEN}🎯 Development Environment Ready${NC}"
echo "Python: $(which python3)"
echo "Version: $(python3 --version 2>&1)"
echo "Pip: $(which pip)"
echo ""
echo "📍 Project: $PROJECT_ROOT"
echo ""
echo "Available commands:"
echo "  pip list                           # Show installed packages"
echo "  cd modules/dictation              # Go to dictation module"
echo "  python modules/dictation/test_dictate.py  # Run tests"
echo "  deactivate                        # Exit virtual environment"
echo ""

if [ -z "$MODULE" ]; then
    echo -e "${YELLOW}💡 Tip: Install dependencies with:${NC}"
    echo "   source scripts/setup-dev.sh dictation"
    echo ""
fi


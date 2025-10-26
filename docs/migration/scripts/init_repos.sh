#!/bin/bash
# Initialize both new repositories for BETA release

set -e

PARENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODBUS_DIR="$PARENT_DIR/ha-abb-fimer-pvi-sunspec"
REST_DIR="$PARENT_DIR/ha-abb-fimer-pvi-vsn-rest"

echo "==================================================================="
echo "Initializing ABB/FIMER PVI Integration Repositories"
echo "==================================================================="

# Initialize Modbus repo
echo ""
echo "Initializing Modbus integration..."
cd "$MODBUS_DIR"
git init
git add .
git commit -m "Initial commit: v1.0.0-beta.1

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git tag -a v1.0.0-beta.1 -m "Release v1.0.0-beta.1 (BETA)"
echo "✅ Modbus repo initialized"

# Initialize REST repo
echo ""
echo "Initializing REST integration..."
cd "$REST_DIR"
git init
git add .
git commit -m "Initial commit: v1.0.0-beta.1

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
git tag -a v1.0.0-beta.1 -m "Release v1.0.0-beta.1 (BETA)"
echo "✅ REST repo initialized"

echo ""
echo "==================================================================="
echo "✅ Repositories initialized!"
echo "==================================================================="
echo ""
echo "Next steps:"
echo "1. Review the generated files in both repositories"
echo "2. Create GitHub repos using:"
echo "   cd $MODBUS_DIR && gh repo create alexdelprete/ha-abb-fimer-pvi-sunspec --public --source=. --push"
echo "   cd $REST_DIR && gh repo create alexdelprete/ha-abb-fimer-pvi-vsn-rest --public --source=. --push"
echo ""
echo "3. Create pre-releases:"
echo "   cd $MODBUS_DIR && gh release create v1.0.0-beta.1 --prerelease --title 'v1.0.0-beta.1' --notes 'Initial beta release'"
echo "   cd $REST_DIR && gh release create v1.0.0-beta.1 --prerelease --title 'v1.0.0-beta.1' --notes 'Initial beta release'"
echo ""

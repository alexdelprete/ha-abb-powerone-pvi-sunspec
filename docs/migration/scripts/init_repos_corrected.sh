#!/bin/bash
# Initialize and publish both new repositories for BETA release

set -e

PARENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MODBUS_DIR="$PARENT_DIR/ha-abb-fimer-pvi-sunspec"
REST_DIR="$PARENT_DIR/ha-abb-fimer-pvi-vsn-rest"
VERSION="v1.0.0-beta.1"

echo "==================================================================="
echo "Creating ABB/FIMER PVI Integration Repositories on GitHub"
echo "==================================================================="
echo ""
echo "This will:"
echo "1. Create GitHub repositories (public)"
echo "2. Initialize git locally"
echo "3. Create initial commit"
echo "4. Tag $VERSION"
echo "5. Push to GitHub"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Function to initialize and publish a repo
init_and_publish() {
    local DIR=$1
    local REPO_NAME=$2
    local DESCRIPTION=$3

    echo ""
    echo "==================================================================="
    echo "Processing: $REPO_NAME"
    echo "==================================================================="

    cd "$DIR"

    # Step 1: Create GitHub repo (this will fail if repo already exists, which is fine)
    echo "Creating GitHub repository..."
    gh repo create "alexdelprete/$REPO_NAME" \
        --public \
        --description "$DESCRIPTION" \
        --clone=false \
        || echo "Repository may already exist, continuing..."

    # Step 2: Initialize git locally
    echo "Initializing local git repository..."
    if [ ! -d .git ]; then
        git init
    fi

    # Step 3: Add remote origin
    echo "Adding remote origin..."
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/alexdelprete/$REPO_NAME.git"

    # Step 4: Add all files
    echo "Staging files..."
    git add .

    # Step 5: Create initial commit
    echo "Creating initial commit..."
    git commit -m "Initial commit: $VERSION

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>" || echo "Commit may already exist"

    # Step 6: Rename branch to master (if needed)
    git branch -M master

    # Step 7: Create tag
    echo "Creating tag $VERSION..."
    git tag -a "$VERSION" -m "Release $VERSION (BETA)" -f

    # Step 8: Push to GitHub
    echo "Pushing to GitHub..."
    git push -u origin master --force
    git push origin "$VERSION" --force

    echo "✅ $REPO_NAME complete!"
}

# Initialize Modbus integration
init_and_publish \
    "$MODBUS_DIR" \
    "ha-abb-fimer-pvi-sunspec" \
    "ABB/FIMER PVI inverters - Modbus/TCP integration for Home Assistant"

# Initialize REST integration
init_and_publish \
    "$REST_DIR" \
    "ha-abb-fimer-pvi-vsn-rest" \
    "ABB/FIMER PVI inverters - VSN300/VSN700 REST API integration for Home Assistant"

echo ""
echo "==================================================================="
echo "✅ Both repositories created and pushed!"
echo "==================================================================="
echo ""
echo "Repositories:"
echo "  Modbus: https://github.com/alexdelprete/ha-abb-fimer-pvi-sunspec"
echo "  REST:   https://github.com/alexdelprete/ha-abb-fimer-pvi-vsn-rest"
echo ""
echo "Next steps:"
echo "1. Begin development work on TODO sections"
echo "2. Download SunSpec models to vendor/sunspec_models/json/"
echo "3. Test with real hardware"
echo "4. Create GitHub releases when ready for beta testing"
echo ""

#!/bin/sh
set -e

# Ensure we're in the project root (VS Code mounts workspace to /workspaces/<name>)
cd "$(dirname "$0")/.."

echo "Installing Python requirements..."
pip install -r requirements.txt

echo "Validating project structure..."
make validate-project

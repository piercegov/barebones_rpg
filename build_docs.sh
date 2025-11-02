#!/bin/bash
# Build Sphinx documentation

set -e

cd "$(dirname "$0")/sphinx_docs"

echo "Building Sphinx documentation..."
echo "================================"
echo

uv run sphinx-build -b html . _build/html

echo
echo "================================"
echo "Documentation built successfully!"
echo "Open sphinx_docs/_build/html/index.html to view."
echo
echo "Or run: open sphinx_docs/_build/html/index.html"


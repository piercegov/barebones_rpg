# Barebones RPG Documentation

This directory contains the Sphinx documentation source files for the Barebones RPG Framework.

## Building the Documentation

### Quick Build

From the project root:
```bash
./build_docs.sh
```

### Using Make

```bash
cd sphinx_docs
make html        # Build HTML documentation
make clean       # Remove build artifacts
make livehtml    # Auto-rebuilding server
```

### Manual Build

```bash
cd sphinx_docs
uv run sphinx-build -b html . _build/html
```

## Viewing the Documentation

After building, open `_build/html/index.html` in your web browser:

```bash
# macOS
open _build/html/index.html

# Linux
xdg-open _build/html/index.html

# Windows
start _build/html/index.html
```

## Documentation Structure

```
sphinx_docs/
├── conf.py              # Sphinx configuration
├── index.rst            # Main documentation index
├── getting_started.rst  # Installation and quick start
├── core_concepts.rst    # Architecture overview
├── api/                 # Auto-generated API docs
│   ├── core.rst
│   ├── entities.rst
│   ├── combat.rst
│   └── ...
├── tutorials/           # Step-by-step tutorials
├── guides/              # In-depth topic guides
├── examples/            # Example game breakdowns
└── _build/              # Generated documentation (gitignored)
```

## Adding New Documentation

### New Pages

1. Create a new `.rst` file in the appropriate directory
2. Add it to the relevant `toctree` in `index.rst` or section index
3. Rebuild the documentation

### Updating API Docs

API documentation is auto-generated from docstrings. To update:

1. Edit docstrings in the source code
2. Rebuild the documentation

### Writing ReStructuredText

Basic syntax examples:

```rst
Section Headers
===============

Subsection
----------

**bold text**
*italic text*
``code``

.. code-block:: python

   def example():
       return "Hello"

- Bullet list
- Another item

1. Numbered list
2. Another item
```

## Theme Customization

The documentation uses the Furo theme. Customize in `conf.py`:

```python
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#7C4DFF",  # Change primary color
    },
}
```

## Requirements

Documentation dependencies are in `pyproject.toml`:

- sphinx >= 7.0.0
- furo >= 2023.0.0 (theme)
- sphinx-autodoc-typehints >= 1.24.0
- myst-parser >= 2.0.0 (Markdown support)

## Tips

- Use `make livehtml` for auto-rebuilding during development
- Check `_build/html` is in `.gitignore`
- Run `make clean` before committing to ensure fresh builds
- Test cross-references with `make linkcheck`


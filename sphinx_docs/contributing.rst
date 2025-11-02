Contributing
============

We welcome contributions to Barebones RPG Framework!

How to Contribute
-----------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

Development Setup
-----------------

.. code-block:: bash

   # Clone the repository
   git clone <your-fork-url>
   cd barebones_rpg

   # Install with dev dependencies
   uv sync --dev

   # Run tests
   uv run pytest

   # Format code
   uv run black .

   # Type checking
   uv run mypy barebones_rpg

Guidelines
----------

Code Style
~~~~~~~~~~

- Follow PEP 8
- Use type hints
- Write docstrings for all public APIs
- Format with Black

Testing
~~~~~~~

- Write tests for new features
- Maintain test coverage
- Test edge cases
- Use pytest fixtures

Documentation
~~~~~~~~~~~~~

- Update docstrings
- Add examples
- Update relevant guides
- Regenerate Sphinx docs

Areas for Contribution
----------------------

We're especially interested in contributions for:

- Additional example games
- More AI implementations
- Custom combat actions
- Renderer implementations
- Data loaders
- Documentation improvements
- Bug fixes

Questions?
----------

Open an issue on GitHub or start a discussion.


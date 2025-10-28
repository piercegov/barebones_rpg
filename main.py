"""Main entry point for Barebones RPG Framework.

This runs the mini RPG example by default to demonstrate the framework.
"""


def main():
    """Run the mini RPG example."""
    print("Barebones RPG Framework v0.1.0\n")
    print("Running the mini RPG example...")
    print("(Check barebones_rpg/examples/ for more examples)\n")

    # Import and run the mini RPG example
    from barebones_rpg.examples.mini_rpg import main as mini_rpg_main

    try:
        mini_rpg_main()
    except Exception as e:
        print(f"\nError running example: {e}")
        print("\nTo run examples manually:")
        print("  python -m barebones_rpg.examples.simple_combat_example")
        print("  python -m barebones_rpg.examples.mini_rpg")


if __name__ == "__main__":
    main()

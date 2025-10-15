#!/usr/bin/env python3
"""
Toy Compiler - Main Entry Point

This file is the main entry point for the compiler.
It uses the compiler.py file from the src/compiler/ module.
"""

import sys
import os

def main():
    """Main entry point for the toy compiler."""
    # Add src directory to Python path
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Import and run compiler main function
    try:
        # Import compiler module dynamically to avoid IDE warnings
        import compiler.compiler as compiler_module  # type: ignore
        compiler_module.main()
    except ImportError as e:
        print(f"Error: Failed to import compiler module: {e}")
        print("Please ensure all required files are in the src/compiler/ directory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
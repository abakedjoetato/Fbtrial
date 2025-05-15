"""
Check Discord Installation

This script checks the Discord library installation.
"""

import sys
import os
import importlib.util
import pkgutil

def check_module(module_name):
    """Check if a module is installed and get its location"""
    print(f"Checking for module: {module_name}")
    
    try:
        # Try to import the module
        module = __import__(module_name)
        print(f"Module {module_name} found!")
        print(f"Location: {module.__file__}")
        print(f"Version: {getattr(module, '__version__', 'Not available')}")
        print(f"Path: {module.__path__ if hasattr(module, '__path__') else 'Not a package'}")
        
        # Check if it's a package and list submodules
        if hasattr(module, '__path__'):
            print(f"\nSubmodules of {module_name}:")
            try:
                submodules = [m[1] for m in pkgutil.iter_modules(module.__path__)]
                if submodules:
                    for submodule in submodules:
                        print(f"  - {submodule}")
                else:
                    print("  No submodules found")
            except Exception as e:
                print(f"  Error listing submodules: {e}")
        
        # Check important attributes
        print(f"\nImportant attributes in {module_name}:")
        important_attrs = ['Client', 'Bot', 'ext', 'app_commands', 'ui', 'Intents']
        for attr in important_attrs:
            has_attr = hasattr(module, attr)
            print(f"  {attr}: {'✓' if has_attr else '✗'}")
            
            # If it has ext, check for commands
            if attr == 'ext' and has_attr:
                try:
                    ext = getattr(module, 'ext')
                    has_commands = hasattr(ext, 'commands')
                    print(f"    ext.commands: {'✓' if has_commands else '✗'}")
                except Exception as e:
                    print(f"    Error checking ext.commands: {e}")
        
        return True
    except ImportError as e:
        print(f"Module {module_name} not found: {e}")
        return False
    except Exception as e:
        print(f"Error checking module {module_name}: {e}")
        return False

def check_import_paths():
    """Check Python import paths"""
    print("\nPython import paths:")
    for p in sys.path:
        print(f"  {p}")
    
    # Check for site-packages
    site_packages = [p for p in sys.path if 'site-packages' in p]
    if site_packages:
        print("\nSite-packages directories:")
        for sp in site_packages:
            print(f"  {sp}")
            try:
                contents = os.listdir(sp)
                discord_related = [c for c in contents if 'discord' in c.lower() or 'py-cord' in c.lower() or 'pycord' in c.lower()]
                if discord_related:
                    print(f"    Discord-related entries: {', '.join(discord_related)}")
                else:
                    print("    No Discord-related entries found")
            except Exception as e:
                print(f"    Error listing contents: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("DISCORD LIBRARY CHECKER")
    print("=" * 60)
    
    # Check standard Discord modules
    check_module('discord')
    print("\n" + "-" * 60)
    
    # Check for py-cord specifically
    check_module('py_cord')
    print("\n" + "-" * 60)
    
    # Check import paths
    check_import_paths()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
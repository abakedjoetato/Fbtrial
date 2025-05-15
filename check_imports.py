#!/usr/bin/env python3

"""
Script to check if all required modules can be imported successfully
"""

def check_imports():
    try:
        import main
        print("✓ Successfully imported main.py")
        
        import app_enhanced
        print("✓ Successfully imported app_enhanced.py")
        
        import bot
        print("✓ Successfully imported bot.py")
        
        import discord_compat_layer
        print("✓ Successfully imported discord_compat_layer.py")
        
        print("\nAll required modules can be imported successfully!")
        return True
    except Exception as e:
        print(f"Error importing modules: {e}")
        return False

if __name__ == "__main__":
    check_imports()
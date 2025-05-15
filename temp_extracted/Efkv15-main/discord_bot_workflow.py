"""
Replit Discord Bot Workflow
This file defines a workflow that can be started by Replit.
"""

def start_workflow():
    """
    Start the Discord bot workflow
    """
    import os
    import sys
    
    # Run the main.py file
    print("Starting Discord bot through main.py...")
    from main import start_server
    
    # Start the server
    start_server()

if __name__ == "__main__":
    start_workflow()
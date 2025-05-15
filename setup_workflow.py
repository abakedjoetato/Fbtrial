"""
Setup Workflow Script

This script sets up the Replit workflow for the Discord bot.
"""

import json
import os
import sys
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_workflow_file():
    """Create or update the Replit workflow file."""
    workflow_content = {
        "globalEnv": True,
        "onBoot": [],
        "packages": [],
        "processes": [
            {
                "name": "Discord Bot",
                "cwd": "/",
                "cmd": "python main.py",
                "restartOn": {
                    "files": ["**/*.py"],
                    "startOnBoot": True
                },
                "env": {},
                "persistent": True
            }
        ]
    }
    
    # Write to file
    workflow_path = ".replit.workflow"
    with open(workflow_path, 'w') as f:
        json.dump(workflow_content, f, indent=2)
    logger.info(f"Created workflow file at {workflow_path}")
    
    return workflow_path

def create_replit_file():
    """Create or update the Replit configuration file."""
    replit_content = """
run = "python main.py"
modules = ["python-3.11:v24-20240513-322bc39"]

hidden = [".pythonlibs"]
language = "python3"

[nix]
channel = "stable-23_11"

[env]
PYTHONPATH = "${PYTHONPATH}:${REPL_HOME}"

[unitTest]
language = "python3"

[gitHubImport]
requiredFiles = [".replit", "replit.nix", ".gitignore"]

[deployment]
run = "python main.py"
deploymentTarget = "cloudrun"
"""
    
    # Write to file
    replit_path = ".replit"
    with open(replit_path, 'w') as f:
        f.write(replit_content.strip())
    logger.info(f"Created Replit configuration at {replit_path}")
    
    return replit_path

def create_run_workflow_script():
    """Create the workflow runner script."""
    script_content = '''#!/usr/bin/env python3
"""
Workflow Runner Script

This script starts the Discord bot workflow.
"""

import logging
import os
import subprocess
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    logger.info("Starting Discord bot workflow...")
    
    try:
        # Run the main Python script
        process = subprocess.Popen(
            ["python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end="")
        
        # Wait for process to complete
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"Bot process exited with code {process.returncode}")
            return process.returncode
        
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Error starting workflow: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
    
    # Write to file
    script_path = "run_workflow.py"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    os.chmod(script_path, 0o755)
    logger.info(f"Created workflow runner script at {script_path}")
    
    return script_path

def check_secret_token():
    """Check if the DISCORD_TOKEN is set in Replit secrets."""
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.warning("DISCORD_TOKEN is not set in Replit secrets.")
        logger.warning("Please add your Discord bot token to Replit secrets.")
        logger.warning("Go to 'Secrets' tab and add DISCORD_TOKEN as the key with your bot token as the value.")
        return False
    
    logger.info("DISCORD_TOKEN is set in Replit secrets.")
    return True

def main():
    """Main entry point."""
    logger.info("Setting up Replit workflow for Discord bot...")
    
    # Create workflow files
    create_workflow_file()
    create_replit_file()
    create_run_workflow_script()
    
    # Check secrets
    check_secret_token()
    
    logger.info("Workflow setup completed.")
    logger.info("You can now start the bot by pressing the 'Run' button in Replit.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
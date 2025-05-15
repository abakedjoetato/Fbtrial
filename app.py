
import os
import sys
import subprocess
import threading
import time
import logging
import signal
from flask import Flask, render_template_string

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('discord_bot_app')

# Initialize Flask app
app = Flask(__name__)

# Global variables
bot_process = None
start_time = time.time()

def start_discord_bot():
    """
    Start the Discord bot in a subprocess
    """
    global bot_process
    
    # Kill any existing process
    if bot_process and bot_process.poll() is None:
        logger.info("Stopping existing bot process...")
        os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
    
    # Start the bot process using python directly instead of a bash script
    logger.info("Starting Discord bot...")
    bot_process = subprocess.Popen(
        ["python", "bot.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
        env=dict(os.environ)  # Pass all environment variables to the subprocess
    )
    
    # Start logging thread
    threading.Thread(target=log_output, daemon=True).start()
    
    return bot_process

def log_output():
    """Function to continuously read and log output from the bot process"""
    global bot_process
    
    if not bot_process or not bot_process.stdout:
        logger.warning("Cannot log output: bot process or stdout not available")
        return
        
    for line in bot_process.stdout:
        logger.info(f"BOT: {line.strip()}")

def cleanup(signum, frame):
    """
    Cleanup function to terminate the bot process when this script is stopped
    """
    global bot_process
    
    if bot_process and bot_process.poll() is None:
        logger.info("Terminating bot process...")
        os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        bot_process = None
    
    sys.exit(0)

def get_uptime():
    """Get uptime of the bot process"""
    uptime_seconds = time.time() - start_time
    
    # Convert to days, hours, minutes, seconds
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{int(days)}d {int(hours)}h {int(minutes)}m"
    elif hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{int(seconds)}s"

def is_bot_running():
    """Check if the bot process is running"""
    global bot_process
    return bot_process is not None and bot_process.poll() is None

@app.route('/')
def index():
    """Root route to display bot status"""
    status = "Running" if is_bot_running() else "Stopped"
    color = "green" if is_bot_running() else "red"
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Status</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            .status {
                padding: 10px;
                border-radius: 5px;
                display: inline-block;
                color: white;
                font-weight: bold;
            }
            .running {
                background-color: #4CAF50;
            }
            .stopped {
                background-color: #F44336;
            }
            .container {
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
                margin-top: 20px;
            }
            h1, h2 {
                color: #333;
            }
            .info {
                margin-bottom: 10px;
            }
            .refresh {
                margin-top: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <h1>Discord Bot Dashboard</h1>
        
        <div class="container">
            <h2>Bot Status</h2>
            <div class="info">
                <strong>Status:</strong> <span class="status {{ 'running' if status == 'Running' else 'stopped' }}">{{ status }}</span>
            </div>
            <div class="info">
                <strong>Uptime:</strong> {{ uptime }}
            </div>
        </div>
        
        <div class="refresh">
            <p>This page auto-refreshes every 30 seconds</p>
            <button onclick="window.location.reload()">Refresh Now</button>
        </div>
        
        <script>
            // Auto refresh every 30 seconds
            setTimeout(function() {
                window.location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    """
    
    return render_template_string(
        template,
        status=status,
        uptime=get_uptime()
    )

def start_server():
    """
    Function for Replit to call
    """
    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Start the bot
    start_discord_bot()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    start_server()
        
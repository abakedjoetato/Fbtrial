"""
Flask App for Discord Bot

This is a simple Flask app that runs the Discord bot in a background thread,
allowing it to be managed through a web interface.
"""

import os
import sys
import threading
import time
import logging
import signal
import subprocess
import flask
from flask import Flask, render_template_string

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables
bot_process = None
start_time = time.time()

def start_bot():
    """Start the Discord bot process"""
    global bot_process
    
    # Kill any existing process
    if bot_process and bot_process.poll() is None:
        logger.info("Stopping existing bot process...")
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Error stopping bot process: {e}")
    
    # Start the bot process
    logger.info("Starting Discord bot...")
    try:
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            preexec_fn=os.setsid
        )
        
        # Start logging thread
        threading.Thread(target=log_output, daemon=True).start()
        
        return True
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        return False

def log_output():
    """Log output from the bot process"""
    global bot_process
    
    if not bot_process or not bot_process.stdout:
        logger.warning("Cannot log output: bot process or stdout not available")
        return
    
    try:
        for line in bot_process.stdout:
            if line.strip():  # Only log non-empty lines
                logger.info(f"BOT: {line.strip()}")
    except Exception as e:
        logger.error(f"Error logging output: {e}")

def cleanup(signum, frame):
    """Cleanup function to terminate the bot process"""
    global bot_process
    
    logger.info(f"Received signal {signum}, cleaning up...")
    
    if bot_process and bot_process.poll() is None:
        logger.info("Terminating bot process...")
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
        except Exception as e:
            logger.error(f"Error terminating bot process: {e}")

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
            .button {
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                margin: 5px;
            }
            .button.stop {
                background-color: #F44336;
            }
            .button.restart {
                background-color: #FF9800;
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
            <div class="actions">
                {% if status == 'Running' %}
                <a href="/stop" class="button stop">Stop Bot</a>
                <a href="/restart" class="button restart">Restart Bot</a>
                {% else %}
                <a href="/start" class="button">Start Bot</a>
                {% endif %}
            </div>
        </div>
        
        <div class="refresh">
            <p>This page auto-refreshes every 30 seconds</p>
            <button onclick="window.location.reload()" class="button">Refresh Now</button>
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

@app.route('/start')
def start_route():
    """Start the bot"""
    start_bot()
    return flask.redirect('/')

@app.route('/stop')
def stop_route():
    """Stop the bot"""
    global bot_process
    if bot_process and bot_process.poll() is None:
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
            bot_process = None
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    return flask.redirect('/')

@app.route('/restart')
def restart_route():
    """Restart the bot"""
    stop_route()
    start_bot()
    return flask.redirect('/')

def main():
    """Main entry point"""
    # Register signal handlers
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    
    # Make sure DISCORD_TOKEN is set
    if not os.getenv("DISCORD_TOKEN"):
        logger.error("DISCORD_TOKEN environment variable not set")
        logger.error("Please set the DISCORD_TOKEN in the Replit Secrets tab")
        return 1
    
    # Start the bot
    start_bot()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
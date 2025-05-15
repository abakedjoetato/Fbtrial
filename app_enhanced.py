"""
Enhanced entry point for Replit to start the Discord bot

This version includes additional compatibility fixes and error handling
for issues with py-cord 2.6.1 and different library versions.
It also provides a simple web interface to monitor the bot's status.
"""

import os
import sys
import subprocess
import time
import signal
import logging
import traceback
import threading
import datetime
from flask import Flask, render_template_string, jsonify

# Create Flask app
app = Flask(__name__)

# Set up constants
START_TIME = datetime.datetime.now()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger("app_enhanced")

# Discord bot process
bot_process = None

def start_discord_bot():
    """
    Start the Discord bot in a subprocess with improved error handling
    """
    global bot_process
    
    try:
        logger.info("Starting Discord bot with enhanced compatibility...")
        
        # Set environment variables for compatibility
        env = os.environ.copy()
        
        # Run the bot using our start.sh script
        cmd = ["bash", "start.sh"]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        bot_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            env=env,
            preexec_fn=os.setsid
        )
        
        # Create a thread to continuously read and log output
        import threading
        
        def log_output():
            """Function to continuously read and log output from the bot process"""
            startup_lines = 0
            max_startup_lines = 20
            try:
                logger.info("Bot starting - showing output...")
                # Check if stdout is valid
                if bot_process and bot_process.stdout:
                    for line in iter(bot_process.stdout.readline, ''):
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        startup_lines += 1
                        if startup_lines == max_startup_lines:
                            logger.info("Bot startup proceeding - further logs will be in bot.log")
                else:
                    logger.warning("Bot process stdout not available for logging")
            except Exception as e:
                logger.error(f"Error reading bot output: {e}")
                
        # Start the output logging thread
        output_thread = threading.Thread(target=log_output, daemon=True)
        output_thread.start()
        
        # Log a message indicating the bot is running
        logger.info("Bot startup initiated - check bot.log for details")
        
        # Don't wait for process to complete - we want it to keep running
        logger.info("Discord bot process is now running in the background")
        logger.info("Monitor the bot.log file for ongoing logs")
            
    except Exception as e:
        logger.error(f"Failed to start Discord bot process: {e}")
        logger.error(traceback.format_exc())

def cleanup(signum, frame):
    """
    Cleanup function to terminate the bot process when this script is stopped
    """
    global bot_process
    
    if bot_process:
        logger.info("Terminating Discord bot process...")
        try:
            os.killpg(os.getpgid(bot_process.pid), signal.SIGTERM)
            bot_process.wait(timeout=5)
            logger.info("Discord bot process terminated")
        except Exception as e:
            logger.error(f"Failed to terminate Discord bot process: {e}")
    
    # Exit this process
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# Web routes
@app.route('/')
def index():
    """Root route to display bot status"""
    uptime = get_uptime()
    bot_status = is_bot_running()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Status</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #36393f;
                color: #dcddde;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #2f3136;
                border-radius: 5px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }
            h1 {
                color: #ffffff;
                border-bottom: 1px solid #4e5d94;
                padding-bottom: 10px;
            }
            .status {
                display: flex;
                align-items: center;
                margin: 20px 0;
                padding: 15px;
                background-color: #36393f;
                border-radius: 5px;
            }
            .status-dot {
                width: 15px;
                height: 15px;
                border-radius: 50%;
                margin-right: 10px;
            }
            .online {
                background-color: #43b581;
            }
            .offline {
                background-color: #f04747;
            }
            .info {
                margin-bottom: 10px;
            }
            .button {
                display: inline-block;
                padding: 10px 15px;
                background-color: #7289da;
                color: white;
                border-radius: 3px;
                text-decoration: none;
                margin-top: 15px;
            }
            .button:hover {
                background-color: #677bc4;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Discord Bot Status</h1>
            
            <div class="status">
                <div class="status-dot {{ 'online' if bot_status else 'offline' }}"></div>
                <div>
                    <strong>Status:</strong> {{ 'Online' if bot_status else 'Offline' }}
                </div>
            </div>
            
            <div class="info">
                <strong>Uptime:</strong> {{ uptime }}
            </div>
            
            <div class="info">
                <strong>Started:</strong> {{ start_time }}
            </div>
            
            <div class="info">
                <strong>Version:</strong> Tower of Temptation Bot 2.0 (py-cord 2.6.1)
            </div>
            
            <a href="/restart" class="button">Restart Bot</a>
        </div>
    </body>
    </html>
    """
    
    # Replace template variables
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html = html.replace("{{ 'online' if bot_status else 'offline' }}", "online" if bot_status else "offline")
    html = html.replace("{{ 'Online' if bot_status else 'Offline' }}", "Online" if bot_status else "Offline")
    html = html.replace("{{ uptime }}", uptime)
    html = html.replace("{{ start_time }}", START_TIME.strftime("%Y-%m-%d %H:%M:%S"))
    
    return html

@app.route('/restart')
def restart_bot():
    """Restart the bot"""
    try:
        global bot_process
        
        # Check if bot is running
        if bot_process and bot_process.poll() is None:
            # Kill the bot process
            cleanup(None, None)
            time.sleep(2)  # Give it time to shut down
            
        # Start the bot again
        start_discord_bot()
        time.sleep(2)  # Give it time to start
        
        # Return to the main page
        return '<meta http-equiv="refresh" content="1;url=/">'
    except Exception as e:
        return f"Error restarting bot: {str(e)}"

@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    return jsonify({
        'status': 'online' if is_bot_running() else 'offline',
        'uptime': get_uptime(),
        'start_time': START_TIME.strftime("%Y-%m-%d %H:%M:%S"),
        'version': 'Tower of Temptation Bot 2.0 (py-cord 2.6.1)'
    })

def get_uptime():
    """Get uptime of the bot process"""
    if not bot_process:
        return "Not started"
        
    if bot_process.poll() is not None:
        return "Not running"
        
    # Calculate uptime from START_TIME
    uptime = datetime.datetime.now() - START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
    return ", ".join(parts)

def is_bot_running():
    """Check if the bot process is running"""
    return bot_process is not None and bot_process.poll() is None

def start_server():
    """
    Function for Replit to call
    """
    # Print banner
    print("=" * 60)
    print("  TOWER OF TEMPTATION DISCORD BOT (Web Interface)")
    print("  Starting Discord bot with py-cord 2.6.1 compatibility")
    print("  " + time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # Start the Discord bot in a separate thread
    bot_thread = threading.Thread(target=start_discord_bot_with_monitoring)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start the Flask app
    logger.info("Starting web interface on port 5000...")
    app.run(host='0.0.0.0', port=5000)

def start_discord_bot_with_monitoring():
    """Start the Discord bot and monitor it"""
    # Start the Discord bot
    start_discord_bot()
    
    # Keep monitoring the bot
    try:
        logger.info("Monitor thread started")
        
        # Check if bot process is still running
        iteration = 0
        while True:
            time.sleep(10)
            
            # Print a heartbeat message every minute (6 iterations)
            iteration += 1
            if iteration % 6 == 0:
                if bot_process and bot_process.poll() is None:
                    logger.info("Heartbeat: Discord bot is still running")
                else:
                    logger.warning("Heartbeat: Discord bot process has stopped!")
                    
                    # If bot process has stopped unexpectedly, restart it
                    if bot_process and bot_process.poll() is not None:
                        logger.info("Attempting to restart Discord bot process...")
                        start_discord_bot()
    except Exception as e:
        logger.error(f"Error in monitoring thread: {e}")

# Main entry point - Just start the Discord bot
if __name__ == "__main__":
    start_server()
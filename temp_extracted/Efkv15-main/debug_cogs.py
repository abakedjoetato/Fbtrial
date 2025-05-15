import asyncio
import logging
import sys
import os
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import necessary dependencies
import discord
from discord.ext import commands

# Load the environment variables
try:
    from utils.env_config import load_env_vars
    load_env_vars()
except ImportError:
    # Backup method: load from env.py module
    try:
        from env import load_env
        load_env()
    except ImportError:
        print("WARNING: Could not load environment variables from any module")
        # Load env file manually
        from dotenv import load_dotenv
        load_dotenv()

# Discord bot token
TOKEN = os.environ.get("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found in environment variables")
    sys.exit(1)

class DebugBot(commands.Bot):
    """Debug bot to test cog loading"""

    def __init__(self):
        """Initialize the bot"""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")
        
        # Load cogs
        await self.load_cogs()
        
        # Exit once cogs have been loaded (or attempted to load)
        await self.close()

    async def load_cogs(self):
        """Load all cogs"""
        cogs_dir = "cogs"
        
        if not os.path.isdir(cogs_dir):
            logger.error(f"Cogs directory '{cogs_dir}' not found")
            return
            
        # Priority cogs to load first
        priority_cogs = [
            'error_handling.py', 
            'basic_commands.py',
            'basic_fixed.py',
            'help.py',
            'admin.py',
            'database.py',
            'debug_fixed.py',
            'sftp_commands_fixed.py',
            'setup_fixed_enhanced.py'
        ]
        
        # Skip problematic cogs that might need additional setup
        skip_cogs = [
            '__init__.py',
            'basic.py',  # Original basic.py has uptime command conflict
            'debug.py',  # Original debug has import issues
            'sftp_commands_simple.py',  # Has test_sftp command conflict
            'setup.py',  # Original setup has command conflicts
        ]
        
        # Load priority cogs first
        for cog_file in priority_cogs:
            if os.path.exists(os.path.join(cogs_dir, cog_file)):
                cog_name = f"cogs.{os.path.splitext(cog_file)[0]}"
                try:
                    logger.info(f"Loading priority cog: {cog_name}")
                    await self.load_extension(cog_name)
                    logger.info(f"Successfully loaded {cog_name}")
                except Exception as e:
                    logger.error(f"Failed to load {cog_name}: {e}")
                    traceback.print_exc()
        
        # Load remaining cogs
        loaded_cogs = 0
        failed_cogs = []
        
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and filename not in priority_cogs and filename not in skip_cogs:
                cog_name = f"cogs.{os.path.splitext(filename)[0]}"
                try:
                    logger.info(f"Loading cog: {cog_name}")
                    await self.load_extension(cog_name)
                    logger.info(f"Successfully loaded {cog_name}")
                    loaded_cogs += 1
                except Exception as e:
                    logger.error(f"Failed to load {cog_name}: {e}")
                    failed_cogs.append(cog_name)
                    traceback.print_exc()
        
        logger.info(f"Successfully loaded {loaded_cogs} additional cogs")
        if failed_cogs:
            logger.warning(f"Failed to load {len(failed_cogs)} cogs: {', '.join(failed_cogs)}")

async def main():
    """Main function"""
    bot = DebugBot()
    try:
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        await bot.close()
    finally:
        logger.info("Bot has been closed")

if __name__ == "__main__":
    asyncio.run(main())

import logging
import asyncio
import sys
import traceback

# Force configure logging to stream to stdout
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

async def run_bot():
    try:
        logger.info("Importing nse_bot...")
        import nse_bot
        logger.info("nse_bot imported successfully.")
        
        # Check if main exists
        if hasattr(nse_bot, 'main'):
            logger.info("Running nse_bot.main()...")
            # If main is async, await it; if not, just call it
            if asyncio.iscoroutinefunction(nse_bot.main):
                await nse_bot.main()
            else:
                nse_bot.main()
        else:
            logger.error("nse_bot.py has no main() function!")
            
    except Exception as e:
        logger.error(f"CRASH: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting debug_bot...")
    try:
        # Check if nse_bot.py exists in current dir
        import os
        if not os.path.exists("nse_bot.py"):
            print("ERROR: nse_bot.py not found in current directory.")
            sys.exit(1)
            
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Interrupted.")
    except Exception as e:
        print(f"Top-level error: {e}")
        traceback.print_exc()

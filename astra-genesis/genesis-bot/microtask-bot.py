import requests
import json
import time
import logging
from typing import Dict, List
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('microtask-bot.log'),
        logging.StreamHandler()
    ]
)

# Configuration
class Config:
    GITCOIN_API_URL = "https://gitcoin.co/api/v0.1/bounties/?network=mainnet"
    POLL_INTERVAL = 600  # 10 minutes
    OUTPUT_FILE = "bounty-config.json"

def fetch_bounties() -> List[Dict]:
    """
    Fetch bounties from Gitcoin API with error handling and retries.
    """
    try:
        logging.info("Retrieving available bounties from Gitcoin...")
        response = requests.get(
            Config.GITCOIN_API_URL, 
            timeout=30,
            headers={'User-Agent': 'AstraLink-Bot/1.0'}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Error fetching bounties: {str(e)}")
        return []

def save_bounties(bounties: List[Dict]) -> None:
    """
    Save bounties to JSON file with error handling.
    """
    try:
        output_path = Path(Config.OUTPUT_FILE)
        with output_path.open('w') as f:
            json.dump(bounties, f, indent=4)
        logging.info(f"Saved {len(bounties)} bounties to {Config.OUTPUT_FILE}")
    except IOError as e:
        logging.error(f"Error saving bounties: {str(e)}")

async def main() -> None:
    """
    Main loop with error handling and graceful shutdown.
    """
    try:
        while True:
            bounties = fetch_bounties()
            if bounties:
                save_bounties(bounties)
            logging.info(f"Sleeping for {Config.POLL_INTERVAL/60} minutes...")
            await asyncio.sleep(Config.POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

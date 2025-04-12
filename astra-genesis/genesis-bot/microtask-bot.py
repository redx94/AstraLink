import requests
import json
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import asyncio
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('microtask-bot.log'),
        logging.StreamHandler()
    ]
)

class Config:
    GITCOIN_API_URL = "https://gitcoin.co/api/v0.1/bounties/?network=mainnet"
    JUICEBOX_API_URL = "https://rpc.juice.box/v1/projects"
    MIRROR_API_URL = "https://mirror.xyz/api/projects"
    POLL_INTERVAL = 600  # 10 minutes
    OUTPUT_FILE = "fundraising-config.json"
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 5  # seconds
    
    # Supported networks
    NETWORKS = {
        'base': 'https://mainnet.base.org',
        'ethereum': 'https://mainnet.ethereum.org'
    }

class FundraisingManager:
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(Config.NETWORKS['base']))
        
    async def fetch_opportunities(self) -> Dict[str, List[Dict]]:
        """
        Fetch fundraising opportunities from multiple platforms
        """
        opportunities = {
            'gitcoin': await self.fetch_gitcoin_bounties(),
            'juicebox': await self.fetch_juicebox_projects(),
            'mirror': await self.fetch_mirror_campaigns(),
            'nft_sales': await self.get_nft_stats()
        }
        return opportunities

    async def fetch_gitcoin_bounties(self) -> List[Dict]:
        """
        Fetch bounties from Gitcoin with retry mechanism
        """
        for attempt in range(Config.RETRY_ATTEMPTS):
            try:
                response = requests.get(
                    Config.GITCOIN_API_URL,
                    timeout=30,
                    headers={'User-Agent': 'AstraLink-Bot/1.0'}
                )
                response.raise_for_status()
                bounties = response.json()
                logging.info(f"Successfully fetched {len(bounties)} Gitcoin bounties")
                return bounties
            except requests.RequestException as e:
                if attempt == Config.RETRY_ATTEMPTS - 1:
                    logging.error(f"Failed to fetch Gitcoin bounties after {Config.RETRY_ATTEMPTS} attempts: {str(e)}")
                    return []
                await asyncio.sleep(Config.RETRY_DELAY)

    async def fetch_juicebox_projects(self) -> List[Dict]:
        """
        Fetch relevant Juicebox projects for potential fundraising
        """
        try:
            response = requests.get(Config.JUICEBOX_API_URL)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching Juicebox projects: {str(e)}")
            return []

    async def fetch_mirror_campaigns(self) -> List[Dict]:
        """
        Fetch relevant Mirror writing/fundraising campaigns
        """
        try:
            response = requests.get(Config.MIRROR_API_URL)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching Mirror campaigns: {str(e)}")
            return []

    async def get_nft_stats(self) -> Dict:
        """
        Get statistics about AstraLink NFT sales and performance
        """
        try:
            # Add NFT contract interaction here
            return {
                'total_minted': 0,
                'total_sales': 0,
                'avg_price': 0,
                'active_auctions': 0
            }
        except Exception as e:
            logging.error(f"Error fetching NFT stats: {str(e)}")
            return {}

    def save_opportunities(self, opportunities: Dict[str, List[Dict]]) -> None:
        """
        Save fundraising opportunities to JSON file
        """
        try:
            output_path = Path(Config.OUTPUT_FILE)
            with output_path.open('w') as f:
                json.dump(opportunities, f, indent=4)
            logging.info(f"Saved fundraising opportunities to {Config.OUTPUT_FILE}")
        except IOError as e:
            logging.error(f"Error saving opportunities: {str(e)}")

async def main() -> None:
    """
    Main loop with error handling and graceful shutdown
    """
    manager = FundraisingManager()
    
    try:
        while True:
            opportunities = await manager.fetch_opportunities()
            if opportunities:
                manager.save_opportunities(opportunities)
            logging.info(f"Sleeping for {Config.POLL_INTERVAL/60} minutes...")
            await asyncio.sleep(Config.POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

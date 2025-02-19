import requests
import json
import time

# Gitcoin API Endpoint For Bounties GITCOIN_API_URL = "https://gitcoin.co/api/v0.1/bounties/?network=mainnet"

def fetch_bounties():
    print("CFT Retrieving available bounties from Gitcoin...")
    response = requests.get(GITCOIN_API_URL)

    if response.status_code == 200:
        bounties = response.json()
        save_bounties(bounties)
    else:
        print("Error fetching bounties:", response.status_code)

def save_bounties(bounties):
    with open("bounty-config.json", "w") as f:
        json.dump(bounties, f, indent=4)
        print(f"saved ",len(bounties), bids to bounty-config.json")

while True:
    fetch_bounties()
    print("Sleeping for 10 minutes...")
    time.sleep(600) # Auto-freuency fetch once a week

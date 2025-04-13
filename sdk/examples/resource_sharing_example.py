# Connecting to the Decentralized Resource Sharing Contract

import requests

def connect_to_contract(sharer, amount):
    url = "https://astralink-blockchain.net/resource_contract"
    data = {"sharer": sharer, "amount": amount}
    response = requests.post(url, json=data)
    return response.json()

# Example call with shared bandwidth
response = connect_to_contract("sharer_address", 1000)
print("Contract Details", response)
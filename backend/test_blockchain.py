
import json
import os
import sys
from web3 import Web3

# Add app to path
sys.path.append(os.getcwd())

from app.utils.config import settings

def test_blockchain():
    rpc_urls = [settings.BLOCKCHAIN_RPC_URL, "http://195.35.23.26:8545"]
    
    for rpc_url in rpc_urls:
        print(f"\nTesting RPC URL: {rpc_url}")
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        try:
            if w3.is_connected():
                print(f"PASS: Connected to {rpc_url}")
                print(f"Network ID: {w3.eth.chain_id}")
                return
            else:
                print(f"FAIL: {rpc_url} unreachable.")
        except Exception as e:
            print(f"Error testing {rpc_url}: {e}")

    print("\nNo reachable blockchain nodes found.")

if __name__ == "__main__":
    test_blockchain()

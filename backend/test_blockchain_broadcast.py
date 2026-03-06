
import os
import sys
import time
import asyncio
import logging

# Add app to path
sys.path.append(os.getcwd())

from app.blockchain.reporter import BlockchainReporter

# Configure logging to see the blockchain logs
logging.basicConfig(level=logging.INFO)

async def test_broadcast():
    print("--- Live Blockchain Broadcast Test (Amoy) ---")
    reporter = BlockchainReporter()
    
    # Test alert data
    ip = "1.2.3.4"
    attack = "Test Attack - Live Amoy"
    integrity_hash = "f1e2d3c4b5a697887766554433221100"
    
    print(f"Broadcasting alert for {ip}...")
    reporter.report_alert(ip, attack, integrity_hash)
    
    # Wait for the thread pool to process
    print("Waiting 15 seconds for transaction processing...")
    await asyncio.sleep(15)
    print("Test complete. Check logs above for TX hash.")

if __name__ == "__main__":
    asyncio.run(test_broadcast())

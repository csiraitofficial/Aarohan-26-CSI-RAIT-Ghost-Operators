
import os
import sys
import time
import asyncio
import logging
from web3 import Web3

# Add app to path
sys.path.append(os.getcwd())

from app.blockchain.reporter import BlockchainReporter
from app.utils.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConsensusSim")

async def simulate_consensus():
    logger.info("--- 🛡️ NIDS Decentralized Consensus Simulation ---")
    
    if not settings.BLOCKCHAIN_PRIVATE_KEY:
        logger.error("BLOCKCHAIN_PRIVATE_KEY missing in .env")
        return

    reporter = BlockchainReporter()
    w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))
    account = w3.eth.account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
    
    # 1. Propose a Threat (Targeting a test IP)
    test_ip = "192.168.99.99"
    logger.info(f"1. Node A (This System) detects threat from {test_ip}")
    logger.info(f"   Proposing {test_ip} to Global Consensus...")
    reporter.propose_threat(test_ip, "Simulated Attack Burst")
    
    # Wait for proposal to be mined
    logger.info("Waiting 20 seconds for proposal to be mined on Amoy...")
    await asyncio.sleep(20)
    
    # 2. Mimic external nodes voting
    # Since we only have one private key, we'll use the same account to vote multiple times
    # Note: The contract prevents duplicate votes from the same address, 
    # but for simulation purposes, we just want to see the threshold logic.
    # In a real scenario, this would be 3 different nodes.
    
    # Get current proposal ID
    consensus_contract = w3.eth.contract(
        address=Web3.to_checksum_address(settings.BLOCKCHAIN_CONSENSUS_ADDRESS),
        abi=[{"inputs":[],"name":"proposalCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]
    )
    prop_id = consensus_contract.functions.proposalCount().call()
    logger.info(f"2. Proposal ID: {prop_id} created.")
    
    # 3. Check Global Block List local enforcement
    # We will wait for the admin/voters (simulated) to finalize it
    # For this simulation, we'll manually finalize it via a single vote if possible
    # or just show the 'is_globally_blocked' check.
    
    logger.info(f"3. Checking if {test_ip} is already globally blocked...")
    is_blocked = reporter.is_globally_blocked(test_ip)
    logger.info(f"   Status: {'BLOCKED' if is_blocked else 'PENDING'}")
    
    logger.info("--- Simulation Step Complete ---")
    logger.info("In a full network, other nodes would now vote 'Approve'.")
    logger.info("Once 3 votes are cast, the IP is automatically blocked by all NIDS instances.")

if __name__ == "__main__":
    asyncio.run(simulate_consensus())

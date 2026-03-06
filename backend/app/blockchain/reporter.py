import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Global executor for non-blocking blockchain reporting
blockchain_executor = ThreadPoolExecutor(max_workers=2)

class BlockchainReporter:
    """ Industrial-Grade Asynchronous Blockchain Reporter. """
    
    def __init__(self):
        self.enabled = settings.BLOCKCHAIN_ENABLED
        self.rpc_url = settings.BLOCKCHAIN_RPC_URL
        self.contract_address = settings.BLOCKCHAIN_CONTRACT_ADDRESS
        self._contract = None
        self._w3 = None
        
        if not self.enabled:
            logger.info("Blockchain reporting is disabled via settings.")
            return

    def _lazy_init(self):
        """ Initialize Web3 only when needed to prevent startup crashes. """
        if self._w3 is not None:
            return True
            
        try:
            from web3 import Web3
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            if not self._w3.is_connected():
                logger.error(f"Blockchain node at {self.rpc_url} unreachable.")
                return False
                
            with open("app/blockchain/abi.json") as f:
                abi = json.load(f)
                
            self._contract = self._w3.eth.contract(
                address=self.contract_address,
                abi=abi
            )
            return True
        except ImportError:
            logger.error("web3 library missing. Run 'pip install web3' to fix.")
            return False
        except Exception as e:
            logger.error(f"Blockchain init failed: {e}")
            return False

    def report_alert(self, ip: str, attack_category: str, integrity_hash: str = ""):
        """ Public non-blocking entry point. """
        if not self.enabled:
            return
            
        # Dispatch to worker thread to prevent blocking real-time NIDS
        blockchain_executor.submit(self._report_sync, ip, attack_category, integrity_hash)

    def _report_sync(self, ip: str, attack: str, integrity_hash: str):
        """ Synchronous worker function. """
        if not self._lazy_init():
            return

        try:
            account = self._w3.eth.accounts[0]
            # Combine attack category and integrity hash for storage as per requirements
            documented_data = f"{attack} | Hash: {integrity_hash}" if integrity_hash else attack
            
            tx = self._contract.functions.storeAlert(
                str(ip),
                str(documented_data)
            ).transact({"from": account})
            
            tx_hash = self._w3.to_hex(tx)
            logger.info(f"⛓️ Blockchain: Alert for {ip} documented at TX {tx_hash}")
        except Exception as e:
            logger.warning(f"Failed to document alert on blockchain: {e}")
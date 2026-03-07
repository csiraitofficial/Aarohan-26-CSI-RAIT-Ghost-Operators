import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Global executor for non-blocking blockchain reporting
blockchain_executor = ThreadPoolExecutor(max_workers=2)

class BlockchainReporter:
    """ Industrial-Grade Asynchronous Blockchain Reporter with Consensus support. """
    
    def __init__(self):
        self.enabled = settings.BLOCKCHAIN_ENABLED
        self.rpc_url = settings.BLOCKCHAIN_RPC_URL
        self._contract = None
        self._consensus_contract = None
        self._w3 = None
        self._lock = threading.Lock()
        
        if not self.enabled:
            logger.info("Blockchain reporting is disabled via settings.")
            return

    def _lazy_init(self):
        """ Initialize Web3 and contracts only when needed. """
        if self._w3 is not None and self._w3.is_connected():
            return True
            
        with self._lock:
            try:
                from web3 import Web3
                self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
                
                if not self._w3.is_connected():
                    logger.error(f"Blockchain node at {self.rpc_url} unreachable.")
                    return False
                
                # Global Logger Contract
                if settings.BLOCKCHAIN_CONTRACT_ADDRESS:
                    with open("app/blockchain/abi.json") as f:
                        abi = json.load(f)
                    self._contract = self._w3.eth.contract(
                        address=Web3.to_checksum_address(settings.BLOCKCHAIN_CONTRACT_ADDRESS),
                        abi=abi
                    )

                # Consensus Contract
                if hasattr(settings, 'BLOCKCHAIN_CONSENSUS_ADDRESS') and settings.BLOCKCHAIN_CONSENSUS_ADDRESS:
                    # Minimal ABI for consensus
                    CONSENSUS_ABI = [
                        {"inputs":[{"internalType":"bytes32","name":"_ipHash","type":"bytes32"},{"internalType":"string","name":"_category","type":"string"}],"name":"proposeThreat","outputs":[],"stateMutability":"nonpayable","type":"function"},
                        {"inputs":[{"internalType":"uint256","name":"_id","type":"uint256"},{"internalType":"bool","name":"_approve","type":"bool"}],"name":"vote","outputs":[],"stateMutability":"nonpayable","type":"function"},
                        {"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"globalBlockList","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}
                    ]
                    self._consensus_contract = self._w3.eth.contract(
                        address=Web3.to_checksum_address(settings.BLOCKCHAIN_CONSENSUS_ADDRESS),
                        abi=CONSENSUS_ABI
                    )

                return True
            except Exception as e:
                logger.error(f"Blockchain init failed: {e}")
                return False

    def hash_ip(self, ip: str) -> bytes:
        """ Securely hash an IP using Keccak256 for privacy on the blockchain. """
        if not self._lazy_init():
            import hashlib
            return hashlib.sha256(ip.encode()).digest() # Fallback
        return self._w3.keccak(text=ip)

    def report_alert(self, ip: str, attack_category: str, integrity_hash: str = ""):
        """ Public non-blocking entry point for the Logger. """
        if not self.enabled:
            return
        blockchain_executor.submit(self._report_sync, ip, attack_category, integrity_hash)

    def propose_threat(self, ip: str, category: str):
        """ Propose a threat to the global consensus (hashes IP first). """
        if not self.enabled or not hasattr(settings, 'BLOCKCHAIN_CONSENSUS_ADDRESS'):
            return
        ip_hash = self.hash_ip(ip)
        blockchain_executor.submit(self._propose_sync, ip_hash, category)

    def _report_sync(self, ip: str, attack: str, integrity_hash: str):
        """ Synchronous worker for the Logger contract. """
        if not self._lazy_init() or not self._contract:
            return
        try:
            documented_data = f"{attack} | Hash: {integrity_hash}" if integrity_hash else attack
            self._send_tx(self._contract.functions.storeAlert(str(ip), str(documented_data)))
        except Exception as e:
            logger.warning(f"Failed to document alert: {e}")

    def _propose_sync(self, ip_hash: bytes, category: str):
        """ Synchronous worker for the Consensus contract. """
        if not self._lazy_init() or not self._consensus_contract:
            return
        try:
            logger.info(f"🗳️ Blockchain: Proposing threat hash {ip_hash.hex()}...")
            self._send_tx(self._consensus_contract.functions.proposeThreat(ip_hash, category))
        except Exception as e:
            logger.warning(f"Failed to propose threat: {e}")

    def _send_tx(self, func_call):
        """ Helper to sign and send transactions via Private Key. """
        if settings.BLOCKCHAIN_PRIVATE_KEY:
            account = self._w3.eth.account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY)
            nonce = self._w3.eth.get_transaction_count(account.address)
            tx_data = func_call.build_transaction({
                "from": account.address,
                "nonce": nonce,
                "gasPrice": self._w3.eth.gas_price
            })
            signed_tx = self._w3.eth.account.sign_transaction(tx_data, settings.BLOCKCHAIN_PRIVATE_KEY)
            tx = self._w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        else:
            account = self._w3.eth.accounts[0]
            tx = func_call.transact({"from": account})
        
        logger.info(f"⛓️ Blockchain: Transaction sent {self._w3.to_hex(tx)}")
        return tx

    def is_globally_blocked(self, ip: str) -> bool:
        """ Check if an IP (after hashing) is blocked on the global ledger. """
        if not self.enabled or not self._lazy_init() or not self._consensus_contract:
            return False
        try:
            ip_hash = self.hash_ip(ip)
            return self._consensus_contract.functions.globalBlockList(ip_hash).call()
        except Exception:
            return False

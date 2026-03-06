"""
Blockchain Listener

Listens to blockchain events and reacts to threats
shared by other NIDS nodes.
"""

import json
import logging
import asyncio
from web3 import Web3

logger = logging.getLogger(__name__)


class BlockchainListener:

    def __init__(self, rpc_url: str, contract_address: str, abi_path: str):

        self.enabled = False

        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))

            if not self.w3.is_connected():
                logger.warning("Blockchain connection failed")
                return

            with open(abi_path) as f:
                abi = json.load(f)

            self.contract = self.w3.eth.contract(
                address=contract_address,
                abi=abi
            )

            self.enabled = True
            logger.info("Blockchain listener initialized")

        except Exception as e:
            logger.error(f"Blockchain listener init failed: {e}")

    async def listen(self):
        """Continuously listen for threat events"""

        if not self.enabled:
            return

        logger.info("Listening for blockchain threat events")

        event_filter = self.contract.events.AlertStored.create_filter(fromBlock="latest")

        while True:
            try:
                events = event_filter.get_new_entries()

                for event in events:
                    ip = event["args"]["ip"]
                    attack = event["args"]["attack"]

                    logger.warning(
                        f"⚠ Blockchain Threat Received | IP={ip} Attack={attack}"
                    )

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Blockchain listener error: {e}")
                await asyncio.sleep(5)
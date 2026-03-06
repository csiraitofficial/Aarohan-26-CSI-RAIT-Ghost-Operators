from web3 import Web3
import json


class BlockchainReporter:

    def __init__(self):

        rpc_url = "http://127.0.0.1:8545"

        contract_address = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        with open("app/blockchain/abi.json") as f:
            abi = json.load(f)

        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=abi
        )

    def report_alert(self, ip, attack):

        account = self.w3.eth.accounts[0]

        tx = self.contract.functions.storeAlert(
            ip,
            attack
        ).transact({"from": account})

        return self.w3.to_hex(tx)
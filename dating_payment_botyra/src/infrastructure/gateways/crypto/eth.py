import logging
import uuid
from typing import Any

from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.contract import AsyncContract

from src.config import settings

logger = logging.getLogger(__name__)

ERC20_ABI: list[dict[str, Any]] = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

FACTORY_ABI: list[dict[str, Any]] = [
    {
        "inputs": [{"name": "paymentId", "type": "bytes32"}],
        "name": "computeAddress",
        "outputs": [{"name": "predicted", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "paymentId", "type": "bytes32"}],
        "name": "deployAndSweep",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


def _uuid_to_bytes32(payment_id: uuid.UUID) -> bytes:
    return payment_id.bytes.rjust(32, b"\x00")


class EthUsdtGateway:
    def __init__(self) -> None:
        self._web3: AsyncWeb3 | None = None
        self._usdt: AsyncContract | None = None
        self._factory: AsyncContract | None = None

    async def start(self) -> None:
        if not settings.eth_rpc_url:
            logger.warning("ETH_RPC_URL not configured — crypto payments disabled")
            return

        self._web3 = AsyncWeb3(AsyncHTTPProvider(settings.eth_rpc_url))

        self._usdt = self._web3.eth.contract(
            address=AsyncWeb3.to_checksum_address(settings.usdt_contract_address),
            abi=ERC20_ABI,
        )

        if settings.payment_factory_address:
            self._factory = self._web3.eth.contract(
                address=AsyncWeb3.to_checksum_address(settings.payment_factory_address),
                abi=FACTORY_ABI,
            )

        chain_id = await self._web3.eth.chain_id
        logger.info("EthUsdtGateway started, chain_id=%s", chain_id)

    @property
    def is_available(self) -> bool:
        return self._web3 is not None

    def _ensure_available(self) -> None:
        if not self.is_available:
            raise RuntimeError("EthUsdtGateway is not available (ETH_RPC_URL not set)")


    async def compute_deposit_address(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        if self._factory is None:
            raise RuntimeError("PaymentFactory address not configured")

        salt = _uuid_to_bytes32(payment_id)
        address = await self._factory.functions.computeAddress(salt).call()
        return address


    async def get_usdt_balance(self, address: str) -> int:
        self._ensure_available()
        checksum = AsyncWeb3.to_checksum_address(address)
        balance = await self._usdt.functions.balanceOf(checksum).call()
        return balance

    async def has_sufficient_payment(self, address: str, expected_amount: int) -> bool:
        balance = await self.get_usdt_balance(address)
        return balance >= expected_amount


    async def deploy_and_sweep(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        if self._factory is None:
            raise RuntimeError("PaymentFactory address not configured")
        if not settings.factory_owner_private_key:
            raise RuntimeError("Factory owner private key not configured")

        salt = _uuid_to_bytes32(payment_id)
        account = self._web3.eth.account.from_key(settings.factory_owner_private_key)

        tx = await self._factory.functions.deployAndSweep(salt).build_transaction({
            "from": account.address,
            "nonce": await self._web3.eth.get_transaction_count(account.address),
            "gas": 300_000,
            "maxFeePerGas": await self._web3.eth.gas_price,
            "maxPriorityFeePerGas": self._web3.to_wei(1, "gwei"),
        })

        signed = account.sign_transaction(tx)
        tx_hash = await self._web3.eth.send_raw_transaction(signed.raw_transaction)
        logger.info(
            "deployAndSweep sent for payment %s, tx=%s",
            payment_id, tx_hash.hex(),
        )
        return tx_hash.hex()

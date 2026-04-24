import base64
import logging
import uuid
from typing import Any

import aiohttp
from tonsdk.boc import Cell, begin_cell
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import Address, to_nano

from src.config import settings

logger = logging.getLogger(__name__)


OP_DEPLOY_AND_SWEEP = 774468011
OP_DEPLOY_AND_SWEEP_TON = 3685897264
OP_SET_TREASURY = 241953983
OP_TRANSFER_OWNERSHIP = 2636691758

GETTER_COMPUTE_ADDRESS = 73495
GETTER_FACTORY_OWNER = 111611
GETTER_FACTORY_TREASURY = 95301
GETTER_USDT_MASTER = 113833

JETTON_GETTER_WALLET_DATA = "get_wallet_data"
JETTON_GETTER_WALLET_ADDRESS = "get_wallet_address"


def _uuid_to_int(payment_id: uuid.UUID) -> int:
    """Pack a UUID into a 256-bit integer for use as on-chain payment_id."""
    return int.from_bytes(payment_id.bytes.rjust(32, b"\x00"), "big")


class TonUsdtGateway:
     def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._deposit_code: Cell | None = None
        self._factory_addr: Address | None = None
        self._usdt_master: Address | None = None
        self._treasury: Address | None = None
        self._owner_mnemonic: list[str] | None = None

    async def start(self) -> None:
        if not settings.ton_payment_factory_address:
            logger.warning("TON_PAYMENT_FACTORY_ADDRESS not set — TON payments disabled")
            return

        if not settings.ton_deposit_wallet_code_boc:
            logger.warning("TON_DEPOSIT_WALLET_CODE_BOC not set — TON payments disabled")
            return

        code_bytes = base64.b64decode(settings.ton_deposit_wallet_code_boc)
        self._deposit_code = Cell.one_from_boc(code_bytes)
        self._factory_addr = Address(settings.ton_payment_factory_address)
        self._usdt_master = Address(settings.ton_usdt_master_address)
        self._treasury = Address(settings.ton_treasury_address) if settings.ton_treasury_address else None

        if settings.ton_factory_owner_mnemonic:
            self._owner_mnemonic = settings.ton_factory_owner_mnemonic.split()

        self._session = aiohttp.ClientSession(
            base_url=settings.ton_api_url,
            headers={"X-API-Key": settings.ton_api_key} if settings.ton_api_key else {},
        )
        logger.info("TonUsdtGateway started, factory=%s", self._factory_addr.to_string())

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    @property
    def is_available(self) -> bool:
        return (
            self._session is not None
            and self._deposit_code is not None
            and self._factory_addr is not None
        )

    def _ensure_available(self) -> None:
        if not self.is_available:
            raise RuntimeError("TonUsdtGateway is not available (check TON_* settings)")

    def _build_deposit_data(self, payment_id: uuid.UUID) -> Cell:
        assert self._factory_addr is not None
        return (
            begin_cell()
            .store_bit(0)
            .store_address(self._factory_addr)
            .store_int(_uuid_to_int(payment_id), 257)
            .end_cell()
        )

    def _build_state_init(self, code: Cell, data: Cell) -> Cell:
        return (
            begin_cell()
            .store_bit(0) 
            .store_bit(0) 
            .store_bit(1).store_ref(code)
            .store_bit(1).store_ref(data)
            .store_bit(0)  
            .end_cell()
        )

    def compute_deposit_address(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        assert self._deposit_code is not None
        data = self._build_deposit_data(payment_id)
        state_init = self._build_state_init(self._deposit_code, data)
        addr_hash = state_init.bytes_hash()
        return Address(f"0:{addr_hash.hex()}").to_string(
            is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=False
        )

    async def _run_get_method(
        self, address: str, method: str | int, stack: list[Any] | None = None
    ) -> dict[str, Any]:
        assert self._session is not None
        payload = {
            "address": address,
            "method": method,
            "stack": stack or [],
        }
        async with self._session.post("/runGetMethod", json=payload) as resp:
            data = await resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"runGetMethod({method}) failed: {data}")
        return data["result"]

    async def _get_jetton_wallet_for(self, owner: Address) -> str:
        assert self._usdt_master is not None
        owner_cell = begin_cell().store_address(owner).end_cell()
        owner_boc = base64.b64encode(owner_cell.to_boc(False)).decode()
        result = await self._run_get_method(
            self._usdt_master.to_string(True, True, True),
            JETTON_GETTER_WALLET_ADDRESS,
            stack=[["tvm.Slice", owner_boc]],
        )
        slice_boc = base64.b64decode(result["stack"][0][1]["bytes"])
        cell = Cell.one_from_boc(slice_boc)
        return cell.begin_parse().read_msg_addr().to_string(True, True, True)

    async def get_usdt_balance(self, address: str) -> int:
        self._ensure_available()
        jetton_wallet = await self._get_jetton_wallet_for(Address(address))
        try:
            result = await self._run_get_method(jetton_wallet, JETTON_GETTER_WALLET_DATA)
        except RuntimeError:
            return 0
        return int(result["stack"][0][1], 16)

    async def has_sufficient_payment(self, address: str, expected_amount: int) -> bool:
        balance = await self.get_usdt_balance(address)
        return balance >= expected_amount

    def _build_deploy_and_sweep_body(
        self, payment_id: uuid.UUID, jetton_wallet: Address, amount: int
    ) -> Cell:
        return (
            begin_cell()
            .store_uint(OP_DEPLOY_AND_SWEEP, 32)
            .store_uint(_uuid_to_int(payment_id), 256)
            .store_address(jetton_wallet)
            .store_coins(amount)
            .end_cell()
        )

    async def deploy_and_sweep(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        if self._owner_mnemonic is None:
            raise RuntimeError("Factory owner mnemonic not configured")
        assert self._factory_addr is not None
        assert self._session is not None

        deposit_addr_str = self.compute_deposit_address(payment_id)
        deposit_jetton = await self._get_jetton_wallet_for(Address(deposit_addr_str))
        amount = await self.get_usdt_balance(deposit_addr_str)
        if amount == 0:
            raise RuntimeError(f"no USDT at {deposit_addr_str} to sweep")

        body = self._build_deploy_and_sweep_body(
            payment_id, Address(deposit_jetton), amount
        )

        _, _pub, _priv, owner_wallet = Wallets.from_mnemonics(
            self._owner_mnemonic, WalletVersionEnum.v4r2, 0
        )

        seqno = await self._get_wallet_seqno(owner_wallet.address)
        query = owner_wallet.create_transfer_message(
            to_addr=self._factory_addr.to_string(True, True, True),
            amount=to_nano(0.2, "ton"),
            seqno=seqno,
            payload=body,
            send_mode=3,  
        )

        boc = base64.b64encode(query["message"].to_boc(False)).decode()
        async with self._session.post("/sendBoc", json={"boc": boc}) as resp:
            data = await resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"sendBoc failed: {data}")

        tx_id = query["message"].bytes_hash().hex()
        logger.info("TON deployAndSweep sent for payment %s, ext_hash=%s", payment_id, tx_id)
        return tx_id

    async def _get_wallet_seqno(self, wallet_address: Address) -> int:
        try:
            result = await self._run_get_method(
                wallet_address.to_string(True, True, True), "seqno"
            )
            return int(result["stack"][0][1], 16)
        except RuntimeError:
            return 0

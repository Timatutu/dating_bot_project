import json
import logging
import uuid
from pathlib import Path

from solana.rpc.core import RPCException
from solana.rpc.async_api import AsyncClient
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction

from src.config import settings

logger = logging.getLogger(__name__)

TOKEN_PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string(
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
)
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
FACTORY_SEED = b"factory"
DEPOSIT_SEED = b"deposit"
SWEEP_DISCRIMINATOR = bytes([40, 23, 234, 175, 14, 61, 154, 177])


def _uuid_to_bytes32(payment_id: uuid.UUID) -> bytes:
    return payment_id.bytes.rjust(32, b"\x00")


def _ata_address(owner: Pubkey, mint: Pubkey) -> Pubkey:
    ata, _ = Pubkey.find_program_address(
        [bytes(owner), bytes(TOKEN_PROGRAM_ID), bytes(mint)],
        ASSOCIATED_TOKEN_PROGRAM_ID,
    )
    return ata


class SolUsdtGateway:
    def __init__(self) -> None:
        self._client: AsyncClient | None = None
        self._program_id: Pubkey | None = None
        self._usdc_mint: Pubkey | None = None
        self._treasury: Pubkey | None = None
        self._owner: Keypair | None = None

    async def start(self) -> None:
        if (
            not settings.solana_program_id
            or not settings.solana_usdc_mint
            or not settings.solana_treasury_address
            or not settings.solana_owner_keypair_path
        ):
            logger.warning("Solana gateway is not fully configured")
            return

        self._program_id = Pubkey.from_string(settings.solana_program_id)
        self._usdc_mint = Pubkey.from_string(settings.solana_usdc_mint)
        self._treasury = Pubkey.from_string(settings.solana_treasury_address)
        keypair_path = Path(settings.solana_owner_keypair_path)
        if not keypair_path.exists():
            logger.warning(
                "Solana keypair file not found: %s (gateway disabled)",
                keypair_path,
            )
            return

        try:
            keypair_bytes = json.loads(keypair_path.read_text(encoding="utf-8"))
            self._owner = Keypair.from_bytes(bytes(keypair_bytes))
        except Exception as exc:  
            logger.warning("Invalid Solana keypair file %s: %s", keypair_path, exc)
            return

        self._client = AsyncClient(settings.solana_rpc_url, commitment="confirmed")
        logger.info("SolUsdtGateway started: rpc=%s", settings.solana_rpc_url)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None and self._program_id is not None

    def _ensure_available(self) -> None:
        if not self.is_available:
            raise RuntimeError("SolUsdtGateway is not configured")

    def _factory_pda(self) -> Pubkey:
        assert self._program_id is not None
        pda, _ = Pubkey.find_program_address([FACTORY_SEED], self._program_id)
        return pda

    def _deposit_pda(self, payment_id: uuid.UUID) -> Pubkey:
        assert self._program_id is not None
        payment_bytes32 = _uuid_to_bytes32(payment_id)
        pda, _ = Pubkey.find_program_address(
            [DEPOSIT_SEED, payment_bytes32],
            self._program_id,
        )
        return pda

    async def derive_deposit_address(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        deposit_pda = self._deposit_pda(payment_id)
        return str(deposit_pda)

    async def check_balance(self, payment_id: uuid.UUID) -> int:
        self._ensure_available()
        assert self._client is not None
        assert self._usdc_mint is not None
        deposit_pda = Pubkey.from_string(await self.derive_deposit_address(payment_id))
        deposit_ata = _ata_address(deposit_pda, self._usdc_mint)
        try:
            resp = await self._client.get_token_account_balance(deposit_ata)
        except RPCException as exc:
            if "could not find account" in str(exc).lower():
                return 0
            raise
        value = resp.value
        if value is None:
            return 0
        return int(value.amount)

    async def has_sufficient_payment(self, payment_id: uuid.UUID, expected_amount: int) -> bool:
        balance = await self.check_balance(payment_id)
        return balance >= expected_amount

    async def sweep(self, payment_id: uuid.UUID) -> str:
        self._ensure_available()
        assert self._client is not None
        assert self._program_id is not None
        assert self._usdc_mint is not None
        assert self._treasury is not None
        assert self._owner is not None

        payment_bytes32 = _uuid_to_bytes32(payment_id)
        factory_pda = self._factory_pda()
        deposit_pda = self._deposit_pda(payment_id)
        deposit_ata = _ata_address(deposit_pda, self._usdc_mint)
        treasury_ata = _ata_address(self._treasury, self._usdc_mint)
        ix_data = SWEEP_DISCRIMINATOR + payment_bytes32
        accounts = [
            AccountMeta(factory_pda, False, False),
            AccountMeta(self._owner.pubkey(), True, True),
            AccountMeta(deposit_pda, False, False),
            AccountMeta(deposit_ata, False, True),
            AccountMeta(self._treasury, False, False),
            AccountMeta(self._usdc_mint, False, False),
            AccountMeta(treasury_ata, False, True),
            AccountMeta(TOKEN_PROGRAM_ID, False, False),
            AccountMeta(ASSOCIATED_TOKEN_PROGRAM_ID, False, False),
            AccountMeta(SYSTEM_PROGRAM_ID, False, False),
        ]
        instruction = Instruction(self._program_id, ix_data, accounts)

        latest = await self._client.get_latest_blockhash()
        blockhash: Hash = latest.value.blockhash
        message = Message.new_with_blockhash(
            [instruction], self._owner.pubkey(), blockhash
        )
        tx = Transaction.new_unsigned(message)
        tx.sign([self._owner], blockhash)
        sig = await self._client.send_raw_transaction(bytes(tx))
        tx_hash = str(sig.value)
        logger.info("solana sweep sent for payment %s tx=%s", payment_id, tx_hash)
        return tx_hash

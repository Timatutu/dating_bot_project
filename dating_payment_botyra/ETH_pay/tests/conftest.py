import sys
from pathlib import Path

import pytest
from eth_utils import keccak

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.deploy import blueprint_initcode  # noqa: E402


@pytest.fixture
def deployer(accounts):
    return accounts[0]


@pytest.fixture
def treasury(accounts):
    return accounts[1]


@pytest.fixture
def user(accounts):
    return accounts[2]


@pytest.fixture
def stranger(accounts):
    return accounts[3]


@pytest.fixture
def usdt(project, deployer):
    return project.MockUSDT.deploy(sender=deployer)


@pytest.fixture
def deposit_initcode(project) -> bytes:
    # The full deployment bytecode (constructor + runtime + immutable slots).
    # This is exactly what create_from_blueprint will pass to CREATE2 when
    # code_offset=3 strips the 0xFE7100 preamble from the blueprint.
    return bytes.fromhex(
        project.DepositWallet.contract_type.deployment_bytecode.bytecode.removeprefix("0x")
    )


@pytest.fixture
def initcode_hash(deposit_initcode) -> bytes:
    return keccak(deposit_initcode)


@pytest.fixture
def blueprint(chain, deployer, deposit_initcode):
    initcode = blueprint_initcode(deposit_initcode)
    txn = chain.provider.network.ecosystem.create_transaction(
        sender=deployer.address,
        receiver=None,
        data=initcode,
        value=0,
    )
    receipt = deployer.call(txn)
    assert receipt.contract_address is not None, "blueprint deploy returned no address"
    return receipt.contract_address


@pytest.fixture
def factory(project, deployer, treasury, blueprint, usdt, initcode_hash):
    return project.PaymentFactory.deploy(
        treasury,
        blueprint,
        usdt,
        initcode_hash,
        sender=deployer,
    )


@pytest.fixture
def make_salt():
    counter = {"n": 0}

    def _make() -> bytes:
        counter["n"] += 1
        return counter["n"].to_bytes(32, "big")

    return _make

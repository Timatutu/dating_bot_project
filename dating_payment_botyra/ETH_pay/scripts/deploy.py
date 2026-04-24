import os

from ape import accounts, chain, project
from eth_utils import keccak


EIP5202_PREAMBLE = bytes.fromhex("fe7100")


def blueprint_initcode(runtime_bytecode: bytes) -> bytes:
    stored = EIP5202_PREAMBLE + runtime_bytecode
    length = len(stored)
    assert length < 2**16, "runtime too large for uint16 length"

    deployer = (
        b"\x61" + length.to_bytes(2, "big")  
        + b"\x60\x0e"                        
        + b"\x60\x00"                         
        + b"\x39"                          
        + b"\x61" + length.to_bytes(2, "big") 
        + b"\x60\x00"                         
        + b"\xf3"                             
    )
    assert len(deployer) == 14
    return deployer + stored


def main():
    deployer = accounts.test_accounts[0] if _is_local() else accounts.load("deployer")
    treasury = os.environ.get("TREASURY_ADDRESS") or deployer.address

    usdt_addr = os.environ.get("USDT_ADDRESS")
    if not usdt_addr:
        print("USDT_ADDRESS not set — deploying MockUSDT")
        mock = project.MockUSDT.deploy(sender=deployer)
        usdt_addr = mock.address
        print(f"  MockUSDT: {mock.address}")

    deposit_initcode = bytes.fromhex(
        project.DepositWallet.contract_type.deployment_bytecode.bytecode.removeprefix("0x")
    )
    blueprint_init = blueprint_initcode(deposit_initcode)

    txn = chain.provider.network.ecosystem.create_transaction(
        sender=deployer.address,
        receiver=None,
        data=blueprint_init,
        value=0,
    )
    receipt = deployer.call(txn)
    blueprint_addr = receipt.contract_address
    assert blueprint_addr is not None, "blueprint deployment did not return an address"
    print(f"  DepositWallet blueprint: {blueprint_addr}")
    initcode_hash = keccak(deposit_initcode)
    print(f"  initcode_hash: 0x{initcode_hash.hex()}")

    factory = project.PaymentFactory.deploy(
        treasury,
        blueprint_addr,
        usdt_addr,
        initcode_hash,
        sender=deployer,
    )
    print(f"  PaymentFactory: {factory.address}")
    print(f"  treasury: {treasury}")
    print(f"  usdt: {usdt_addr}")

    return {
        "factory": factory.address,
        "blueprint": blueprint_addr,
        "usdt": usdt_addr,
        "treasury": treasury,
        "initcode_hash": "0x" + initcode_hash.hex(),
    }


def _is_local() -> bool:
    from ape import networks
    return networks.provider.network.name in {"local", "development", "foundry"}

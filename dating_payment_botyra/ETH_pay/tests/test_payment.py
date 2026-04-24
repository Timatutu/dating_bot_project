import ape
import pytest
from eth_utils import keccak, to_checksum_address


def _create2_address(deployer: str, salt: bytes, initcode_hash: bytes) -> str:
    digest = keccak(
        b"\xff"
        + bytes.fromhex(deployer.removeprefix("0x"))
        + salt
        + initcode_hash
    )
    return to_checksum_address(digest[12:])


def test_immutables_set(factory, treasury, blueprint, usdt, initcode_hash):
    assert factory.treasury() == treasury.address
    assert factory.blueprint() == blueprint
    assert factory.usdt() == usdt.address
    assert bytes(factory.initcode_hash()) == initcode_hash


def test_compute_address_matches_offchain(factory, initcode_hash, make_salt):
    salt = make_salt()
    on_chain = factory.computeAddress(salt)
    off_chain = _create2_address(factory.address, salt, initcode_hash)
    assert on_chain == off_chain


def test_compute_address_is_deterministic(factory, make_salt):
    salt = make_salt()
    assert factory.computeAddress(salt) == factory.computeAddress(salt)


def test_deploy_creates_wallet_at_predicted_address(factory, deployer, make_salt):
    salt = make_salt()
    predicted = factory.computeAddress(salt)
    tx = factory.deploy(salt, sender=deployer)
    # Wallet now has code.
    code = ape.chain.provider.get_code(predicted)
    assert len(bytes(code)) > 0
    # Event was emitted.
    events = list(tx.decode_logs(factory.WalletDeployed))
    assert len(events) == 1
    assert events[0].wallet == predicted


def test_deploy_is_idempotent(factory, deployer, make_salt):
    salt = make_salt()
    factory.deploy(salt, sender=deployer)
    # Second deploy must not revert and must not emit WalletDeployed again.
    tx = factory.deploy(salt, sender=deployer)
    events = list(tx.decode_logs(factory.WalletDeployed))
    assert events == []


def test_only_owner_can_deploy(factory, stranger, make_salt):
    with ape.reverts("OnlyOwner"):
        factory.deploy(make_salt(), sender=stranger)


def test_only_owner_can_sweep(factory, stranger, make_salt):
    with ape.reverts("OnlyOwner"):
        factory.sweep(make_salt(), "0x0000000000000000000000000000000000000000", sender=stranger)


def test_sweep_eth_to_treasury(factory, deployer, treasury, user, make_salt):
    salt = make_salt()
    wallet = factory.computeAddress(salt)

    # Fund the (yet-undeployed) wallet with ETH; CREATE2 lets value sit at the
    # predicted address before code is deployed.
    user.transfer(wallet, "1 ether")
    treasury_before = treasury.balance

    tx = factory.sweep(salt, "0x0000000000000000000000000000000000000000", sender=deployer)

    assert ape.chain.provider.get_balance(wallet) == 0
    assert treasury.balance == treasury_before + 10**18

    swept = list(tx.decode_logs(factory.Swept))
    assert len(swept) == 1
    assert swept[0].amount == 10**18


def test_sweep_usdt_to_treasury(factory, deployer, treasury, usdt, make_salt):
    salt = make_salt()
    wallet = factory.computeAddress(salt)

    usdt.mint(wallet, 1_000_000, sender=deployer)
    assert usdt.balanceOf(wallet) == 1_000_000

    tx = factory.sweep(salt, usdt.address, sender=deployer)

    assert usdt.balanceOf(wallet) == 0
    assert usdt.balanceOf(treasury.address) == 1_000_000

    swept = list(tx.decode_logs(factory.Swept))
    assert len(swept) == 1
    assert swept[0].amount == 1_000_000


def test_deploy_and_sweep_uses_configured_usdt(factory, deployer, treasury, usdt, make_salt):
    salt = make_salt()
    wallet = factory.computeAddress(salt)

    usdt.mint(wallet, 5_000_000, sender=deployer)

    tx = factory.deployAndSweep(salt, sender=deployer)

    assert usdt.balanceOf(wallet) == 0
    assert usdt.balanceOf(treasury.address) == 5_000_000

    swept = list(tx.decode_logs(factory.Swept))
    assert len(swept) == 1
    assert swept[0].token == usdt.address
    assert swept[0].amount == 5_000_000


def test_sweep_zero_balance_does_not_revert(factory, deployer, usdt, make_salt):
    salt = make_salt()
    tx = factory.sweep(salt, usdt.address, sender=deployer)
    swept = list(tx.decode_logs(factory.Swept))
    assert len(swept) == 1
    assert swept[0].amount == 0


def test_set_treasury(factory, deployer, accounts):
    new_treasury = accounts[5]
    tx = factory.setTreasury(new_treasury, sender=deployer)
    assert factory.treasury() == new_treasury.address

    changed = list(tx.decode_logs(factory.TreasuryChanged))
    assert len(changed) == 1
    assert changed[0].current == new_treasury.address


def test_set_treasury_rejects_zero(factory, deployer):
    with ape.reverts("ZeroAddress"):
        factory.setTreasury("0x0000000000000000000000000000000000000000", sender=deployer)


def test_set_treasury_only_owner(factory, stranger, accounts):
    with ape.reverts("OnlyOwner"):
        factory.setTreasury(accounts[5], sender=stranger)


def test_transfer_ownership(factory, deployer, stranger, accounts):
    new_owner = accounts[6]
    tx = factory.transferOwnership(new_owner, sender=deployer)
    assert factory.owner() == new_owner.address

    transferred = list(tx.decode_logs(factory.OwnershipTransferred))
    assert len(transferred) == 1
    assert transferred[0].current == new_owner.address

    with ape.reverts("OnlyOwner"):
        factory.setTreasury(stranger, sender=deployer)


def test_transfer_ownership_only_owner(factory, stranger, accounts):
    with ape.reverts("OnlyOwner"):
        factory.transferOwnership(accounts[6], sender=stranger)

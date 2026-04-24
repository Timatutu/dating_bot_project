# @version 0.3.10
# SPDX-License-Identifier: MIT
from vyper.interfaces import ERC20


interface IDepositWallet:
    def sweep(token: address, to: address): nonpayable


event WalletDeployed:
    salt: indexed(bytes32)
    wallet: address

event Swept:
    salt: indexed(bytes32)
    token: indexed(address)
    amount: uint256

event TreasuryChanged:
    previous: indexed(address)
    current: indexed(address)

event OwnershipTransferred:
    previous: indexed(address)
    current: indexed(address)


owner: public(address)
treasury: public(address)
blueprint: public(immutable(address))
usdt: public(immutable(address))
initcode_hash: public(immutable(bytes32))


@external
def __init__(
    _treasury: address,
    _blueprint: address,
    _usdt: address,
    _initcode_hash: bytes32,
):
    assert _treasury != empty(address), "ZeroAddress"
    assert _blueprint != empty(address), "ZeroAddress"
    assert _usdt != empty(address), "ZeroAddress"
    self.owner = msg.sender
    self.treasury = _treasury
    blueprint = _blueprint
    usdt = _usdt
    initcode_hash = _initcode_hash


@internal
def _only_owner():
    assert msg.sender == self.owner, "OnlyOwner"


@internal
@view
def _compute_address(salt: bytes32) -> address:
    digest: bytes32 = keccak256(
        concat(
            b"\xff",
            convert(self, bytes20),
            salt,
            initcode_hash,
        )
    )
    return convert(
        convert(digest, uint256) & convert(max_value(uint160), uint256),
        address,
    )


@external
@view
def computeAddress(salt: bytes32) -> address:
    return self._compute_address(salt)


@internal
def _deploy_if_needed(salt: bytes32) -> address:
    expected: address = self._compute_address(salt)
    if not expected.is_contract:
        deployed: address = create_from_blueprint(blueprint, salt=salt, code_offset=3)
        assert deployed == expected, "AddressMismatch"
        log WalletDeployed(salt, deployed)
    return expected


@external
def deploy(salt: bytes32) -> address:
    self._only_owner()
    return self._deploy_if_needed(salt)


@external
def sweep(salt: bytes32, token: address) -> uint256:
    self._only_owner()
    wallet: address = self._deploy_if_needed(salt)

    amount: uint256 = 0
    if token == empty(address):
        amount = wallet.balance
    else:
        amount = ERC20(token).balanceOf(wallet)

    IDepositWallet(wallet).sweep(token, self.treasury)
    log Swept(salt, token, amount)
    return amount


@external
def deployAndSweep(salt: bytes32) -> uint256:
    self._only_owner()
    wallet: address = self._deploy_if_needed(salt)

    amount: uint256 = ERC20(usdt).balanceOf(wallet)
    IDepositWallet(wallet).sweep(usdt, self.treasury)
    log Swept(salt, usdt, amount)
    return amount


@external
def setTreasury(new_treasury: address):
    self._only_owner()
    assert new_treasury != empty(address), "ZeroAddress"
    log TreasuryChanged(self.treasury, new_treasury)
    self.treasury = new_treasury


@external
def transferOwnership(new_owner: address):
    self._only_owner()
    assert new_owner != empty(address), "ZeroAddress"
    log OwnershipTransferred(self.owner, new_owner)
    self.owner = new_owner

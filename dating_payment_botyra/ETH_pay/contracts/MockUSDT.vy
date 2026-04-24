# @version 0.3.10
# SPDX-License-Identifier: MIT

balances: HashMap[address, uint256]
allowances: HashMap[address, HashMap[address, uint256]]
total_supply: public(uint256)
name: public(String[32])
symbol: public(String[8])
decimals: public(uint8)


event Transfer:
    sender: indexed(address)
    receiver: indexed(address)
    value: uint256

event Approval:
    owner: indexed(address)
    spender: indexed(address)
    value: uint256


@external
def __init__():
    self.name = "Mock USDT"
    self.symbol = "mUSDT"
    self.decimals = 6


@external
@view
def balanceOf(account: address) -> uint256:
    return self.balances[account]


@external
@view
def allowance(owner: address, spender: address) -> uint256:
    return self.allowances[owner][spender]


@external
def transfer(to: address, amount: uint256) -> bool:
    assert self.balances[msg.sender] >= amount, "InsufficientBalance"
    self.balances[msg.sender] -= amount
    self.balances[to] += amount
    log Transfer(msg.sender, to, amount)
    return True


@external
def approve(spender: address, amount: uint256) -> bool:
    self.allowances[msg.sender][spender] = amount
    log Approval(msg.sender, spender, amount)
    return True


@external
def transferFrom(sender: address, to: address, amount: uint256) -> bool:
    assert self.balances[sender] >= amount, "InsufficientBalance"
    assert self.allowances[sender][msg.sender] >= amount, "InsufficientAllowance"
    self.balances[sender] -= amount
    self.allowances[sender][msg.sender] -= amount
    self.balances[to] += amount
    log Transfer(sender, to, amount)
    return True


@external
def mint(to: address, amount: uint256):
    self.balances[to] += amount
    self.total_supply += amount
    log Transfer(empty(address), to, amount)

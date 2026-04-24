# @version 0.3.10
# SPDX-License-Identifier: MIT

from vyper.interfaces import ERC20

factory: public(immutable(address))


@external
def __init__():
    factory = msg.sender


@external
@payable
def __default__():
    pass


@external
def sweep(token: address, to: address):
    assert msg.sender == factory, "OnlyFactory"

    if token == empty(address):
        bal: uint256 = self.balance
        if bal == 0:
            return
        raw_call(to, b"", value=bal)
    else:
        bal: uint256 = ERC20(token).balanceOf(self)
        if bal == 0:
            return
        assert ERC20(token).transfer(
            to, bal, default_return_value=True
        ), "TransferFailed"

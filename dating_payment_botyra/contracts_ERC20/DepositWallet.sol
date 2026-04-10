pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract DepositWallet {
    address public immutable factory;
    address public immutable treasury;

    constructor(address _treasury) {
        factory = msg.sender;
        treasury = _treasury;
    }

    function sweep(address token) external {
        require(msg.sender == factory, "only factory");
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).transfer(treasury, balance);
        }
    }

    receive() external payable {}
}

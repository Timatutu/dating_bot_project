pragma solidity ^0.8.24;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./DepositWallet.sol";

contract PaymentFactory is Ownable {
    address public treasury;
    address public usdtToken;

    mapping(bytes32 => address) public wallets;

    event WalletCreated(bytes32 indexed paymentId, address wallet);
    event Swept(bytes32 indexed paymentId, address wallet, uint256 amount);

    constructor(
        address _treasury,
        address _usdtToken
    ) Ownable(msg.sender) {
        treasury = _treasury;
        usdtToken = _usdtToken;
    }

    function computeAddress(bytes32 paymentId) public view returns (address predicted) {
        bytes memory bytecode = abi.encodePacked(
            type(DepositWallet).creationCode,
            abi.encode(treasury)
        );
        bytes32 hash = keccak256(
            abi.encodePacked(
                bytes1(0xff),
                address(this),
                paymentId,         
                keccak256(bytecode)
            )
        );
        return address(uint160(uint256(hash)));
    }


    function deployAndSweep(bytes32 paymentId) external onlyOwner {
        require(wallets[paymentId] == address(0), "already deployed");

        DepositWallet wallet = new DepositWallet{salt: paymentId}(treasury);
        address walletAddr = address(wallet);
        wallets[paymentId] = walletAddr;

        emit WalletCreated(paymentId, walletAddr);

        uint256 balance = IERC20(usdtToken).balanceOf(walletAddr);
        if (balance > 0) {
            wallet.sweep(usdtToken);
            emit Swept(paymentId, walletAddr, balance);
        }
    }


    function setTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }

    function setUsdtToken(address _usdtToken) external onlyOwner {
        usdtToken = _usdtToken;
    }

    function sweepExisting(bytes32 paymentId) external onlyOwner {
        address walletAddr = wallets[paymentId];
        require(walletAddr != address(0), "wallet not deployed");
        DepositWallet(payable(walletAddr)).sweep(usdtToken);
    }
}

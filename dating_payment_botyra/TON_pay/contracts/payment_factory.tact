import "@stdlib/deploy";
import "./deposit_wallet";

message DeployAndSweep {
    payment_id: Int as uint256;
    jetton_wallet: Address;
    amount: Int as coins;
}

message DeployAndSweepTon {
    payment_id: Int as uint256;
}

message SetTreasury {
    new_treasury: Address;
}

message TransferOwnership {
    new_owner: Address;
}

contract PaymentFactory with Deployable {
    owner: Address;
    treasury: Address;
    usdt_master: Address;

    init(owner: Address, treasury: Address, usdt_master: Address) {
        self.owner = owner;
        self.treasury = treasury;
        self.usdt_master = usdt_master;
    }

    get fun computeAddress(payment_id: Int): Address {
        return contractAddress(
            initOf DepositWallet(myAddress(), payment_id)
        );
    }

    get fun factoryOwner(): Address { return self.owner; }
    get fun factoryTreasury(): Address { return self.treasury; }
    get fun usdtMaster(): Address { return self.usdt_master; }

    receive(msg: DeployAndSweep) {
        require(sender() == self.owner, "OnlyOwner");

        let init: StateInit = initOf DepositWallet(myAddress(), msg.payment_id);
        let wallet: Address = contractAddress(init);

        send(SendParameters{
            to: wallet,
            value: 0,
            mode: SendRemainingValue,
            bounce: false,
            code: init.code,
            data: init.data,
            body: Sweep{
                jetton_wallet: msg.jetton_wallet,
                to: self.treasury,
                amount: msg.amount
            }.toCell()
        });
    }

    receive(msg: DeployAndSweepTon) {
        require(sender() == self.owner, "OnlyOwner");

        let init: StateInit = initOf DepositWallet(myAddress(), msg.payment_id);
        let wallet: Address = contractAddress(init);

        send(SendParameters{
            to: wallet,
            value: 0,
            mode: SendRemainingValue,
            bounce: false,
            code: init.code,
            data: init.data,
            body: SweepTon{to: self.treasury}.toCell()
        });
    }

    receive(msg: SetTreasury) {
        require(sender() == self.owner, "OnlyOwner");
        self.treasury = msg.new_treasury;
    }

    receive(msg: TransferOwnership) {
        require(sender() == self.owner, "OnlyOwner");
        self.owner = msg.new_owner;
    }
}

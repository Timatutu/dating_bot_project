import "@stdlib/deploy";

message(0x0f8a7ea5) JettonTransfer {
    query_id: Int as uint64;
    amount: Int as coins;
    destination: Address;
    response_destination: Address?;
    custom_payload: Cell?;
    forward_ton_amount: Int as coins;
    forward_payload: Slice as remaining;
}

message Sweep {
    jetton_wallet: Address;
    to: Address;
    amount: Int as coins;
}

message SweepTon {
    to: Address;
}

contract DepositWallet with Deployable {
    factory: Address;
    payment_id: Int as uint256;

    init(factory: Address, payment_id: Int) {
        self.factory = factory;
        self.payment_id = payment_id;
    }

    receive() {}

    receive(msg: Sweep) {
        require(sender() == self.factory, "OnlyFactory");

        send(SendParameters{
            to: msg.jetton_wallet,
            value: 0,
            mode: SendRemainingValue,
            bounce: false,
            body: JettonTransfer{
                query_id: self.payment_id,
                amount: msg.amount,
                destination: msg.to,
                response_destination: self.factory,
                custom_payload: null,
                forward_ton_amount: 0,
                forward_payload: emptySlice()
            }.toCell()
        });
    }

    receive(msg: SweepTon) {
        require(sender() == self.factory, "OnlyFactory");

        send(SendParameters{
            to: msg.to,
            value: 0,
            mode: SendRemainingBalance + SendIgnoreErrors,
            bounce: false,
            body: emptyCell()
        });
    }

    get fun factoryAddress(): Address {
        return self.factory;
    }

    get fun paymentId(): Int {
        return self.payment_id;
    }
}

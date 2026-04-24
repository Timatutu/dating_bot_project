import { Blockchain, SandboxContract, TreasuryContract } from "@ton/sandbox";
import { Address, beginCell, Cell, toNano } from "@ton/core";
import "@ton/test-utils";

import { PaymentFactory } from "../build/PaymentFactory/PaymentFactory_PaymentFactory";
import { DepositWallet } from "../build/DepositWallet/DepositWallet_DepositWallet";

// Minimal mock Jetton wallet that accepts JettonTransfer and forwards to dest.
// For sandbox tests we don't spin up a real Jetton master/wallet — we only
// need to verify the factory/deposit wallet emit the right messages.

describe("PaymentFactory", () => {
    let chain: Blockchain;
    let deployer: SandboxContract<TreasuryContract>;
    let owner: SandboxContract<TreasuryContract>;
    let treasury: SandboxContract<TreasuryContract>;
    let usdtMaster: SandboxContract<TreasuryContract>;
    let factory: SandboxContract<PaymentFactory>;

    beforeEach(async () => {
        chain = await Blockchain.create();
        deployer = await chain.treasury("deployer");
        owner = await chain.treasury("owner");
        treasury = await chain.treasury("treasury");
        usdtMaster = await chain.treasury("usdtMaster");

        factory = chain.openContract(
            await PaymentFactory.fromInit(owner.address, treasury.address, usdtMaster.address)
        );
        const r = await factory.send(
            deployer.getSender(),
            { value: toNano("0.5") },
            { $$type: "Deploy", queryId: 0n }
        );
        expect(r.transactions).toHaveTransaction({ to: factory.address, deploy: true, success: true });
    });

    it("stores constructor args", async () => {
        expect((await factory.getFactoryOwner()).equals(owner.address)).toBe(true);
        expect((await factory.getFactoryTreasury()).equals(treasury.address)).toBe(true);
        expect((await factory.getUsdtMaster()).equals(usdtMaster.address)).toBe(true);
    });

    it("computeAddress is deterministic and matches initOf off-chain", async () => {
        const paymentId = 42n;
        const onChain = await factory.getComputeAddress(paymentId);
        const init = await DepositWallet.fromInit(factory.address, paymentId);
        expect(onChain.equals(init.address)).toBe(true);

        // Same input → same address.
        const again = await factory.getComputeAddress(paymentId);
        expect(onChain.equals(again)).toBe(true);

        // Different input → different address.
        const other = await factory.getComputeAddress(43n);
        expect(onChain.equals(other)).toBe(false);
    });

    it("only owner can send DeployAndSweep", async () => {
        const stranger = await chain.treasury("stranger");
        const r = await factory.send(
            stranger.getSender(),
            { value: toNano("0.2") },
            {
                $$type: "DeployAndSweep",
                payment_id: 1n,
                jetton_wallet: stranger.address,
                amount: 1000n,
            }
        );
        expect(r.transactions).toHaveTransaction({ to: factory.address, success: false });
    });

    it("DeployAndSweep deploys the DepositWallet and emits JettonTransfer", async () => {
        const paymentId = 7n;
        const deposit = await DepositWallet.fromInit(factory.address, paymentId);
        const fakeJettonWallet = await chain.treasury("fakeJettonWallet");

        const r = await factory.send(
            owner.getSender(),
            { value: toNano("0.3") },
            {
                $$type: "DeployAndSweep",
                payment_id: paymentId,
                jetton_wallet: fakeJettonWallet.address,
                amount: 1_000_000n,
            }
        );

        // Deposit wallet got deployed.
        expect(r.transactions).toHaveTransaction({
            to: deposit.address,
            deploy: true,
            success: true,
        });

        // And forwarded a JettonTransfer to the (fake) Jetton wallet.
        expect(r.transactions).toHaveTransaction({
            from: deposit.address,
            to: fakeJettonWallet.address,
            success: true,
        });
    });

    it("DeployAndSweep is idempotent (second call doesn't re-deploy)", async () => {
        const paymentId = 8n;
        const fakeJettonWallet = await chain.treasury("jw8");

        await factory.send(
            owner.getSender(),
            { value: toNano("0.3") },
            {
                $$type: "DeployAndSweep",
                payment_id: paymentId,
                jetton_wallet: fakeJettonWallet.address,
                amount: 500n,
            }
        );

        const r2 = await factory.send(
            owner.getSender(),
            { value: toNano("0.3") },
            {
                $$type: "DeployAndSweep",
                payment_id: paymentId,
                jetton_wallet: fakeJettonWallet.address,
                amount: 500n,
            }
        );

        const deposit = await DepositWallet.fromInit(factory.address, paymentId);
        // Second call: NO deploy:true on the wallet.
        const redeploy = r2.transactions.find(
            (t) =>
                t.description.type === "generic" &&
                (t as any).inMessage?.info?.dest?.equals?.(deposit.address) &&
                (t as any).parent === undefined
        );
        expect(redeploy).toBeUndefined();
    });

    it("DeployAndSweepTon forwards TON balance", async () => {
        const paymentId = 99n;
        const deposit = await DepositWallet.fromInit(factory.address, paymentId);

        // Seed the (undeployed) deposit address with some TON.
        await deployer.send({ to: deposit.address, value: toNano("1"), bounce: false });

        const treasuryBefore = await treasury.getBalance();

        const r = await factory.send(
            owner.getSender(),
            { value: toNano("0.2") },
            { $$type: "DeployAndSweepTon", payment_id: paymentId }
        );

        expect(r.transactions).toHaveTransaction({ to: deposit.address, deploy: true, success: true });
        expect(r.transactions).toHaveTransaction({
            from: deposit.address,
            to: treasury.address,
            success: true,
        });

        const treasuryAfter = await treasury.getBalance();
        expect(treasuryAfter).toBeGreaterThan(treasuryBefore);
    });

    it("only owner can SetTreasury / TransferOwnership", async () => {
        const stranger = await chain.treasury("stranger");

        const rt = await factory.send(
            stranger.getSender(),
            { value: toNano("0.1") },
            { $$type: "SetTreasury", new_treasury: stranger.address }
        );
        expect(rt.transactions).toHaveTransaction({ to: factory.address, success: false });

        const ro = await factory.send(
            stranger.getSender(),
            { value: toNano("0.1") },
            { $$type: "TransferOwnership", new_owner: stranger.address }
        );
        expect(ro.transactions).toHaveTransaction({ to: factory.address, success: false });
    });

    it("owner can SetTreasury and TransferOwnership", async () => {
        const newTreasury = await chain.treasury("newTreasury");
        const newOwner = await chain.treasury("newOwner");

        await factory.send(
            owner.getSender(),
            { value: toNano("0.1") },
            { $$type: "SetTreasury", new_treasury: newTreasury.address }
        );
        expect((await factory.getFactoryTreasury()).equals(newTreasury.address)).toBe(true);

        await factory.send(
            owner.getSender(),
            { value: toNano("0.1") },
            { $$type: "TransferOwnership", new_owner: newOwner.address }
        );
        expect((await factory.getFactoryOwner()).equals(newOwner.address)).toBe(true);

        // Old owner can no longer call privileged ops.
        const r = await factory.send(
            owner.getSender(),
            { value: toNano("0.1") },
            { $$type: "SetTreasury", new_treasury: treasury.address }
        );
        expect(r.transactions).toHaveTransaction({ to: factory.address, success: false });
    });
});

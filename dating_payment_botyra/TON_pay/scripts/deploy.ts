/**
 * Deploy PaymentFactory on testnet/mainnet.
 *
 *   ts-node scripts/deploy.ts testnet
 *   ts-node scripts/deploy.ts mainnet
 *
 * Requires env:
 *   TON_DEPLOYER_MNEMONIC  — 24 words, funded wallet
 *   TON_TREASURY           — destination address for swept USDT
 *   TON_USDT_MASTER        — USDT Jetton master address
 *                            (mainnet EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs)
 */
import { Address, beginCell, toNano } from "@ton/core";
import { TonClient, WalletContractV4 } from "@ton/ton";
import { mnemonicToPrivateKey } from "@ton/crypto";

import { PaymentFactory } from "../build/PaymentFactory/PaymentFactory_PaymentFactory";
import { DepositWallet } from "../build/DepositWallet/DepositWallet_DepositWallet";

async function main() {
    const network = (process.argv[2] ?? "testnet") as "testnet" | "mainnet";
    const endpoint =
        network === "mainnet"
            ? "https://toncenter.com/api/v2/jsonRPC"
            : "https://testnet.toncenter.com/api/v2/jsonRPC";

    const mnemonic = (process.env.TON_DEPLOYER_MNEMONIC ?? "").split(/\s+/).filter(Boolean);
    if (mnemonic.length !== 24) throw new Error("TON_DEPLOYER_MNEMONIC must be 24 words");
    const treasury = Address.parse(requireEnv("TON_TREASURY"));
    const usdtMaster = Address.parse(requireEnv("TON_USDT_MASTER"));

    const client = new TonClient({ endpoint, apiKey: process.env.TON_API_KEY });

    const keyPair = await mnemonicToPrivateKey(mnemonic);
    const wallet = WalletContractV4.create({ workchain: 0, publicKey: keyPair.publicKey });
    const walletContract = client.open(wallet);
    const ownerAddress = wallet.address;
    console.log("deployer:", ownerAddress.toString());

    const factory = await PaymentFactory.fromInit(ownerAddress, treasury, usdtMaster);
    console.log("PaymentFactory will be deployed at:", factory.address.toString());

    const openedFactory = client.open(factory);
    await openedFactory.send(
        walletContract.sender(keyPair.secretKey),
        { value: toNano("0.1") },
        { $$type: "Deploy", queryId: 0n }
    );
    console.log("deploy tx sent, waiting for confirmation...");

    const deposit = await DepositWallet.fromInit(factory.address, 0n);
    console.log("DepositWallet code bytes (base64):");
    console.log(deposit.init!.code.toBoc().toString("base64"));

    // After the factory is live, computeAddress for an arbitrary salt shows the
    // deterministic mapping.
    console.log("\nconfig to add to .env:");
    console.log(`TON_PAYMENT_FACTORY_ADDRESS=${factory.address.toString()}`);
    console.log(`TON_TREASURY_ADDRESS=${treasury.toString()}`);
    console.log(`TON_USDT_MASTER_ADDRESS=${usdtMaster.toString()}`);
    console.log(`TON_DEPOSIT_WALLET_CODE_BOC=${deposit.init!.code.toBoc().toString("base64")}`);
}

function requireEnv(name: string): string {
    const v = process.env[name];
    if (!v) throw new Error(`${name} env var is required`);
    return v;
}

main().catch((err) => {
    console.error(err);
    process.exit(1);
});

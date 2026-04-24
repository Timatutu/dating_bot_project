import * as anchor from "@coral-xyz/anchor";
import fs from "node:fs";
import {
  Connection,
  Keypair,
  PublicKey,
  SystemProgram,
} from "@solana/web3.js";
import { SolPay } from "../target/types/sol_pay";

const PROGRAM_ID = new PublicKey("BHihQurX9Cw9pPjQJaE77Wi6wMgvnMiczbeGoHHhk6uq");
const USDC_MINT = new PublicKey("9Abac3CPJznHcCJoFfJtHK7LVa8tLmvbHq1b2VjV9qMd");

const TREASURY = new PublicKey("3KHe6WvKbVydeHppmDf5h6jZzvox1HBWA5jRJ4whMG7J");

(async () => {
  const rpcUrl = "https://api.devnet.solana.com";
  const walletPath = process.env.SOLANA_KEYPAIR_PATH ?? "./.tmp-id.json";
  const walletSecret = JSON.parse(fs.readFileSync(walletPath, "utf-8")) as number[];
  const keypair = Keypair.fromSecretKey(Uint8Array.from(walletSecret));
  const wallet = new anchor.Wallet(keypair);
  const provider = new anchor.AnchorProvider(
    new Connection(rpcUrl, "confirmed"),
    wallet,
    {}
  );
  anchor.setProvider(provider);

  const program = new anchor.Program<SolPay>(
    require("../target/idl/sol_pay.json"),
    provider
  ) as anchor.Program<SolPay>;

  const sig = await program.methods
    .initialize(TREASURY, USDC_MINT)
    .accountsPartial({
      owner: provider.wallet.publicKey,
      systemProgram: SystemProgram.programId,
    })
    .rpc();

  console.log("initialize sig:", sig);
  const [factoryPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("factory")],
    PROGRAM_ID
  );
  console.log("factory PDA:", factoryPda.toBase58());
})();
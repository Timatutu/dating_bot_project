use anchor_lang::prelude::*;

pub mod constants;
pub mod error;
pub mod instructions;
pub mod state;

use instructions::{Initialize, Sweep, UpdateFactory};

use instructions::admin::__client_accounts_update_factory;
use instructions::initialize::__client_accounts_initialize;
use instructions::sweep::__client_accounts_sweep;

declare_id!("BHihQurX9Cw9pPjQJaE77Wi6wMgvnMiczbeGoHHhk6uq");

#[program]
pub mod sol_pay {
    use super::*;

    pub fn initialize(
        ctx: Context<Initialize>,
        treasury: Pubkey,
        usdc_mint: Pubkey,
    ) -> Result<()> {
        instructions::initialize::handler(ctx, treasury, usdc_mint)
    }

    pub fn sweep(ctx: Context<Sweep>, payment_id: [u8; 32]) -> Result<()> {
        instructions::sweep::handler(ctx, payment_id)
    }

    pub fn set_treasury(ctx: Context<UpdateFactory>, new_treasury: Pubkey) -> Result<()> {
        instructions::admin::set_treasury(ctx, new_treasury)
    }

    pub fn transfer_ownership(ctx: Context<UpdateFactory>, new_owner: Pubkey) -> Result<()> {
        instructions::admin::transfer_ownership(ctx, new_owner)
    }
}

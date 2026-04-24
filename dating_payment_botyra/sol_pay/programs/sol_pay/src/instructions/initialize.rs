use anchor_lang::prelude::*;

use crate::constants::FACTORY_SEED;
use crate::state::Factory;

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub owner: Signer<'info>,

    #[account(
        init,
        payer = owner,
        space = 8 + Factory::INIT_SPACE,
        seeds = [FACTORY_SEED],
        bump,
    )]
    pub factory: Account<'info, Factory>,

    pub system_program: Program<'info, System>,
}

pub fn handler(
    ctx: Context<Initialize>,
    treasury: Pubkey,
    usdc_mint: Pubkey,
) -> Result<()> {
    let factory = &mut ctx.accounts.factory;
    factory.owner = ctx.accounts.owner.key();
    factory.treasury = treasury;
    factory.usdc_mint = usdc_mint;
    factory.bump = ctx.bumps.factory;
    Ok(())
}

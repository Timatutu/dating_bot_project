use anchor_lang::prelude::*;

use crate::constants::FACTORY_SEED;
use crate::error::SolPayError;
use crate::state::Factory;

#[derive(Accounts)]
pub struct UpdateFactory<'info> {
    #[account(
        mut,
        seeds = [FACTORY_SEED],
        bump = factory.bump,
        has_one = owner @ SolPayError::OnlyOwner,
    )]
    pub factory: Account<'info, Factory>,

    pub owner: Signer<'info>,
}

pub fn set_treasury(ctx: Context<UpdateFactory>, new_treasury: Pubkey) -> Result<()> {
    require!(new_treasury != Pubkey::default(), SolPayError::ZeroAddress);
    let prev = ctx.accounts.factory.treasury;
    ctx.accounts.factory.treasury = new_treasury;
    emit!(TreasuryChanged {
        previous: prev,
        current: new_treasury,
    });
    Ok(())
}

pub fn transfer_ownership(ctx: Context<UpdateFactory>, new_owner: Pubkey) -> Result<()> {
    require!(new_owner != Pubkey::default(), SolPayError::ZeroAddress);
    let prev = ctx.accounts.factory.owner;
    ctx.accounts.factory.owner = new_owner;
    emit!(OwnershipTransferred {
        previous: prev,
        current: new_owner,
    });
    Ok(())
}

#[event]
pub struct TreasuryChanged {
    pub previous: Pubkey,
    pub current: Pubkey,
}

#[event]
pub struct OwnershipTransferred {
    pub previous: Pubkey,
    pub current: Pubkey,
}

use anchor_lang::prelude::*;

#[account]
#[derive(InitSpace)]
pub struct Factory {
    pub owner: Pubkey,
    pub treasury: Pubkey,
    pub usdc_mint: Pubkey,
    pub bump: u8,
}

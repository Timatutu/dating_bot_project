use anchor_lang::prelude::*;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token::{self, Mint, Token, TokenAccount, TransferChecked};

use crate::constants::{DEPOSIT_SEED, FACTORY_SEED};
use crate::error::SolPayError;
use crate::state::Factory;

#[derive(Accounts)]
#[instruction(payment_id: [u8; 32])]
pub struct Sweep<'info> {
    #[account(
        seeds = [FACTORY_SEED],
        bump = factory.bump,
        has_one = owner @ SolPayError::OnlyOwner,
        has_one = treasury,
        has_one = usdc_mint,
    )]
    pub factory: Account<'info, Factory>,

    #[account(mut)]
    pub owner: Signer<'info>,

    /// CHECK:
    #[account(
        seeds = [DEPOSIT_SEED, payment_id.as_ref()],
        bump,
    )]
    pub deposit_pda: UncheckedAccount<'info>,

    #[account(
        mut,
        associated_token::mint = usdc_mint,
        associated_token::authority = deposit_pda,
    )]
    pub deposit_ata: Account<'info, TokenAccount>,

    /// CHECK: 
    pub treasury: UncheckedAccount<'info>,

    pub usdc_mint: Account<'info, Mint>,

    #[account(
        init_if_needed,
        payer = owner,
        associated_token::mint = usdc_mint,
        associated_token::authority = treasury,
    )]
    pub treasury_ata: Account<'info, TokenAccount>,

    pub token_program: Program<'info, Token>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
}

pub fn handler(ctx: Context<Sweep>, payment_id: [u8; 32]) -> Result<()> {
    let amount = ctx.accounts.deposit_ata.amount;
    require!(amount > 0, SolPayError::ZeroBalance);

    let bump = ctx.bumps.deposit_pda;
    let bump_arr = [bump];
    let payment_ref: &[u8] = payment_id.as_ref();
    let pda_seeds: &[&[u8]] = &[DEPOSIT_SEED, payment_ref, &bump_arr];
    let signer_seeds: &[&[&[u8]]] = &[pda_seeds];

    let cpi_accounts = TransferChecked {
        from: ctx.accounts.deposit_ata.to_account_info(),
        mint: ctx.accounts.usdc_mint.to_account_info(),
        to: ctx.accounts.treasury_ata.to_account_info(),
        authority: ctx.accounts.deposit_pda.to_account_info(),
    };
    let cpi_ctx = CpiContext::new_with_signer(
        ctx.accounts.token_program.key(),
        cpi_accounts,
        signer_seeds,
    );
    token::transfer_checked(cpi_ctx, amount, ctx.accounts.usdc_mint.decimals)?;

    emit!(Swept {
        payment_id,
        amount,
        treasury: ctx.accounts.treasury.key(),
    });

    Ok(())
}

#[event]
pub struct Swept {
    pub payment_id: [u8; 32],
    pub amount: u64,
    pub treasury: Pubkey,
}

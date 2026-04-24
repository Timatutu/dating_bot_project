use anchor_lang::prelude::*;

#[error_code]
pub enum SolPayError {
    #[msg("only factory owner can call this")]
    OnlyOwner,
    #[msg("address must not be zero")]
    ZeroAddress,
    #[msg("deposit balance is zero — nothing to sweep")]
    ZeroBalance,
}

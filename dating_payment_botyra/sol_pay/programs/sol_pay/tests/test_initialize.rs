// TODO: тесты на litesvm — будем писать отдельным шагом.
// Покрыть надо:
//   - initialize создаёт Factory PDA с правильными полями
//   - sweep переводит весь deposit_ata.amount в treasury_ata
//   - sweep ревертит при нулевом балансе (ZeroBalance)
//   - sweep не пускает не-owner (OnlyOwner)
//   - set_treasury / transfer_ownership требуют owner signer

## Parser Contract (Baseline)

Goal: define a **rational, coherent** set of fields for testing. This is not
exhaustive real‑world coverage. The fixtures in this folder are the source of
truth for expected behavior.

### Document Types
- `BANK_STATEMENT`
- `INCOME_PROOF`

### Required Fields (Baseline)
#### BANK_STATEMENT
- `bank_name`
- `clabe`
- `account_number`
- `rfc`
- `period_start`
- `period_end`
- `balance`
- `average_balance`
- `total_deposits`
- `total_withdrawals`

#### INCOME_PROOF
- `employer_name`
- `rfc`
- `payment_frequency`
- `period_start`
- `period_end`
- `net_income`
- `gross_income`

### Data Expectations
- Dates: `DD/MM/YYYY` or `DD-MM-YYYY`
- Amounts: normalized to digits + decimal point (e.g., `12345.67`)
- Text fields: uppercase, accents removed by parser normalization

### Scope Notes
- We validate **only** against our fixtures, not all real‑world formats.
- New variants must include a fixture pair and expected output.

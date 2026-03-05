## Fixtures (OCR Samples)

Purpose: store sanitized, real OCR line samples used to validate parsers.

Rules
- Do not include PII (names, addresses, CURP, account numbers, RFCs).
- Replace sensitive values with realistic but fake tokens.
- Preserve formatting, punctuation, and OCR noise.
- Keep each fixture focused on a single document type.

File naming
- `bank_statement_{bank}_{n}.json`
- `income_proof_{employer}_{n}.json`

Format (JSON)
- Lines file: `*_lines.json` (list of objects with `text` and `confidence` keys)
- Expected file: `*_expected.json` with:
  - `document_type`: `BANK_STATEMENT` or `INCOME_PROOF`
  - `fields`: expected parser output

Lines example
```json
[
  { "text": "BBVA México", "confidence": 98.0 },
  { "text": "CLABE Interbancaria: 012345678901234567", "confidence": 97.5 }
]
```

Expected example
```json
{
  "document_type": "BANK_STATEMENT",
  "fields": {
    "bank_name": { "value": "BBVA MEXICO", "confidence": 98.0 },
    "clabe": { "value": "012345678901234567", "confidence": 97.5 }
  }
}
```

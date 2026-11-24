# Offline Message Scanner Evaluation

- Total records: 4044
- This report measures baseline rule coverage offline; it is not a production accuracy claim.
- Synthetic labels and no-signal results are not proof of safety.

## Results by source

| Source | Total | Detected | Missed positive labels |
|---|---:|---:|---:|
| synthetic | 3837 | 1095 | 939 |
| trannguyenthaituan/vietnamese_sms_phishing_sample | 207 | 131 | 0 |

## Feature coverage

- `account_deactivation`: 14 records
- `advance_fee`: 1896 records
- `brand_impersonation`: 72 records
- `credential_request`: 135 records
- `external_link_request`: 828 records
- `investment_scam`: 47 records
- `prize_claim`: 234 records
- `secrecy`: 76 records
- `urgency`: 656 records
- `verification_phishing`: 941 records

Positive-label misses retained for review: 939

# Status

- Current milestone: M0
- Last task: M0.2 follow-up: open issues 1 to 5 settled by Steven (D17 to D21)
- Next task: M0.3 golden fixture

## Open issues

1. schema_version stays 1, although this follow-up changed two contract rules: claims.location must be non-empty (D21), and normalize_quote maps four more hyphen characters (D19), which changes segment_hash for text containing them. Standing rule 4 bumps the schema version on contract changes. No v1 file exists yet and the contracts are not merged, so this was treated as still defining version 1. Confirm before M0.3 writes the golden fixture.

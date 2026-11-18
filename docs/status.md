# Status

- Current milestone: M0
- Last task: M0.2 records fix before merge (D22, IC19 soft hyphens)
- Next task: M0.3 golden fixture

## Open issues

These are for later, not to fix now.

1. QUOTE_NOT_FOUND blocks a correct quote that spans two line-break hyphens of different kinds (a compound such as "self-" then "evident", and a split word such as "con-" then "sequence"), because each check joins or keeps every break at once. It can only block, never pass, a quote. Revisit before OCR sources in the pilot.
2. episode.budget_cap_usd accepts 0 or a negative value, so BUDGET_CAP_EXCEEDED fires on any spend.

# Status

- Current milestone: M0
- Last task: M0.1 repo scaffold and CLAUDE.md, plus a follow-up: CHARTER.md committed, Records rules tightened, IC5 settled
- Next task: M0.2 schema models and validate command

## Open issues

1. The charter's quote gate allows "only whitespace and OCR punctuation differences", but IC8's quote normalization also applies NFKC, which changes more than punctuation (for example, a superscript 2 becomes a plain 2, and the long s becomes s). Align the charter wording and IC8 before the quote check is built.

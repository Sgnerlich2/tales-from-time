# Status

- Current milestone: M0
- Last task: M0.2 schema models and validate command (all rules, single-file and cross-file; no M0.2b needed)
- Next task: M0.3 golden fixture

## Open issues

1. Single-file mode runs only SCHEMA_INVALID and DUPLICATE_ID, reading "schema rules only" literally (IC20). A 12-second static shot passes `tft validate scenes.json` but fails folder validation. Confirm, or ask for single-file value rules too.
2. Rejected claims are still checked. QUOTE_NOT_FOUND, UNKNOWN_SOURCE, and LONE_CONFLICT_GROUP apply to claims whose status is rejected, so an episode that keeps a rejected claim with a bad quote can never pass. Decide whether rejected claims are exempt or must be removed from claims.json.
3. Quote normalization gaps, all failing safe (they can block a correct quote, never pass a wrong one): hyphen-like characters other than the three named (U+2010 hyphen, U+2011 non-breaking hyphen, U+2012 figure dash, U+2015 horizontal bar) are not mapped; a line-break hyphen between digits (1914- then 1918) is not joined; QUOTE_MISMATCH compares with line-break hyphens joined only, so a claim quote stored as "well-" plus line break plus "known" does not equal segment text "well-known".
4. Folder validation requires no particular file. An empty folder passes with 0 files, and INSUFFICIENT_SOURCES cannot run when script.json exists but sources.json does not.
5. Only quote and bias_note must be non-empty, as specified. Empty strings pass for claim text and location, titles, and attribution. The charter says every claim carries its page or location, so location at least may need tightening.

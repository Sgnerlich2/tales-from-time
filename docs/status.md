# Status

- Current milestone: M0
- Last task: M0.1 repo scaffold and CLAUDE.md
- Next task: M0.2 schema models and validate command

## Open issues

1. Local main has no commits. The M0.1 commit is the root commit of branch m0.1-scaffold, and no remote branches have been fetched. If origin already has commits (for example a README made on GitHub), rebase onto origin/main before pushing.
2. The Records rule protects entries labeled Owner confirmed, Recommended, or Assumption. D13's status, Deferred by Steven, is not in that list. Proposal: add it to the rule, or treat every status Steven set as protected.
3. IC5 does not say when the workspace/ fallback applies instead of TFT_WORKSPACE (default C:\tft-workspace). Settle it in the task that writes the workspace lookup.
4. New implementation choices: IC16 was appended to the decision table and the Changes section left empty, reading Changes as the log of edits to existing entries. Confirm or correct.
5. CHARTER.md is not in the repo yet. Once Steven adds it, CLAUDE.md should point to it.

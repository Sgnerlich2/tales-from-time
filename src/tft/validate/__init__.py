"""Validation of episode files behind the validate command.

Schema rules check each contract file against its model; value and cross-file rules are
pure functions in tft.validate.rules. The validator only reads files: it never writes or
changes them and makes no network calls.
"""

from tft.validate.problems import RULE_CODES, Problem
from tft.validate.runner import Report, validate_file, validate_folder

__all__ = ["RULE_CODES", "Problem", "Report", "validate_file", "validate_folder"]

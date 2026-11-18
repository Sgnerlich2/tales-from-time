"""normalize_quote, quote matching, segment_hash, and file_sha256."""

import hashlib

import pytest

from tft.textnorm import file_sha256, normalize_quote, quote_in_text, segment_hash

SOURCE = (
    "INVENTED TEST DOCUMENT, not a real historical source.\n"
    "At 4:10 a.m. I reported “ice ahead” to   the bridge, and the well-\n"
    "known captain ordered the engines full astern.\n"
    "The floe lay 10² yards off the bow.\n"
)


def test_normalize_quote_straightens_curly_quotes():
    assert normalize_quote("“Ice,” he said, ‘ahead’ „quite‟ ‚so‛") == (
        "\"Ice,\" he said, 'ahead' \"quite\" 'so'"
    )


def test_normalize_quote_maps_dashes_and_the_ellipsis():
    assert normalize_quote("1901–1902 — a − b…") == "1901-1902 - a - b..."


def test_normalize_quote_removes_soft_hyphens():
    assert normalize_quote("well­known") == "wellknown"


def test_normalize_quote_joins_a_line_break_hyphen_between_letters():
    assert normalize_quote("ice-\nberg") == "iceberg"
    assert normalize_quote("ice- \r\n  berg") == "iceberg"
    assert normalize_quote("été-\rété") == "étéété"


def test_normalize_quote_keeps_the_hyphen_when_asked():
    assert normalize_quote("ice-\nberg", keep_linebreak_hyphen=True) == "ice-berg"


def test_normalize_quote_leaves_other_hyphens_alone():
    assert normalize_quote("well-known") == "well-known"
    assert normalize_quote("1914-\n1918") == "1914- 1918"  # digits, not letters
    assert normalize_quote("ice -\nberg") == "ice - berg"  # no letter before the hyphen
    assert normalize_quote("ice-\n\nberg") == "ice- berg"  # a paragraph break, not a line break


def test_normalize_quote_collapses_whitespace_and_strips_the_ends():
    assert normalize_quote("  ice\t\tahead\n now  ") == "ice ahead now"


@pytest.mark.parametrize(
    "text",
    ["Ice AHEAD", "10²", "ﬁre", "ſhip", "café", "café", "Ａ"],
    ids=["case", "superscript", "ligature", "long-s", "composed", "decomposed", "fullwidth"],
)
def test_normalize_quote_keeps_case_and_applies_no_unicode_normalization(text):
    assert normalize_quote(text) == text


# Matching, as QUOTE_NOT_FOUND uses it.


def test_quote_with_curly_quotes_line_break_hyphen_and_extra_whitespace_still_matches():
    assert quote_in_text('I reported "ice ahead" to the bridge', SOURCE)
    assert quote_in_text("the wellknown captain", SOURCE)
    assert quote_in_text("I  reported\n“ice ahead”", SOURCE)


def test_quote_with_one_changed_word_does_not_match():
    assert not quote_in_text('I reported "ice astern" to the bridge', SOURCE)


def test_quote_with_102_does_not_match_a_source_with_10_squared():
    assert not quote_in_text("The floe lay 102 yards off the bow.", SOURCE)
    assert quote_in_text("The floe lay 10² yards off the bow.", SOURCE)


def test_source_with_well_at_a_line_end_matches_a_quote_reading_well_known():
    assert quote_in_text("the well-known captain ordered the engines full astern", SOURCE)


def test_quote_that_normalizes_to_nothing_never_matches():
    assert not quote_in_text("­", SOURCE)


# Hashes


def test_segment_hash_follows_its_definition():
    expected = hashlib.sha256(b"It sank.\nCLM-001,CLM-002").hexdigest()
    assert segment_hash("It sank.", ["CLM-002", "CLM-001"]) == expected


def test_segment_hash_uses_the_normalized_text():
    assert segment_hash("  It “sank.” ", []) == segment_hash('It "sank."', [])


def test_segment_hash_changes_with_the_text_or_the_claims():
    base = segment_hash("It sank.", ["CLM-001"])
    assert segment_hash("It sank!", ["CLM-001"]) != base
    assert segment_hash("It sank.", ["CLM-001", "CLM-002"]) != base


def test_file_sha256_hashes_the_raw_bytes(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"line one\r\nline two\n")
    assert file_sha256(path) == hashlib.sha256(b"line one\r\nline two\n").hexdigest()

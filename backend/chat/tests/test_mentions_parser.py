from types import SimpleNamespace

from chat.mentions import resolve_mentions


def u(uid, full_name):
    return SimpleNamespace(id=uid, full_name=full_name)


NOAH = u(1, "Noah Braun")
NOAH_SHORT = u(2, "Noah")
SOFIA = u(3, "Sofia Mueller")


def test_resolves_a_candidate_name():
    assert resolve_mentions("hey @Noah Braun", [NOAH]) == [NOAH]


def test_longest_name_wins():
    result = resolve_mentions("hey @Noah Braun", [NOAH_SHORT, NOAH])
    assert result == [NOAH]


def test_shorter_name_still_matches_on_its_own():
    assert resolve_mentions("hey @Noah!", [NOAH_SHORT, NOAH]) == [NOAH_SHORT]


def test_case_insensitive():
    assert resolve_mentions("hey @noah braun", [NOAH]) == [NOAH]


def test_email_address_is_not_a_mention():
    assert resolve_mentions("write to noah@braun.com", [NOAH]) == []


def test_trailing_punctuation_ends_the_name():
    assert resolve_mentions("thanks @Noah Braun, great", [NOAH]) == [NOAH]


def test_possessive_ends_the_name():
    assert resolve_mentions("@Noah Braun's idea", [NOAH]) == [NOAH]


def test_longer_word_is_not_a_partial_match():
    assert resolve_mentions("hey @Noahs", [NOAH_SHORT]) == []


def test_same_name_twice_resolves_once():
    assert resolve_mentions("@Noah Braun and @Noah Braun", [NOAH]) == [NOAH]


def test_two_different_people_keep_first_appearance_order():
    text = "@Sofia Mueller and @Noah Braun"
    assert resolve_mentions(text, [NOAH, SOFIA]) == [SOFIA, NOAH]


def test_unknown_name_is_ignored():
    assert resolve_mentions("hey @Elise Roth", [NOAH]) == []


def test_mention_at_start_of_a_later_line():
    assert resolve_mentions("first line\n@Noah Braun", [NOAH]) == [NOAH]


def test_empty_and_plain_content():
    assert resolve_mentions("", [NOAH]) == []
    assert resolve_mentions("no at signs here", [NOAH]) == []

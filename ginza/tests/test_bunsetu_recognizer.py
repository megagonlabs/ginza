from ginza.bunsetu_recognizer import BunsetuRecognizer


def test_bunsetu_recognizer_clause_marker_rules_setter():
    recognizer = BunsetuRecognizer(None)
    rules = [{"tag_": "補助記号-読点"}, {"pos_": "PUNCT"}]

    recognizer.clause_marker_rules = rules

    assert recognizer.clause_marker_rules == rules

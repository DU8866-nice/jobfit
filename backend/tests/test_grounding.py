from jobfit.grounding import Grounder, normalize


def test_normalize_folds_case_punctuation_and_spacing():
    assert normalize("  Built  Tableau\ndashboards!  ") == "built tableau dashboards"


def test_normalize_keeps_plus_and_hash():
    assert normalize("C++ and C#") == "c++ and c#"


def test_quote_matches_despite_bullets_quotes_and_line_breaks():
    source = "• Wrote “SQL” queries to join\nsales and inventory tables"
    assert Grounder(source).contains('Wrote "SQL" queries to join sales and inventory tables')


def test_quote_must_appear_in_order():
    assert not Grounder("joined sales tables").contains("tables sales joined")


def test_quote_must_start_and_end_on_word_boundaries():
    grounder = Grounder("Five years of JavaScript")
    assert not grounder.contains("Java")
    assert grounder.contains("JavaScript")


def test_made_up_quote_is_rejected():
    assert not Grounder("Built Tableau dashboards").contains("Built Power BI dashboards")


def test_empty_quote_is_rejected():
    grounder = Grounder("anything")
    assert not grounder.contains("")
    assert not grounder.contains("  ...  ")

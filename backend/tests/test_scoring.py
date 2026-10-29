from jobfit.scoring import compute_score


def test_weights_must_have_75_and_nice_to_have_25():
    score = compute_score(
        [
            ("must_have", "met"),
            ("must_have", "partial"),
            ("nice_to_have", "missing"),
            ("nice_to_have", "met"),
        ]
    )
    # must: (1 + 0.5) / 2 = 0.75 ; nice: 0.5 ; overall = 0.75*0.75 + 0.25*0.5 = 0.6875
    assert score.overall == 69
    assert score.must_have == 0.75
    assert score.nice_to_have == 0.5
    assert (score.counts.met, score.counts.partial, score.counts.missing) == (2, 1, 1)


def test_only_must_haves_count_fully():
    score = compute_score([("must_have", "met"), ("must_have", "missing")])
    assert score.overall == 50
    assert score.nice_to_have is None


def test_only_nice_to_haves_count_fully():
    assert compute_score([("nice_to_have", "met")]).overall == 100


def test_no_requirements_scores_zero():
    score = compute_score([])
    assert score.overall == 0
    assert score.must_have is None and score.nice_to_have is None

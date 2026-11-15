from backend.engine.write_sites import _failed_analogs, _fmt, _verdict


def test_verdict_thresholds():
    assert _verdict(80.0) == "match"
    assert _verdict(79.9) == "partial"
    assert _verdict(60.0) == "partial"
    assert _verdict(59.9) == "mismatch"


def test_fmt_units():
    assert _fmt(3361.2, "m") == "3,361 m"
    assert _fmt(0.7117, "unitless") == "0.71"
    assert _fmt(-171.489, "degC") == "-171.5 degC"
    assert _fmt(0.0, "mm") == "0.0 mm"


def test_failed_analogs_reads_fail_rows_only():
    text = ("## Lunar south pole\n\n| Site | Score | Rank pct | Check | Best | Worst |\n|---|---|---|---|---|---|\n"
            "| Atacama | 63.1 | 87.2 | PASS | a | b |\n| Devon | 48.9 | 69.8 | FAIL | a | b |\n")
    assert _failed_analogs(text) == ["Lunar south pole: Devon (rank percentile 69.8)"]

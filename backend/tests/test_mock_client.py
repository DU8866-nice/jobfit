"""The offline demo provider, run through the full pipeline."""

from jobfit.llm.mock_client import MockClient
from jobfit.pipeline import analyze


def test_mock_reads_the_sample_job_ad(job_ad, resume):
    result = analyze(job_ad, resume, MockClient())
    by_text = {r.text: r for r in result.requirements}

    assert result.provider == "mock"
    assert result.job_title == "Junior Data Analyst"
    assert len(result.requirements) == 7, "the five bullets under 'What you'll bring' plus two nice-to-haves"

    assert by_text["Strong SQL skills for querying and joining large datasets"].status == "met"
    assert by_text["Python (pandas) for data cleaning and automation"].status == "met"
    assert by_text["Experience building dashboards in Power BI"].status == "missing"
    assert by_text["Exposure to AWS or another cloud platform"].importance == "nice_to_have"
    assert "Hybrid work and a learning budget" not in by_text, "benefits are not requirements"

    assert result.work_rights.status == "required"
    assert result.work_rights.quote_verified

    assert "Power BI" in result.missing_keywords
    assert "SQL" not in result.missing_keywords


def test_mock_output_passes_verification(job_ad, resume):
    result = analyze(job_ad, resume, MockClient())
    assert result.grounding.evidence_removed == 0
    assert result.grounding.suggestions_removed == 0
    assert result.suggestions, "expected at least one suggestion"
    for suggestion in result.suggestions:
        assert suggestion.original in resume


def test_mock_writes_explanations_in_chinese(job_ad, resume):
    result = analyze(job_ad, resume, MockClient(), language="zh")
    assert result.language == "zh"
    assert "演示模式" in result.summary
    assert any("简历" in r.explanation for r in result.requirements)


def test_mock_handles_a_chinese_job_ad():
    job_ad = """\
数据分析师
任职要求：
1、熟练使用 SQL 和 Python 进行数据分析
2、有 Tableau 或 Power BI 报表开发经验
加分项：
1、熟悉机器学习
"""
    resume = """\
陈晓明
技能：SQL、Python、Tableau
实习经历：使用 SQL 和 Python 清洗零售销售数据，并用 Tableau 制作周报看板
"""
    result = analyze(job_ad, resume, MockClient(), language="zh")
    assert [r.importance for r in result.requirements] == ["must_have", "must_have", "nice_to_have"]
    assert result.requirements[0].status == "met"
    assert result.grounding.evidence_removed == 0

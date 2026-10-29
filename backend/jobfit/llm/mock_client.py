"""An offline stand-in for the model, built from simple text rules.

It lets the whole app run with no API key (for local development, tests, CI and a
free demo). It is deliberately simple: keyword matching, not understanding. The UI
labels its results as a demo.
"""

from __future__ import annotations

import re

from ..grounding import Grounder
from ..schemas import (
    Category,
    ExtractionResult,
    Importance,
    Language,
    MatchResult,
    MatchStatus,
    Requirement,
    RequirementMatch,
    Suggestion,
    WorkRights,
)

MAX_REQUIREMENTS = 15
MAX_SUGGESTIONS = 3
MAX_QUOTE_CHARS = 160

_BULLET = re.compile(r"^\s*(?:[-*•·▪●–—]|\d+[.)、])\s*")
_NICE = re.compile(
    r"(nice to have|nice-to-have|\bbonus\b|desirable|preferred|advantage|a plus|ideally|加分|优先)", re.I
)
_REQUIREMENT_HEADING = re.compile(
    r"(requirements?|qualifications?|you have|you'll have|you will have|about you|skills|experience|"
    r"what you bring|what you'll bring|who you are|essential|任职要求|岗位要求|任职资格|技能要求)",
    re.I,
)
_OTHER_HEADING = re.compile(
    r"(benefits|perks|what we offer|why join|about us|about the company|how to apply|the role|"
    r"responsibilities|what you'll do|day to day|岗位职责|工作职责|公司介绍|福利)",
    re.I,
)
_WORK_RIGHTS = re.compile(
    r"(citizen|permanent resident|working rights|right to work|work rights|work authori[sz]ation|"
    r"authori[sz]ed to work|visa sponsorship|sponsorship|security clearance|baseline clearance|\bNV1\b|\bNV2\b|"
    r"签证|工作许可|国籍)",
    re.I,
)
_WORK_RIGHTS_SOFT = re.compile(r"(preferred|desirable|ideally|advantage|优先)", re.I)

# Common terms in IT and data job ads. Matching is case-insensitive.
KNOWN_TERMS = [
    "Python", "SQL", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "React", "Next.js", "Node.js", "Vue", "Angular", "HTML", "CSS", "REST", "GraphQL",
    "FastAPI", "Django", "Flask", "Spring", ".NET",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "CI/CD", "Git", "GitHub Actions", "Linux",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Snowflake", "dbt", "Airflow", "Spark", "Databricks",
    "Power BI", "Tableau", "Excel", "Looker",
    "pandas", "NumPy", "scikit-learn", "PyTorch", "TensorFlow", "machine learning", "deep learning",
    "NLP", "LLM", "RAG", "MLOps", "computer vision", "statistics", "data visualisation", "data visualization",
    "ETL", "data modelling", "data modeling", "Agile", "Scrum", "Jira",
    "stakeholder management", "communication", "unit testing", "API", "APIs",
    "Shopify", "SEO", "Google Analytics",
    "数据分析", "机器学习", "深度学习", "沟通",
]
_CJK = re.compile(r"[\u4e00-\u9fff]")
_STOPWORDS = {
    "and", "the", "with", "for", "you", "your", "our", "are", "will", "have", "has", "from", "that",
    "this", "able", "ability", "strong", "good", "work", "working", "using", "experience", "skills",
    "knowledge", "understanding", "proven", "excellent", "years", "year", "least", "within", "into",
}

TEXT: dict[str, dict[str, str]] = {
    "en": {
        "untitled": "Untitled role",
        "work_rights": "The ad mentions citizenship, residency, visa or work-authorisation conditions, or a security clearance.",
        "met": "Your resume mentions {found}.",
        "partial": "Your resume mentions {found} but not {missing}.",
        "missing": "No mention of {terms} in your resume.",
        "related": "Some related wording appears in your resume; check it really covers this.",
        "nothing": "Nothing in your resume clearly addresses this.",
        "placeholder": " [add a measurable result, e.g. number of users, % improvement or time saved]",
        "rationale": "This is your clearest evidence for \u201c{requirement}\u201d. A concrete outcome makes it easier for a recruiter to notice.",
        "summary": (
            "Demo analysis based on keyword matching: {met} of {total} requirements look met, "
            "{partial} partly met and {missing} missing. Connect an AI provider for a real reading of your resume."
        ),
    },
    "zh": {
        "untitled": "未命名职位",
        "work_rights": "职位描述提到了国籍、居留、签证或工作许可要求，或安全审查。",
        "met": "你的简历提到了 {found}。",
        "partial": "你的简历提到了 {found}，但没有提到 {missing}。",
        "missing": "简历中没有提到 {terms}。",
        "related": "简历里有相关的描述，请确认它确实覆盖了这一项。",
        "nothing": "简历中没有明确对应这一项的内容。",
        "placeholder": " [补充一个可量化的结果，例如用户数、提升百分比或节省的时间]",
        "rationale": "这是你满足\u201c{requirement}\u201d最直接的证据，加上具体成果，招聘方更容易注意到。",
        "summary": (
            "演示模式（关键词匹配）：{total} 项要求中，{met} 项看起来已满足，{partial} 项部分满足，"
            "{missing} 项缺失。接入 AI 服务后可以得到真正读懂简历的分析。"
        ),
    },
}


def _strip_bullet(line: str) -> str:
    return _BULLET.sub("", line, count=1).strip()


def _is_bullet(line: str) -> bool:
    return bool(_BULLET.match(line)) and bool(_strip_bullet(line))


def _is_heading(line: str) -> bool:
    stripped = line.strip().rstrip(":：")
    return bool(stripped) and not _is_bullet(line) and len(stripped) <= 60 and (
        line.strip().endswith((":", "：")) or stripped.isupper() or len(stripped.split()) <= 6
    )


def _keywords(text: str) -> list[str]:
    grounder = Grounder(text)
    found: list[str] = []
    for term in KNOWN_TERMS:
        if grounder.contains(term) and term.lower() not in {f.lower() for f in found}:
            found.append(term)
    return found


def _category(text: str) -> Category:
    lowered = text.lower()
    if re.search(r"\b(degree|bachelor|master|diploma|phd)\b|学历|本科|硕士|学位", lowered):
        return "education"
    if re.search(r"\b(certif|licen[cs]e)|证书", lowered):
        return "certification"
    if re.search(r"\b\d+\+?\s*years?\b|\bexperience\b|\d+\s*年|经验", lowered):
        return "experience"
    return "skill"


def _truncate(text: str) -> str:
    if len(text) <= MAX_QUOTE_CHARS:
        return text
    return text[:MAX_QUOTE_CHARS].rsplit(" ", 1)[0]


class MockClient:
    name = "mock"

    def extract_requirements(self, job_description: str, language: Language) -> ExtractionResult:
        t = TEXT[language]
        lines = [line for line in job_description.splitlines() if line.strip()]
        title = _strip_bullet(lines[0])[:80] if lines else t["untitled"]

        work_rights = WorkRights(status="not_mentioned", detail="", quote="")
        candidates: list[tuple[str, bool]] = []  # (text, in a nice-to-have section)
        has_requirement_heading = any(_is_heading(l) and _REQUIREMENT_HEADING.search(l) for l in lines)
        in_requirements = not has_requirement_heading
        in_nice_section = False

        for line in lines[1:]:
            text = _strip_bullet(line)
            if _WORK_RIGHTS.search(text):
                if work_rights.status == "not_mentioned":
                    soft = bool(_WORK_RIGHTS_SOFT.search(text))
                    work_rights = WorkRights(
                        status="preferred" if soft else "required", detail=t["work_rights"], quote=text
                    )
                continue
            if _is_heading(line):
                if _NICE.search(line):
                    in_requirements, in_nice_section = True, True
                elif _REQUIREMENT_HEADING.search(line):
                    in_requirements, in_nice_section = True, False
                elif _OTHER_HEADING.search(line):
                    in_requirements = False
                continue
            if in_requirements and _is_bullet(line):
                candidates.append((text, in_nice_section))

        requirements: list[Requirement] = []
        for index, (text, nice_section) in enumerate(candidates[:MAX_REQUIREMENTS], start=1):
            importance: Importance = "nice_to_have" if nice_section or _NICE.search(text) else "must_have"
            requirements.append(
                Requirement(
                    id=f"R{index}",
                    text=text[:140],
                    importance=importance,
                    category=_category(text),
                    keywords=_keywords(text),
                )
            )

        return ExtractionResult(job_title=title, company="", requirements=requirements, work_rights=work_rights)

    def match_resume(
        self, requirements: list[Requirement], resume_text: str, language: Language
    ) -> MatchResult:
        t = TEXT[language]
        separator = "、" if language == "zh" else ", "
        resume_lines = [_strip_bullet(l) for l in resume_text.splitlines() if l.strip()]
        line_grounders = [(line, Grounder(line)) for line in resume_lines if line]
        whole = Grounder(resume_text)

        matches: list[RequirementMatch] = []
        suggestions: list[Suggestion] = []
        used_lines: set[str] = set()

        for req in requirements:
            status: MatchStatus
            if req.keywords:
                found = [k for k in req.keywords if whole.contains(k)]
                coverage = len(found) / len(req.keywords)
                status = "met" if coverage >= 0.6 else "partial" if found else "missing"
                evidence_lines = [line for line, g in line_grounders if any(g.contains(k) for k in found)]
                missing_terms = [k for k in req.keywords if k not in found]
                explanation = t[status].format(
                    found=separator.join(found),
                    missing=separator.join(missing_terms),
                    terms=separator.join(req.keywords),
                )
            else:
                words = [w for w in re.findall(r"[a-zA-Z]{4,}", req.text.lower()) if w not in _STOPWORDS]
                evidence_lines = [
                    line for line, g in line_grounders if sum(g.contains(w) for w in set(words)) >= 2
                ]
                status = "partial" if evidence_lines else "missing"
                explanation = t["related"] if evidence_lines else t["nothing"]

            evidence = [_truncate(line) for line in evidence_lines[:2]] if status != "missing" else []
            matches.append(
                RequirementMatch(requirement_id=req.id, status=status, evidence=evidence, explanation=explanation)
            )

            for line in evidence:
                # Only sentence-like lines without a number yet; skip skill lists and lines already used.
                if _CJK.search(line):
                    is_sentence = len(line) >= 12 and line.count("、") < 2
                else:
                    is_sentence = len(line.split()) >= 6 and line.count(",") < 2
                if (
                    len(suggestions) >= MAX_SUGGESTIONS
                    or line in used_lines
                    or not is_sentence
                    or re.search(r"\d", line)
                ):
                    continue
                used_lines.add(line)
                suggestions.append(
                    Suggestion(
                        requirement_ids=[req.id],
                        original=line,
                        rewrite=line + t["placeholder"],
                        rationale=t["rationale"].format(requirement=req.text),
                    )
                )

        counts = {s: sum(m.status == s for m in matches) for s in ("met", "partial", "missing")}
        summary = t["summary"].format(total=len(matches), **counts)
        return MatchResult(matches=matches, suggestions=suggestions, summary=summary)

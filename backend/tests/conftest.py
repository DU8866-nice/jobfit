"""Shared test data. The job ad and the person in the resume are invented."""

import pytest

SAMPLE_JOB_AD = """\
Junior Data Analyst
Bright Harbour Analytics — Melbourne VIC (Hybrid)

About the role
You'll turn messy operational data into clear dashboards for our retail clients.

What you'll bring
- Strong SQL skills for querying and joining large datasets
- Python (pandas) for data cleaning and automation
- Experience building dashboards in Power BI
- Clear communication with non-technical stakeholders
- A degree in IT, statistics or a related field

Nice to have
- Exposure to AWS or another cloud platform
- dbt or Airflow

Applicants must have full working rights in Australia.

What we offer
- Hybrid work and a learning budget
"""

SAMPLE_RESUME = """\
Alex Chen
Melbourne VIC | alex.chen@example.com

EDUCATION
Master of Information Technology, Example University, 2026
Bachelor of Engineering (Electronic), 2024

SKILLS
SQL, Python (pandas, NumPy), Tableau, Excel, Git

EXPERIENCE
Data Intern, Southbank Retail Co (Nov 2025 – Feb 2026)
- Wrote SQL queries to join sales and inventory tables for weekly reporting
- Automated a data cleaning script in Python, cutting report preparation from 3 hours to 20 minutes
- Built Tableau dashboards for the store operations team
- Presented findings to store managers every fortnight

PROJECTS
- Customer churn analysis with pandas and scikit-learn
"""


@pytest.fixture
def job_ad() -> str:
    return SAMPLE_JOB_AD


@pytest.fixture
def resume() -> str:
    return SAMPLE_RESUME

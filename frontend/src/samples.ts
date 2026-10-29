import type { Language } from "./types";

// Invented examples so visitors can try the tool without pasting their own documents.

const EN_JOB = `Junior Data Analyst
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
- Hybrid work and a learning budget`;

const EN_RESUME = `Alex Chen
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
- Customer churn analysis with pandas and scikit-learn`;

const ZH_JOB = `数据分析师（应届/1 年以内）
某零售科技公司 · 上海

岗位职责：
负责门店销售数据的整理、分析和报表制作。

任职要求：
1、统计学、计算机或相关专业本科及以上学历
2、熟练使用 SQL 进行数据查询
3、熟悉 Python 或 R，能独立完成数据清洗
4、有 Power BI 或 Tableau 报表开发经验
5、良好的沟通能力，能向业务同事解释数据结论

加分项：
1、了解机器学习基础算法
2、有零售或电商行业实习经历

福利：
五险一金，带薪年假`;

const ZH_RESUME = `陈晓明
上海 | xiaoming.chen@example.com

教育背景
示例大学 计算机科学与技术 本科，2026 年毕业

技能
SQL、Python（pandas）、Tableau、Excel

实习经历
示例便利店连锁 数据分析实习生（2025.07 – 2025.12）
- 使用 SQL 汇总 200 家门店的周销售数据
- 用 Python 编写数据清洗脚本，处理缺失值和重复记录
- 用 Tableau 制作区域销售周报看板，供运营团队每周例会使用
- 每月向区域经理汇报销售趋势和异常门店

项目经历
- 基于 pandas 的会员复购分析`;

export function sample(language: Language): { job: string; resume: string } {
  return language === "zh" ? { job: ZH_JOB, resume: ZH_RESUME } : { job: EN_JOB, resume: EN_RESUME };
}

# Roadmap / 路线图

This file is the shared memory of the project. At the start of every working session, read it, pick the next unchecked item, and update it before finishing.

每次开始干活前先读这份文件，挑下一个没打勾的任务；结束前更新它。

## How we work / 分工

- **James**: decides what to build next, owns accounts and API keys, tests with real job ads and real users, and must be able to explain every line of code in an interview.
- **Claude**: writes code, tests and docs, researches options, reviews changes.
- Every change goes through CI (tests, eval set, frontend build, Docker smoke test) before it counts as done.
- Commits don't carry AI co-author lines.

## Milestone 1: v0.1, a working app ✅ mostly done

- [x] Two-step pipeline: list requirements, then match the resume
- [x] Verification in code: quotes must exist in the resume; edits can't add skills; work-rights quote checked against the ad
- [x] Score and missing keywords computed in code
- [x] Providers: Claude, DeepSeek, offline demo mode
- [x] Resume upload: PDF, Word (.docx), text; or paste
- [x] English and Chinese interface; results explained in either language; Chinese-aware quote matching
- [x] Cost guards: per-visitor hourly limit, site-wide daily limit
- [x] Tests (pytest), evaluation set (4 cases), GitHub Actions, Docker image
- [x] First green CI run on GitHub (tests, eval set, frontend build, Docker smoke test)
- [x] Run the evaluation set with DeepSeek (`deepseek-flash`): 95.5% status accuracy, 100% grounded quotes, about ¥0.03 per analysis at peak
- [x] Default provider for the public site: DeepSeek (accurate enough and far cheaper)
- [ ] Run the evaluation set with Claude for comparison (needs an `ANTHROPIC_API_KEY` secret)
- [ ] Replace the demo-mode screenshots with real results

## Milestone 2: public launch / 上线

- [x] Choose a host: Render free plan to start (no card, sleeps when idle); Fly.io config kept ready for when traffic justifies a few dollars a month
- [ ] Deploy on Render and get a public URL
- [ ] Confirm the per-visitor rate limit sees real visitor IPs on Render (`True-Client-IP`)
- [ ] Keep the DeepSeek balance small (it is prepaid), since the in-memory daily limit resets whenever the free server sleeps
- [ ] Short privacy page (what is sent to the AI provider, that nothing is stored)
- [ ] Privacy-friendly usage counts (number of analyses, error rate; no content)
- [ ] 5–10 real users (classmates); collect feedback in GitHub Issues

## Milestone 3: quality / 质量

- [ ] Grow the evaluation set to 20+ cases: more roles, countries, Chinese and English, scanned-PDF edge cases
- [ ] Compare models and effort levels on cost, latency and accuracy
- [ ] Tolerate PDF hyphenation and line-break artefacts in quote matching
- [ ] Show progress while the analysis runs (stream the two steps)

## Milestone 4: more for job seekers / 更多功能

- [ ] Application tracker (which jobs, which resume version, status)
- [ ] Mock interview questions for the job, with feedback on answers
- [ ] Cover letter draft that only uses facts from the resume
- [ ] Browser extension to send a job ad from a job site to JobFit in one click

## Log / 进度记录

- **2026-10-29**: First DeepSeek evaluation run. 21/22 statuses, 32/32 quotes verified, 17s and about 5k tokens per analysis. Its only miss exposed a label that contradicted the rubric (Tableau for a Power BI requirement is partial, not missing); label fixed, demo baseline is now 68.2%.
- **2026-10-29**: Project started. Built v0.1: backend pipeline with verification, Claude/DeepSeek/demo providers, bilingual React frontend, tests, eval set, CI and Docker. Mock baseline status accuracy 72.7% (16/22).

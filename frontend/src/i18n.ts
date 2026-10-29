import type { Language } from "./types";

const en = {
  brand: "JobFit",
  sourceCode: "Source code",
  heroTitle: "See how your resume reads against a job ad",
  heroBody:
    "Paste a job ad and add your resume. You get every requirement checked, a quote from your resume for each match, and edits that never invent experience.",

  jobLabel: "Job ad",
  jobHint: "Paste the full ad, including the requirements.",
  jobPlaceholder: "Paste the job ad here",
  resumeLabel: "Your resume",
  resumeUpload: "Upload a file",
  resumePaste: "Paste text",
  dropTitle: "Drop your resume here, or choose a file",
  dropHint: "PDF, Word (.docx) or text, up to 2 MB",
  chooseFile: "Choose a file",
  removeFile: "Remove",
  resumePlaceholder: "Paste the text of your resume here",
  explainIn: "Explain results in",
  analyze: "Check my resume",
  analyzing: "Checking…",
  trySample: "Try it with a sample job ad and resume",
  privacy: "Your resume is sent to an AI service for analysis. JobFit doesn't store it.",
  privacy_deepseek: "Your resume is sent to DeepSeek's AI for analysis. JobFit doesn't store it.",
  privacy_anthropic: "Your resume is sent to Anthropic's Claude for analysis. JobFit doesn't store it.",
  privacy_mock: "Demo mode: your resume is checked on this server only and isn't stored.",

  loadingTitle: "Reading the job ad and your resume",
  loadingBody: "This usually takes under a minute.",
  elapsed: "{seconds}s",

  demoBanner:
    "Demo mode: results come from simple keyword matching, not AI. Set an API key on the server for a real analysis.",
  resultsFor: "Results for",
  metOf: "{met} of {total} requirements met",
  partialCount: "{count} partly met",
  missingCount: "{count} missing",
  stripLabel: "Each requirement, coloured by result",
  matchScore: "Match score",
  scoreHelp: "Must-haves count for 75% and nice-to-haves for 25%. Met counts fully, partly met counts half.",
  verifiedAll: "All {count} quotes the AI cited were found in your resume.",
  verifiedSome:
    "{removed} of {count} quotes the AI cited could not be found in your resume, so they were removed and not counted.",
  verifiedNone: "No quotes to check.",
  suggestionsRemoved: "{count} suggested edits were removed because they changed lines that aren't in your resume or added skills you haven't listed.",

  workRightsRequired: "This job asks for work rights you may need to check",
  workRightsPreferred: "This job prefers certain work rights",
  workRightsUnverified: "The AI's quote for this could not be found in the ad, so read the ad to confirm.",

  summary: "Summary",
  mustHaves: "Must-haves",
  niceToHaves: "Nice-to-haves",
  status_met: "Met",
  status_partial: "Partly met",
  status_missing: "Missing",
  fromResume: "From your resume",
  note_not_assessed: "The AI skipped this one, so it counts as missing.",
  note_evidence_not_found:
    "The AI said you meet this, but the quote it gave isn't in your resume, so it counts as missing.",

  keywordsTitle: "Words from the ad that your resume never uses",
  keywordsBody:
    "Recruiters and screening software often search for these exact terms. Add the ones you genuinely have.",
  suggestionsTitle: "Suggested edits",
  suggestionsBody:
    "Each edit starts from a line already in your resume. Fill in anything in [square brackets] with your real details.",
  original: "Now",
  rewrite: "Suggested",
  copy: "Copy",
  copied: "Copied",
  forRequirements: "Helps with:",
  noSuggestions: "No edits suggested for this job.",
  editInputs: "Change the job ad or resume",

  footerPrivacy: "Resumes are processed in memory and never saved.",
  footerHonesty: "JobFit only reports a match when it can show you the line in your resume that proves it.",
};

type Strings = typeof en;

const zh: Strings = {
  brand: "JobFit",
  sourceCode: "源代码",
  heroTitle: "看看你的简历，在这份职位面前表现如何",
  heroBody:
    "粘贴职位描述，再放入你的简历。每一项要求都会逐条核对，每个“符合”都附上简历原文作为依据，修改建议也绝不编造经历。",

  jobLabel: "职位描述",
  jobHint: "请粘贴完整的职位描述，包括任职要求。",
  jobPlaceholder: "在这里粘贴职位描述",
  resumeLabel: "你的简历",
  resumeUpload: "上传文件",
  resumePaste: "粘贴文字",
  dropTitle: "把简历拖到这里，或选择文件",
  dropHint: "支持 PDF、Word（.docx）或纯文本，最大 2 MB",
  chooseFile: "选择文件",
  removeFile: "移除",
  resumePlaceholder: "在这里粘贴简历的文字内容",
  explainIn: "结果说明语言",
  analyze: "开始分析",
  analyzing: "分析中…",
  trySample: "用示例职位和简历试一试",
  privacy: "简历会发送给 AI 服务进行分析，JobFit 不会保存。",
  privacy_deepseek: "简历会发送给 DeepSeek 的 AI 进行分析，JobFit 不会保存。",
  privacy_anthropic: "简历会发送给 Anthropic 的 Claude 进行分析，JobFit 不会保存。",
  privacy_mock: "演示模式：简历只在本服务器上检查，不会被保存。",

  loadingTitle: "正在阅读职位描述和你的简历",
  loadingBody: "通常不到一分钟。",
  elapsed: "{seconds} 秒",

  demoBanner: "演示模式：以下结果来自简单的关键词匹配，不是 AI 分析。在服务器上配置 API Key 后即可获得真正的分析。",
  resultsFor: "分析职位",
  metOf: "{total} 项要求中满足 {met} 项",
  partialCount: "{count} 项部分满足",
  missingCount: "{count} 项缺失",
  stripLabel: "每一项要求的结果",
  matchScore: "匹配分",
  scoreHelp: "必备要求占 75%，加分项占 25%。满足计全分，部分满足计一半。",
  verifiedAll: "AI 引用的 {count} 处简历原文都已核实存在。",
  verifiedSome: "AI 引用的 {count} 处原文中，有 {removed} 处在你的简历里找不到，已删除且不计入结果。",
  verifiedNone: "没有需要核对的引用。",
  suggestionsRemoved: "有 {count} 条修改建议被删除：它们改的句子不在你的简历里，或者加入了你简历中没有的技能。",

  workRightsRequired: "这个职位对工作身份有要求，请注意核对",
  workRightsPreferred: "这个职位对工作身份有偏好",
  workRightsUnverified: "AI 给出的原句在职位描述里找不到，请自己再读一遍职位描述确认。",

  summary: "总结",
  mustHaves: "必备要求",
  niceToHaves: "加分项",
  status_met: "满足",
  status_partial: "部分满足",
  status_missing: "缺失",
  fromResume: "简历原文",
  note_not_assessed: "AI 没有评估这一项，因此按缺失计算。",
  note_evidence_not_found: "AI 认为你满足这一项，但它引用的句子不在你的简历里，因此按缺失计算。",

  keywordsTitle: "职位描述里有、而你的简历从未出现的词",
  keywordsBody: "招聘方和筛选系统常常直接搜索这些词。确实具备的，就写进简历。",
  suggestionsTitle: "修改建议",
  suggestionsBody: "每条建议都基于你简历里已有的一句话。方括号 [ ] 里的内容请换成你的真实信息。",
  original: "原句",
  rewrite: "建议改为",
  copy: "复制",
  copied: "已复制",
  forRequirements: "对应要求：",
  noSuggestions: "这份职位暂时没有修改建议。",
  editInputs: "修改职位描述或简历",

  footerPrivacy: "简历只在内存中处理，从不保存。",
  footerHonesty: "只有能在你的简历里找到对应原句时，JobFit 才会判定“符合”。",
};

export type StringKey = keyof Strings;

const STRINGS: Record<Language, Strings> = { en, zh };

export function translate(language: Language, key: StringKey, vars: Record<string, string | number> = {}): string {
  return STRINGS[language][key].replace(/\{(\w+)\}/g, (match, name: string) =>
    name in vars ? String(vars[name]) : match,
  );
}

const ERRORS: Record<Language, Record<string, string>> = {
  en: {
    network: "Couldn't reach the server. Check your connection and try again.",
    server: "Something went wrong on the server. Please try again.",
    job_too_short: "The job ad is too short. Paste the full ad, including the requirements.",
    job_too_long: "The job ad is too long. Remove the company background and benefits, then try again.",
    resume_too_short: "The resume is too short to check.",
    resume_too_long: "The resume is too long. Keep it to the main sections and try again.",
    no_resume: "Add your resume, either as a file or as pasted text.",
    unsupported_file_type: "That file type isn't supported. Upload a PDF, a Word (.docx) file or a text file.",
    file_too_large: "The file is larger than 2 MB. Upload a smaller file or paste the text.",
    no_text_in_file: "No text could be read from this file. If it's a scanned PDF, paste the text instead.",
    unreadable_pdf: "This PDF couldn't be read. Export it again, or paste the text.",
    encrypted_pdf: "This PDF is password-protected. Upload an unlocked copy.",
    unreadable_docx: "This Word file couldn't be read. Save it again, or paste the text.",
    no_requirements: "No requirements were found in this job ad. Make sure you pasted the part that lists them.",
    rate_limited: "You've run several checks in a short time. Try again in an hour.",
    daily_limit: "Today's free checks have run out. Come back tomorrow.",
    ai_unavailable: "The AI service didn't respond. Try again in a minute.",
    ai_refused: "The AI declined to analyse this text.",
    ai_output_too_long: "The job ad and resume are too long to check together. Shorten one of them.",
    ai_bad_output: "The AI's answer came back incomplete. Try again.",
    ai_not_configured: "The server isn't set up with an AI provider yet.",
  },
  zh: {
    network: "无法连接服务器，请检查网络后重试。",
    server: "服务器出了问题，请重试。",
    job_too_short: "职位描述太短了。请粘贴完整的职位描述，包括任职要求。",
    job_too_long: "职位描述太长了。请删掉公司介绍和福利部分后重试。",
    resume_too_short: "简历内容太短，无法分析。",
    resume_too_long: "简历太长了。请只保留主要部分后重试。",
    no_resume: "请上传简历文件，或粘贴简历文字。",
    unsupported_file_type: "不支持这种文件格式。请上传 PDF、Word（.docx）或文本文件。",
    file_too_large: "文件超过 2 MB。请上传更小的文件，或直接粘贴文字。",
    no_text_in_file: "无法从文件中读取文字。如果是扫描版 PDF，请直接粘贴文字。",
    unreadable_pdf: "无法读取这个 PDF。请重新导出，或直接粘贴文字。",
    encrypted_pdf: "这个 PDF 设置了密码。请上传未加密的版本。",
    unreadable_docx: "无法读取这个 Word 文件。请重新保存，或直接粘贴文字。",
    no_requirements: "没有在职位描述中找到任何要求。请确认粘贴了列出要求的部分。",
    rate_limited: "短时间内分析次数太多了，请一小时后再试。",
    daily_limit: "今天的免费次数已用完，请明天再来。",
    ai_unavailable: "AI 服务没有响应，请稍后重试。",
    ai_refused: "AI 拒绝分析这段内容。",
    ai_output_too_long: "职位描述和简历合起来太长了，请缩短其中一份。",
    ai_bad_output: "AI 返回的结果不完整，请重试。",
    ai_not_configured: "服务器还没有配置 AI 服务。",
  },
};

export function errorMessage(language: Language, code: string, fallback: string): string {
  return ERRORS[language][code] ?? fallback;
}

export function detectLanguage(): Language {
  try {
    const saved = window.localStorage.getItem("jobfit-language");
    if (saved === "en" || saved === "zh") return saved;
  } catch {
    // Storage can be unavailable (private mode, blocked cookies); fall back to the browser language.
  }
  return navigator.language.toLowerCase().startsWith("zh") ? "zh" : "en";
}

export function saveLanguage(language: Language): void {
  try {
    window.localStorage.setItem("jobfit-language", language);
  } catch {
    // Not critical: the choice just won't be remembered.
  }
}

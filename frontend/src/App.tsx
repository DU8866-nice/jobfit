import { useEffect, useRef, useState } from "react";
import { ApiError, analyze } from "./api";
import { InputPanel } from "./components/InputPanel";
import type { ResumeMode } from "./components/InputPanel";
import { Results } from "./components/Results";
import { detectLanguage, errorMessage, saveLanguage, translate } from "./i18n";
import type { StringKey } from "./i18n";
import { sample } from "./samples";
import type { AnalysisResult, Language } from "./types";

const REPO_URL = "https://github.com/DU8866-nice/jobfit";

function prefersReducedMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

export function App() {
  const [lang, setLang] = useState<Language>(detectLanguage);
  const [outputLanguage, setOutputLanguage] = useState<Language>(lang);
  const [outputLanguageChosen, setOutputLanguageChosen] = useState(false);

  const [jobText, setJobText] = useState("");
  const [mode, setMode] = useState<ResumeMode>("file");
  const [resumeText, setResumeText] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const resultsHeading = useRef<HTMLHeadingElement>(null);
  const formTop = useRef<HTMLDivElement>(null);

  const t = (key: StringKey, vars?: Record<string, string | number>) => translate(lang, key, vars);

  useEffect(() => {
    document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    saveLanguage(lang);
  }, [lang]);

  useEffect(() => {
    if (!loading) return;
    setElapsed(0);
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000);
    return () => window.clearInterval(timer);
  }, [loading]);

  useEffect(() => {
    if (!result || !resultsHeading.current) return;
    resultsHeading.current.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth", block: "start" });
    resultsHeading.current.focus({ preventScroll: true });
  }, [result]);

  function changeLanguage(next: Language) {
    setLang(next);
    if (!outputLanguageChosen) setOutputLanguage(next);
  }

  function chooseOutputLanguage(next: Language) {
    setOutputLanguage(next);
    setOutputLanguageChosen(true);
  }

  function loadSample() {
    const { job, resume } = sample(lang);
    setJobText(job);
    setMode("text");
    setResumeText(resume);
    setFile(null);
  }

  async function submit() {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const analysis = await analyze(
        {
          jobDescription: jobText,
          resumeText: mode === "text" ? resumeText : undefined,
          resumeFile: mode === "file" ? file : null,
          language: outputLanguage,
        },
        controller.signal,
      );
      setResult(analysis);
    } catch (caught) {
      if (caught instanceof DOMException && caught.name === "AbortError") return;
      if (caught instanceof ApiError) {
        setError({ code: caught.code, message: caught.message });
      } else {
        setError({ code: "server", message: String(caught) });
      }
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  }

  function backToInputs() {
    formTop.current?.scrollIntoView({ behavior: prefersReducedMotion() ? "auto" : "smooth" });
  }

  return (
    <div className="page">
      <header className="top-bar">
        <a className="wordmark" href="/">
          <img src="/favicon.svg" alt="" width={24} height={24} />
          {t("brand")}
        </a>
        <div className="top-actions">
          <div className="language-switch" role="group" aria-label="Language / 语言">
            {(["en", "zh"] as const).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={lang === option}
                onClick={() => changeLanguage(option)}
              >
                {option === "en" ? "EN" : "中文"}
              </button>
            ))}
          </div>
          <a className="top-link" href={REPO_URL} target="_blank" rel="noreferrer">
            {t("sourceCode")}
          </a>
        </div>
      </header>

      <main>
        <div className="hero" ref={formTop}>
          <h1>{t("heroTitle")}</h1>
          <p className="hero-body">{t("heroBody")}</p>
        </div>

        <InputPanel
          lang={lang}
          jobText={jobText}
          onJobText={setJobText}
          mode={mode}
          onMode={setMode}
          resumeText={resumeText}
          onResumeText={setResumeText}
          file={file}
          onFile={setFile}
          outputLanguage={outputLanguage}
          onOutputLanguage={chooseOutputLanguage}
          loading={loading}
          onSubmit={submit}
          onSample={loadSample}
        />

        <div aria-live="polite" className="status-area">
          {loading && (
            <div className="loading">
              <span className="loading-bar" aria-hidden="true" />
              <div>
                <p className="loading-title">{t("loadingTitle")}</p>
                <p className="loading-body">
                  {t("loadingBody")} {t("elapsed", { seconds: elapsed })}
                </p>
              </div>
            </div>
          )}
          {error && !loading && (
            <p className="error-message" role="alert">
              {errorMessage(lang, error.code, error.message)}
            </p>
          )}
        </div>

        {result && <Results result={result} lang={lang} onEdit={backToInputs} headingRef={resultsHeading} />}
      </main>

      <footer className="footer">
        <p>{t("footerHonesty")}</p>
        <p>
          {t("footerPrivacy")}{" "}
          <a href={REPO_URL} target="_blank" rel="noreferrer">
            {t("sourceCode")}
          </a>
        </p>
      </footer>
    </div>
  );
}

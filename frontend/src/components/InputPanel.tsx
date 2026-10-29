import { useId, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, FormEvent } from "react";
import { errorMessage, translate } from "../i18n";
import type { StringKey } from "../i18n";
import type { Language } from "../types";

export type ResumeMode = "file" | "text";

const ACCEPTED = [".pdf", ".docx", ".txt", ".md"];
const MAX_BYTES = 2_000_000;

interface Props {
  lang: Language;
  jobText: string;
  onJobText: (value: string) => void;
  mode: ResumeMode;
  onMode: (mode: ResumeMode) => void;
  resumeText: string;
  onResumeText: (value: string) => void;
  file: File | null;
  onFile: (file: File | null) => void;
  outputLanguage: Language;
  onOutputLanguage: (value: Language) => void;
  loading: boolean;
  onSubmit: () => void;
  onSample: () => void;
}

function formatSize(bytes: number): string {
  return bytes < 1_000_000 ? `${Math.max(1, Math.round(bytes / 1000))} KB` : `${(bytes / 1_000_000).toFixed(1)} MB`;
}

export function InputPanel(props: Props) {
  const { lang } = props;
  const t = (key: StringKey) => translate(lang, key);
  const ids = { job: useId(), resume: useId(), out: useId(), drop: useId() };
  const fileInput = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [fileError, setFileError] = useState<string | null>(null);

  function acceptFile(candidate: File | undefined) {
    if (!candidate) return;
    const ext = candidate.name.slice(candidate.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setFileError(errorMessage(lang, "unsupported_file_type", ""));
      return;
    }
    if (candidate.size > MAX_BYTES) {
      setFileError(errorMessage(lang, "file_too_large", ""));
      return;
    }
    setFileError(null);
    props.onFile(candidate);
  }

  function handleFileInput(event: ChangeEvent<HTMLInputElement>) {
    acceptFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files[0]);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    props.onSubmit();
  }

  const hasResume = props.mode === "file" ? props.file !== null : props.resumeText.trim().length > 0;
  const canSubmit = !props.loading && props.jobText.trim().length > 0 && hasResume;

  return (
    <form className="input-panel" onSubmit={handleSubmit} noValidate>
      <div className="input-grid">
        <div className="field">
          <label htmlFor={ids.job} className="field-label">
            {t("jobLabel")}
          </label>
          <p className="field-hint">{t("jobHint")}</p>
          <textarea
            id={ids.job}
            className="text-area"
            value={props.jobText}
            onChange={(e) => props.onJobText(e.target.value)}
            placeholder={t("jobPlaceholder")}
            rows={16}
          />
        </div>

        <div className="field">
          <span className="field-label" id={ids.resume}>
            {t("resumeLabel")}
          </span>
          <div className="mode-switch" role="radiogroup" aria-labelledby={ids.resume}>
            {(["file", "text"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                role="radio"
                aria-checked={props.mode === mode}
                className="mode-option"
                onClick={() => props.onMode(mode)}
              >
                {t(mode === "file" ? "resumeUpload" : "resumePaste")}
              </button>
            ))}
          </div>

          {props.mode === "file" ? (
            props.file ? (
              <div className="file-chosen">
                <div>
                  <div className="file-name">{props.file.name}</div>
                  <div className="file-size">{formatSize(props.file.size)}</div>
                </div>
                <button type="button" className="text-button" onClick={() => props.onFile(null)}>
                  {t("removeFile")}
                </button>
              </div>
            ) : (
              <div
                id={ids.drop}
                className={dragging ? "drop-zone is-dragging" : "drop-zone"}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
              >
                <p className="drop-title">{t("dropTitle")}</p>
                <p className="drop-hint">{t("dropHint")}</p>
                <button type="button" className="secondary-button" onClick={() => fileInput.current?.click()}>
                  {t("chooseFile")}
                </button>
                <input
                  ref={fileInput}
                  type="file"
                  accept={ACCEPTED.join(",")}
                  onChange={handleFileInput}
                  className="visually-hidden"
                  tabIndex={-1}
                  aria-hidden="true"
                />
              </div>
            )
          ) : (
            <textarea
              aria-labelledby={ids.resume}
              className="text-area"
              value={props.resumeText}
              onChange={(e) => props.onResumeText(e.target.value)}
              placeholder={t("resumePlaceholder")}
              rows={13}
            />
          )}
          {fileError && (
            <p className="field-error" role="alert">
              {fileError}
            </p>
          )}
        </div>
      </div>

      <div className="submit-row">
        <div className="submit-main">
          <button type="submit" className="primary-button" disabled={!canSubmit}>
            {props.loading ? t("analyzing") : t("analyze")}
          </button>
          <label className="output-language" htmlFor={ids.out}>
            <span>{t("explainIn")}</span>
            <select
              id={ids.out}
              value={props.outputLanguage}
              onChange={(e) => props.onOutputLanguage(e.target.value === "zh" ? "zh" : "en")}
            >
              <option value="en">English</option>
              <option value="zh">中文</option>
            </select>
          </label>
        </div>
        <button type="button" className="text-button" onClick={props.onSample} disabled={props.loading}>
          {t("trySample")}
        </button>
      </div>
      <p className="privacy-note">{t("privacy")}</p>
    </form>
  );
}

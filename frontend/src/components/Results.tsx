import { useState } from "react";
import type { Ref } from "react";
import { translate } from "../i18n";
import type { StringKey } from "../i18n";
import type { AnalysisResult, Language, MatchStatus, RequirementReport, Suggestion } from "../types";

type T = (key: StringKey, vars?: Record<string, string | number>) => string;

const STATUS_MARK: Record<MatchStatus, string> = { met: "✓", partial: "–", missing: "✕" };

function statusLabel(t: T, status: MatchStatus): string {
  return t(`status_${status}` as StringKey);
}

function RequirementStrip({ requirements, t }: { requirements: RequirementReport[]; t: T }) {
  return (
    <ol className="strip" aria-label={t("stripLabel")}>
      {requirements.map((req, index) => (
        <li key={req.id} className="strip-item" style={{ animationDelay: `${index * 40}ms` }}>
          <a
            href={`#req-${req.id}`}
            className={`strip-segment status-${req.status} ${req.importance === "must_have" ? "is-must" : "is-nice"}`}
            title={`${req.text} (${statusLabel(t, req.status)})`}
          >
            <span className="visually-hidden">
              {req.text}: {statusLabel(t, req.status)}
            </span>
          </a>
        </li>
      ))}
    </ol>
  );
}

function RequirementItem({ req, t }: { req: RequirementReport; t: T }) {
  return (
    <li className={`requirement status-${req.status}`} id={`req-${req.id}`}>
      <div className="requirement-head">
        <span className="status-mark" aria-hidden="true">
          {STATUS_MARK[req.status]}
        </span>
        <p className="requirement-text">{req.text}</p>
        <span className="status-label">{statusLabel(t, req.status)}</span>
      </div>
      {req.evidence.length > 0 && (
        <figure className="evidence">
          <figcaption>{t("fromResume")}</figcaption>
          {req.evidence.map((quote) => (
            <blockquote key={quote}>
              <mark className="highlight">{quote}</mark>
            </blockquote>
          ))}
        </figure>
      )}
      {req.explanation && <p className="explanation">{req.explanation}</p>}
      {req.note && <p className="requirement-note">{t(`note_${req.note}` as StringKey)}</p>}
    </li>
  );
}

function withPlaceholders(text: string) {
  return text.split(/(\[[^\]]+\])/g).map((part, index) =>
    /^\[[^\]]+\]$/.test(part) ? (
      <span key={index} className="placeholder">
        {part}
      </span>
    ) : (
      part
    ),
  );
}

function SuggestionItem({
  suggestion,
  requirementText,
  t,
}: {
  suggestion: Suggestion;
  requirementText: Map<string, string>;
  t: T;
}) {
  const helpsWith = suggestion.requirement_ids
    .map((id) => requirementText.get(id))
    .filter((text): text is string => Boolean(text));
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(suggestion.rewrite);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied; the text is still visible to copy by hand.
    }
  }

  return (
    <li className="suggestion">
      {suggestion.rationale && <p className="suggestion-why">{suggestion.rationale}</p>}
      <dl className="suggestion-lines">
        <div className="suggestion-line is-original">
          <dt>{t("original")}</dt>
          <dd>{suggestion.original}</dd>
        </div>
        <div className="suggestion-line is-rewrite">
          <dt>{t("rewrite")}</dt>
          <dd>{withPlaceholders(suggestion.rewrite)}</dd>
        </div>
      </dl>
      <div className="suggestion-foot">
        {helpsWith.length > 0 ? (
          <span className="suggestion-for">
            {t("forRequirements")} {helpsWith.join("; ")}
          </span>
        ) : (
          <span />
        )}
        <button type="button" className="secondary-button small" onClick={copy}>
          {copied ? t("copied") : t("copy")}
        </button>
      </div>
    </li>
  );
}

interface Props {
  result: AnalysisResult;
  lang: Language;
  onEdit: () => void;
  headingRef: Ref<HTMLHeadingElement>;
}

export function Results({ result, lang, onEdit, headingRef }: Props) {
  const t: T = (key, vars) => translate(lang, key, vars);
  const { score, grounding, work_rights: workRights } = result;
  const total = result.requirements.length;
  const must = result.requirements.filter((r) => r.importance === "must_have");
  const nice = result.requirements.filter((r) => r.importance === "nice_to_have");
  const requirementText = new Map(result.requirements.map((r) => [r.id, r.text]));

  const kept = grounding.evidence_cited - grounding.evidence_removed;
  const verification =
    grounding.evidence_cited === 0
      ? t("verifiedNone")
      : grounding.evidence_removed === 0
        ? t("verifiedAll", { count: kept })
        : t("verifiedSome", { removed: grounding.evidence_removed, count: grounding.evidence_cited });

  return (
    <section className="results" aria-labelledby="results-heading">
      {result.provider === "mock" && <p className="demo-banner">{t("demoBanner")}</p>}

      <header className="results-head">
        <p className="results-for">
          {t("resultsFor")} <strong>{result.job_title}</strong>
          {result.company && <span className="results-company">, {result.company}</span>}
        </p>
        <h2 id="results-heading" ref={headingRef} tabIndex={-1}>
          {t("metOf", { met: score.counts.met, total })}
        </h2>
        <p className="results-counts">
          {score.counts.partial > 0 && <span>{t("partialCount", { count: score.counts.partial })}</span>}
          {score.counts.missing > 0 && <span>{t("missingCount", { count: score.counts.missing })}</span>}
        </p>
        <RequirementStrip requirements={result.requirements} t={t} />
        <div className="score-line">
          <span className="score-value">
            {t("matchScore")} <strong>{score.overall}</strong>
            <span className="score-max">/100</span>
          </span>
          <span className="score-help">{t("scoreHelp")}</span>
        </div>
        <p className={grounding.evidence_removed > 0 ? "verification has-removed" : "verification"}>
          <span className="verification-icon" aria-hidden="true">
            ✓
          </span>
          {verification}
        </p>
      </header>

      {workRights.status !== "not_mentioned" && (
        <aside className="work-rights">
          <p className="work-rights-title">
            {t(workRights.status === "required" ? "workRightsRequired" : "workRightsPreferred")}
          </p>
          {workRights.detail && <p>{workRights.detail}</p>}
          {workRights.quote && <blockquote className="ad-quote">{workRights.quote}</blockquote>}
          {workRights.quote && !workRights.quote_verified && (
            <p className="requirement-note">{t("workRightsUnverified")}</p>
          )}
        </aside>
      )}

      {result.summary && (
        <div className="summary">
          <h3>{t("summary")}</h3>
          <p>{result.summary}</p>
        </div>
      )}

      {[
        { key: "mustHaves" as const, items: must },
        { key: "niceToHaves" as const, items: nice },
      ]
        .filter((group) => group.items.length > 0)
        .map((group) => (
          <div className="requirement-group" key={group.key}>
            <h3>{t(group.key)}</h3>
            <ul className="requirement-list">
              {group.items.map((req) => (
                <RequirementItem key={req.id} req={req} t={t} />
              ))}
            </ul>
          </div>
        ))}

      {result.missing_keywords.length > 0 && (
        <div className="keywords">
          <h3>{t("keywordsTitle")}</h3>
          <p className="section-intro">{t("keywordsBody")}</p>
          <ul className="keyword-list">
            {result.missing_keywords.map((keyword) => (
              <li key={keyword}>{keyword}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="suggestions">
        <h3>{t("suggestionsTitle")}</h3>
        {result.suggestions.length > 0 ? (
          <>
            <p className="section-intro">{t("suggestionsBody")}</p>
            <ul className="suggestion-list">
              {result.suggestions.map((suggestion) => (
                <SuggestionItem
                  key={suggestion.original}
                  suggestion={suggestion}
                  requirementText={requirementText}
                  t={t}
                />
              ))}
            </ul>
          </>
        ) : (
          <p className="section-intro">{t("noSuggestions")}</p>
        )}
        {grounding.suggestions_removed > 0 && (
          <p className="requirement-note">{t("suggestionsRemoved", { count: grounding.suggestions_removed })}</p>
        )}
      </div>

      <button type="button" className="secondary-button" onClick={onEdit}>
        {t("editInputs")}
      </button>
    </section>
  );
}

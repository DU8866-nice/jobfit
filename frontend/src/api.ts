import type { AnalysisResult, ApiErrorBody, Language } from "./types";

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

export interface AnalyzeInput {
  jobDescription: string;
  resumeText?: string;
  resumeFile?: File | null;
  language: Language;
}

function isErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as ApiErrorBody).code === "string" &&
    typeof (value as ApiErrorBody).message === "string"
  );
}

export async function analyze(input: AnalyzeInput, signal?: AbortSignal): Promise<AnalysisResult> {
  const form = new FormData();
  form.append("job_description", input.jobDescription);
  form.append("language", input.language);
  if (input.resumeFile) {
    form.append("resume_file", input.resumeFile);
  } else if (input.resumeText) {
    form.append("resume_text", input.resumeText);
  }

  let response: Response;
  try {
    response = await fetch("/api/analyze", { method: "POST", body: form, signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("network", "Could not reach the server.");
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // Non-JSON body (for example a proxy error page); handled below.
  }

  if (!response.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    if (isErrorBody(detail)) throw new ApiError(detail.code, detail.message);
    throw new ApiError("server", `The server answered ${response.status}.`);
  }
  return body as AnalysisResult;
}

/** Which AI provider the server uses ("deepseek", "anthropic" or "mock"), or null if unknown. */
export async function fetchProvider(): Promise<string | null> {
  try {
    const response = await fetch("/api/health");
    if (!response.ok) return null;
    const body = (await response.json()) as { provider?: unknown };
    return typeof body.provider === "string" ? body.provider : null;
  } catch {
    return null;
  }
}

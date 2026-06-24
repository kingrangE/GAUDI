/**
 * Rich per-feature detail panels for the admin result page.
 * One panel per exam step, each tailored to its raw_result shape.
 * Uses only palette tokens and @/components/ui primitives — no raw hex.
 */

import { Badge, CodeMeta, CodePanel, Metric, Panel, SectionLabel, Table } from "@/components/ui";
import type { FeatureResult } from "@/lib/adminApi";
import { STEP_LABELS } from "@/lib/adminApi";

// ---------- Helpers ----------

function pct(n: number | undefined | null): string {
  if (n == null) return "—";
  return `${Math.round(n * 100)}%`;
}

function scoreTone(score: number): "good" | "warn" | "bad" {
  if (score >= 70) return "good";
  if (score >= 40) return "warn";
  return "bad";
}

function outcomeTone(
  outcome: string | undefined,
): "good" | "bad" | "warn" | "neutral" {
  switch (outcome) {
    case "caught":
      return "good";
    case "missed":
      return "bad";
    case "false_alarm":
      return "warn";
    case "correct_accept":
      return "neutral";
    default:
      return "neutral";
  }
}

function outcomeLabel(outcome: string | undefined): string {
  switch (outcome) {
    case "caught":
      return "탐지";
    case "missed":
      return "누락";
    case "false_alarm":
      return "오경보";
    case "correct_accept":
      return "정상수용";
    default:
      return outcome ?? "—";
  }
}

/** Shared panel shell: label in header, badge with rounded score, optional summary. */
function FeatureShell({
  featureKey,
  normalizedScore,
  summary,
  children,
}: {
  featureKey: string;
  normalizedScore: number;
  summary: string | null;
  children: React.ReactNode;
}) {
  const label = STEP_LABELS[featureKey as keyof typeof STEP_LABELS] ?? featureKey;
  return (
    <Panel className="p-5">
      <div className="mb-4 flex items-start justify-between gap-3">
        <SectionLabel>{label}</SectionLabel>
        <Badge tone={scoreTone(normalizedScore)}>{Math.round(normalizedScore)}점</Badge>
      </div>
      {summary ? (
        <p className="mb-4 text-sm leading-relaxed text-ink-soft">{summary}</p>
      ) : null}
      {children}
    </Panel>
  );
}

// ---------- context_engineering ----------

function ContextEngineeringPanel({
  feature_key,
  normalized_score,
  summary,
  raw_result: raw,
}: FeatureResult & { feature_key: "context_engineering" }) {
  const total = raw?.total ?? normalized_score;
  const scored = raw?.scored;
  const resultCount = raw?.results?.length;

  return (
    <FeatureShell featureKey={feature_key} normalizedScore={normalized_score} summary={summary}>
      {/* Metrics */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Metric label="종합 점수" value={`${Math.round(total)}`} />
        {scored != null && resultCount != null ? (
          <Metric
            label="커버 기준"
            value={`${scored}/${resultCount}`}
            hint="충족된 평가 기준 수"
          />
        ) : null}
      </div>

      {/* Criteria coverage table */}
      {raw?.results && raw.results.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">기준별 커버리지</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>기준</th>
                <th>카테고리</th>
                <th>충족</th>
                <th>근거 요약</th>
              </tr>
            </thead>
            <tbody>
              {raw.results.map((r) => (
                <tr key={r.id}>
                  <td title={r.text} className="max-w-[200px] truncate">
                    {r.text}
                  </td>
                  <td>{r.category}</td>
                  <td>
                    <Badge tone={r.covered ? "good" : "bad"}>
                      {r.covered ? "충족" : "미충족"}
                    </Badge>
                  </td>
                  <td title={r.evidence ?? undefined} className="max-w-[180px] truncate text-ink-faint">
                    {r.evidence ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}

      {/* Dimensions table */}
      {raw?.dimensions && raw.dimensions.length > 0 ? (
        <div>
          <SectionLabel className="mb-2 block">차원별 점수</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>차원</th>
                <th>점수</th>
                <th>가중치</th>
                <th>가용</th>
              </tr>
            </thead>
            <tbody>
              {raw.dimensions.map((d) => (
                <tr key={d.key}>
                  <td>{d.label}</td>
                  <td className="tabular-nums">{d.score}</td>
                  <td className="tabular-nums">{d.weight}</td>
                  <td className="tabular-nums">{d.available}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}
    </FeatureShell>
  );
}

// ---------- spec_design ----------

function SpecDesignPanel({
  feature_key,
  normalized_score,
  summary,
  raw_result: raw,
}: FeatureResult & { feature_key: "spec_design" }) {
  const score = raw?.score;
  const total = raw?.total ?? raw?.total_score ?? normalized_score;
  const grade = score?.grade;
  const failedReqs = score?.failed_requirements ?? [];
  const weakDecs = score?.weak_decisions ?? [];
  const penalty = score?.overengineering_penalty;

  return (
    <FeatureShell featureKey={feature_key} normalizedScore={normalized_score} summary={summary}>
      {/* Metrics */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric label="종합" value={`${Math.round(total)}`} />
        {score?.requirement_score != null ? (
          <Metric label="요구사항" value={`${Math.round(score.requirement_score)}`} />
        ) : null}
        {score?.decision_score != null ? (
          <Metric label="의사결정" value={`${Math.round(score.decision_score)}`} />
        ) : null}
        {grade ? (
          <Metric label="등급" value={<Badge tone="brand">{grade}</Badge>} />
        ) : null}
      </div>

      {/* Over-engineering penalty */}
      {penalty != null && penalty !== 0 ? (
        <p className="mb-4 text-sm text-warn-600">
          과설계 페널티: <strong>-{penalty}</strong>점
        </p>
      ) : null}

      {/* Requirements table */}
      {raw?.requirements && raw.requirements.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">요구사항 충족도</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>요구사항</th>
                <th>충족도</th>
                <th>판정</th>
              </tr>
            </thead>
            <tbody>
              {raw.requirements.map((r) => (
                <tr key={r.id}>
                  <td title={r.text} className="max-w-[280px] truncate">
                    {r.text}
                  </td>
                  <td className="tabular-nums">{Math.round(r.satisfaction * 100)}%</td>
                  <td>
                    <Badge tone={r.satisfied ? "good" : "bad"}>
                      {r.satisfied ? "충족" : "미충족"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}

      {/* Dimensions (decisions) table */}
      {raw?.dimensions && raw.dimensions.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">의사결정 차원</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>차원</th>
                <th>최상위 값</th>
                <th>동의율</th>
                <th>품질</th>
              </tr>
            </thead>
            <tbody>
              {raw.dimensions.map((d) => (
                <tr key={d.key}>
                  <td>{d.label}</td>
                  <td className="tabular-nums">{d.top_value ?? "—"}</td>
                  <td className="tabular-nums">
                    {d.agreement != null ? pct(d.agreement) : "—"}
                  </td>
                  <td className="tabular-nums">
                    {d.quality != null ? pct(d.quality) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}

      {/* Failed requirements chips */}
      {failedReqs.length > 0 ? (
        <div className="mb-3">
          <SectionLabel className="mb-1.5 block">실패한 요구사항</SectionLabel>
          <div className="flex flex-wrap gap-1.5">
            {failedReqs.map((req, i) => (
              <Badge key={i} tone="bad">
                {req}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {/* Weak decisions chips */}
      {weakDecs.length > 0 ? (
        <div className="mb-3">
          <SectionLabel className="mb-1.5 block">약한 의사결정</SectionLabel>
          <div className="flex flex-wrap gap-1.5">
            {weakDecs.map((dec, i) => (
              <Badge key={i} tone="warn">
                {dec}
              </Badge>
            ))}
          </div>
        </div>
      ) : null}

      {/* Feedback */}
      {score?.feedback ? (
        <div className="mt-4 rounded-lg border border-line bg-surface p-4">
          <SectionLabel className="mb-2 block">LLM 피드백</SectionLabel>
          <p className="text-sm leading-relaxed text-ink-soft">{score.feedback}</p>
        </div>
      ) : null}
    </FeatureShell>
  );
}

// ---------- rejection_eval ----------

function RejectionEvalPanel({
  feature_key,
  normalized_score,
  summary,
  raw_result: raw,
}: FeatureResult & { feature_key: "rejection_eval" }) {
  return (
    <FeatureShell featureKey={feature_key} normalizedScore={normalized_score} summary={summary}>
      {/* F1 / P / R metrics */}
      <div className="mb-5 grid grid-cols-3 gap-3">
        <Metric
          label="F1"
          value={raw?.f1 != null ? pct(raw.f1) : "—"}
          hint="균형 지표"
        />
        <Metric
          label="Precision"
          value={raw?.precision != null ? pct(raw.precision) : "—"}
          hint="정밀도"
        />
        <Metric
          label="Recall"
          value={raw?.recall != null ? pct(raw.recall) : "—"}
          hint="재현율"
        />
      </div>

      {/* Outcome ledger table */}
      {raw?.items && raw.items.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">결과 원장</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>항목</th>
                <th>결함 여부</th>
                <th>결과</th>
                <th>플래그</th>
              </tr>
            </thead>
            <tbody>
              {raw.items.map((item) => (
                <tr key={item.id}>
                  <td title={item.text} className="max-w-[240px] truncate">
                    {item.text}
                  </td>
                  <td>
                    <Badge tone={item.is_flawed ? "bad" : "neutral"}>
                      {item.is_flawed ? `결함 (${item.flaw_type ?? "?"})` : "정상"}
                    </Badge>
                  </td>
                  <td>
                    <Badge tone={outcomeTone(item.outcome)}>
                      {outcomeLabel(item.outcome)}
                    </Badge>
                  </td>
                  <td>
                    <Badge tone={item.flagged ? "warn" : "neutral"}>
                      {item.flagged ? "플래그" : "—"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}

      {/* Report */}
      {raw?.report ? (
        <div className="rounded-lg border border-line bg-surface p-4">
          <SectionLabel className="mb-2 block">LLM 보고서</SectionLabel>
          <p className="text-sm leading-relaxed text-ink-soft">{raw.report}</p>
        </div>
      ) : null}
    </FeatureShell>
  );
}

// ---------- test_design ----------

function severityTone(severity: string | undefined): "bad" | "warn" | "neutral" {
  switch (severity?.toLowerCase()) {
    case "high":
    case "critical":
      return "bad";
    case "medium":
      return "warn";
    default:
      return "neutral";
  }
}

function TestDesignPanel({
  feature_key,
  normalized_score,
  summary,
  raw_result: raw,
}: FeatureResult & { feature_key: "test_design" }) {
  const fpCount = Array.isArray(raw?.false_positives) ? raw!.false_positives.length : 0;

  return (
    <FeatureShell featureKey={feature_key} normalizedScore={normalized_score} summary={summary}>
      {/* Metrics */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          label="가중 점수"
          value={raw?.weighted_score != null ? `${Math.round(raw.weighted_score)}` : "—"}
        />
        <Metric label="Recall" value={raw?.recall != null ? pct(raw.recall) : "—"} hint="탐지율" />
        <Metric
          label="Precision"
          value={raw?.precision != null ? pct(raw.precision) : "—"}
          hint="정밀도"
        />
        <Metric
          label="평균 품질"
          value={raw?.mean_quality != null ? pct(raw.mean_quality) : "—"}
        />
      </div>

      {/* Flaws table */}
      {raw?.flaws && raw.flaws.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">결함 목록</SectionLabel>
          <Table>
            <thead>
              <tr>
                <th>결함</th>
                <th>심각도</th>
                <th>카테고리</th>
                <th>탐지</th>
                <th>품질</th>
              </tr>
            </thead>
            <tbody>
              {raw.flaws.map((flaw) => (
                <tr key={flaw.id}>
                  <td title={flaw.text} className="max-w-[220px] truncate">
                    {flaw.text}
                  </td>
                  <td>
                    <Badge tone={severityTone(flaw.severity)}>
                      {flaw.severity ?? "—"}
                    </Badge>
                  </td>
                  <td>{flaw.category ?? "—"}</td>
                  <td>
                    <Badge tone={flaw.found ? "good" : "bad"}>
                      {flaw.found ? "탐지" : "누락"}
                    </Badge>
                  </td>
                  <td className="tabular-nums">
                    {flaw.quality != null ? pct(flaw.quality) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </div>
      ) : null}

      {/* False positives count */}
      {fpCount > 0 ? (
        <p className="mb-4 text-sm text-warn-600">
          오탐지(false positive): <strong>{fpCount}건</strong>
        </p>
      ) : null}

      {/* Report */}
      {raw?.report ? (
        <div className="rounded-lg border border-line bg-surface p-4">
          <SectionLabel className="mb-2 block">LLM 보고서</SectionLabel>
          <p className="text-sm leading-relaxed text-ink-soft">{raw.report}</p>
        </div>
      ) : null}
    </FeatureShell>
  );
}

// ---------- dev_prompting ----------

function DevPromptingPanel({
  feature_key,
  normalized_score,
  summary,
  raw_result: raw,
}: FeatureResult & { feature_key: "dev_prompting" }) {
  const score = raw?.score;
  const solved = raw?.solved ?? false;

  // Pick the code to display: first solved turn, or last turn overall.
  const turns = raw?.turns ?? [];
  const solvedTurn = turns.find((t) => t.solved);
  const displayTurn = solvedTurn ?? turns[turns.length - 1];

  return (
    <FeatureShell featureKey={feature_key} normalizedScore={normalized_score} summary={summary}>
      {/* Metrics */}
      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Metric
          label="종합 점수"
          value={raw?.total != null ? pct(raw.total) : "—"}
          hint={solved ? "풀이 완료" : "미완료"}
        />
        <Metric
          label="최고 통과율"
          value={score?.best_pass_rate != null ? pct(score.best_pass_rate) : "—"}
        />
        <Metric
          label="풀이 턴"
          value={
            score?.solved_turn != null
              ? `${score.solved_turn}번`
              : solved
                ? "풀이됨"
                : "미풀이"
          }
        />
      </div>

      {/* Turn summary */}
      {turns.length > 0 ? (
        <div className="mb-5">
          <SectionLabel className="mb-2 block">턴별 결과</SectionLabel>
          <div className="grid gap-2">
            {turns.map((t) => (
              <div
                key={t.turn}
                className="flex items-start justify-between gap-4 rounded-lg border border-line bg-surface p-3"
              >
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <SectionLabel>TURN {t.turn}</SectionLabel>
                    <Badge tone={t.solved ? "good" : "neutral"}>
                      {t.solved ? "✓ 풀이" : `${t.passed_count}/${t.total}`}
                    </Badge>
                  </div>
                  {t.feedback ? (
                    <p className="text-xs leading-relaxed text-ink-faint">{t.feedback}</p>
                  ) : null}
                </div>
                <span className="shrink-0 font-mono text-kicker tabular-nums text-ink-soft">
                  {t.passed_count}/{t.total}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {/* Submitted code (dark CodePanel — the ONE dark zone for this feature) */}
      {displayTurn?.code ? (
        <CodePanel
          label="제출 코드"
          meta={
            <>
              <CodeMeta>TURN {displayTurn.turn}</CodeMeta>
              <CodeMeta>{solved ? "SOLVED" : "LAST"}</CodeMeta>
            </>
          }
          code={displayTurn.code}
        />
      ) : null}
    </FeatureShell>
  );
}

// ---------- Public dispatcher ----------

export function FeaturePanel({ feature }: { feature: FeatureResult }) {
  if (feature.feature_key === "context_engineering") return <ContextEngineeringPanel {...feature} />;
  if (feature.feature_key === "spec_design") return <SpecDesignPanel {...feature} />;
  if (feature.feature_key === "rejection_eval") return <RejectionEvalPanel {...feature} />;
  if (feature.feature_key === "test_design") return <TestDesignPanel {...feature} />;
  if (feature.feature_key === "dev_prompting") return <DevPromptingPanel {...feature} />;
  // All known keys handled above. Defensive fallback for any future feature keys.
  return null;
}

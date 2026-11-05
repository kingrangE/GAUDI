"use client";

import { useEffect, useState } from "react";
import { Badge, Panel, SectionLabel } from "@/components/ui";
import { demoFetch, isDemoEnabled } from "./session";

const LABELS: Record<string, string> = {
  context_engineering: "컨텍스트", spec_design: "명세 설계", dev_prompting: "개발 프롬프팅",
  coding_test: "코딩", cs_eval: "CS", office_prompting: "업무 프롬프팅",
  rejection_eval: "거부 능력", test_design: "테스트 설계", mock_exam: "모의고사",
};

type Usage = { limited: boolean; features: { feature: string; remaining: number; state: string }[] };

export function UsageNotice() {
  const [usage, setUsage] = useState<Usage | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!isDemoEnabled()) return;
    let active = true;
    const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
    void demoFetch(`${base}/api/demo/usage`).then(async (response) => {
      if (!response.ok) throw new Error("체험 현황을 불러오지 못했습니다.");
      const result = await response.json() as Usage;
      if (active) setUsage(result);
    }).catch((cause: unknown) => {
      if (active) setError(cause instanceof Error ? cause.message : "체험 현황을 불러오지 못했습니다.");
    });
    return () => { active = false; };
  }, []);
  if (!isDemoEnabled() || (!error && !usage?.limited)) return null;
  return (
    <Panel className="mt-6" aria-label="체험 사용 현황">
      <SectionLabel>포트폴리오 체험</SectionLabel>
      <p className="mt-2 text-sm text-ink-soft">
        자유롭게 둘러보고 원하는 기능만 선택하세요. 기능별 최대 1회이며 모두 이용할 필요는 없습니다.
        시작한 체험의 여러 단계와 개발 턴, 업무 문제별 3회 실행은 한 번의 체험에 포함됩니다.
      </p>
      {error ? <p role="alert" className="mt-2 text-sm text-bad-700">{error}</p> : (
        <ul className="mt-3 flex flex-wrap gap-2" aria-label="기능별 남은 체험">
          {usage?.features.map((item) => (
            <li key={item.feature}>
              <Badge tone={item.remaining ? "brand" : "neutral"}>
                {LABELS[item.feature] ?? item.feature}: {item.remaining ? "1회 가능" :
                  item.state === "active" ? "시작됨 · 이어서 진행" : "체험 종료"}
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}

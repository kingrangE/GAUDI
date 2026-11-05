import { Badge, Metric, Panel, SectionLabel } from "@/components/ui";

const AXES: Record<string, [string, string, string]> = {
  context_engineering: ["근거 연결", "핵심 규칙 포함", "경계 조건 안내"],
  spec_design: ["요구사항 충족", "설계 결정 품질", "출력 일관성"],
  dev_prompting: ["공개 사례 검증", "지시 구체성", "수정 과정 설명"],
  coding_test: ["테스트 통과", "코드 품질", "예외 처리"],
  cs_eval: ["개념 이해", "판단 근거", "모르는 내용 구분"],
  office_prompting: ["추출 정밀도", "조건 충족", "누락 확인"],
  rejection_eval: ["문제 발견", "오탐 구분", "거부 근거"],
  test_design: ["결함 발견", "검증 정밀도", "테스트 설명"],
};

/** Handwritten fiction, independent of evaluation banks, prompts and user records. */
export function SampleReport({ feature }: { feature?: string }) {
  const axes = AXES[feature ?? ""] ?? ["문제 이해", "검증 과정", "개선 설명"];
  return (
    <Panel className="space-y-3" aria-label="합성 샘플 리포트">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <SectionLabel>Sample Report</SectionLabel>
        <Badge tone="neutral">미리 작성한 합성 예시</Badge>
      </div>
      <p className="text-sm text-ink-soft">
        가상 사례 ‘공유 화분 관찰 기록’의 결과 형식 예시입니다.
        현재 문제의 정답이나 이번 입력의 평가 결과가 아닙니다.
      </p>
      <div className="grid grid-cols-3 gap-2">
        {axes.map((axis, i) => <Metric key={axis} label={axis} value={[84, 76, 90][i]} hint="예시 수치" />)}
      </div>
      <p className="text-sm text-ink-soft">예시 강점: 관찰 기록을 확인할 기준과 판단 근거를 명확히 설명했습니다.</p>
      <p className="text-sm text-ink-soft">예시 개선점: 기록이 비어 있는 날의 확인 절차를 더 구체적으로 정리하세요.</p>
    </Panel>
  );
}

import Link from "next/link";

type Feature = {
  href: string;
  badge: string;
  title: string;
  desc: string;
};

type Group = {
  kicker: string;
  desc: string;
  features: Feature[];
};

// 그룹 1(AI 활용 역량)의 카드 순서는 추후 실전 모의고사 흐름과 맞추기 위해 고정한다.
const GROUPS: Group[] = [
  {
    kicker: "AI 활용 역량 평가",
    desc: "AI 에이전트에게 지시를 내리고 그 출력을 검증하는 역량을 평가합니다.",
    features: [
      {
        href: "/context-engineering",
        badge: "컨텍스트",
        title: "컨텍스트 엔지니어링 평가",
        desc: "에이전트에게 필요한 컨텍스트만 정확히 골라 제공하는 역량을 측정합니다.",
      },
      {
        href: "/spec-design",
        badge: "명세 설계",
        title: "명세 설계 평가",
        desc: "요구사항을 명세로 풀어내는 설계 역량을 요구사항·결정 품질·일관성으로 평가합니다.",
      },
      {
        href: "/rejection-eval",
        badge: "거부 능력",
        title: "거부 능력 평가",
        desc: "AI가 생성한 설계안의 결함을 가려내는 능력을 정밀도·재현율로 측정합니다.",
      },
      {
        href: "/test-design",
        badge: "테스트 설계",
        title: "테스트 설계 평가",
        desc: "주어진 코드의 숨은 결함을 찾아내는 검증 역량을 발견율·정밀도로 채점합니다.",
      },
      {
        href: "/dev-prompting",
        badge: "개발 프롬프팅",
        title: "개발 프롬프팅 평가",
        desc: "AI 에이전트에게 지시를 내려 문제를 해결시키고, 프롬프트의 질을 채점합니다.",
      },
    ],
  },
  {
    kicker: "전통 개발자 역량 평가",
    desc: "직접 코드를 짜고 CS 지식의 깊이를 검증하는 전통적인 개발 역량입니다.",
    features: [
      {
        href: "/coding-test",
        badge: "코딩 테스트",
        title: "코딩 테스트",
        desc: "문제를 직접 풀고, 히든 케이스 채점과 LLM 코드 품질 분석으로 실력을 평가합니다.",
      },
      {
        href: "/cs-eval",
        badge: "CS 서술형",
        title: "CS 심층 평가",
        desc: "CS 서술형 문항에 답하면, 정확·부분·솔직한 모름·허세-오답으로 이해의 깊이와 정직함을 채점합니다.",
      },
    ],
  },
  {
    kicker: "사무직 Prompt 역량 평가",
    desc: "실무 데이터를 다루며 AI에게 프롬프트로 업무를 처리시키는 역량입니다.",
    features: [
      {
        href: "/office-prompting",
        badge: "사무직 Prompt",
        title: "데이터 분석 프롬프팅 평가",
        desc: "여러 표(CSV)를 조합해야 풀리는 문제를 AI에게 프롬프트로 지시해 해결하고, 프롬프트의 질을 채점합니다.",
      },
    ],
  },
];

export default function PracticePage() {
  return (
    <div className="py-10">
      <section>
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-600">
          개별 연습 · GAUDI
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-ink-900">
          AI Agent를 다루고 검증하는 역량을 평가합니다
        </h1>
        <p className="mt-3 max-w-3xl text-ink-soft">
          AI 활용 역량, 전통 개발자 역량, 사무직 Prompt 역량 — 세 갈래로 나눠
          LLM-as-a-judge로 측정합니다. 원하는 평가를 골라 바로 시작하세요.
        </p>
      </section>

      <div className="mt-10 space-y-10">
        {GROUPS.map((group) => (
          <section key={group.kicker}>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-600">
              {group.kicker}
            </p>
            <p className="mt-1 max-w-3xl text-sm text-ink-soft">{group.desc}</p>

            <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
              {group.features.map((f) => (
                <Link
                  key={f.href}
                  href={f.href}
                  className="group flex flex-col rounded-lg border border-line bg-surface p-5 shadow-panel transition-colors hover:border-brand-300"
                >
                  <span className="inline-flex w-fit rounded-sm border border-brand-200 px-2 py-[3px] font-mono text-[11px] uppercase tracking-[0.12em] text-brand-600">
                    {f.badge}
                  </span>
                  <h2 className="mt-3 text-lg font-semibold text-ink-900">{f.title}</h2>
                  <p className="mt-1 flex-1 text-sm text-ink-soft">{f.desc}</p>
                  <span className="mt-4 font-mono text-xs font-semibold uppercase tracking-[0.1em] text-brand-600 group-hover:text-brand-700">
                    시작하기 →
                  </span>
                </Link>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

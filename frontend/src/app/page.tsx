import Link from "next/link";

const FEATURES = [
  {
    href: "/coding-test",
    badge: "코딩 · CS",
    title: "코딩 테스트",
    desc: "문제를 직접 풀고, 히든 케이스 채점과 LLM 코드 품질 분석으로 실력을 평가합니다.",
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
];

export default function HomePage() {
  return (
    <div className="py-10">
      <section>
        <p className="text-sm font-semibold text-brand-600">AI SW 해커톤 · and you</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          AI Agent를 다루고 검증하는 역량을 평가합니다
        </h1>
        <p className="mt-3 text-slate-600">
          프롬프트 엔지니어링, 설계 명세, 컨텍스트 엔지니어링, 그리고 잘못된 AI 출력을 거부하는
          능력까지 — LLM-as-a-judge로 측정하는 세 가지 평가를 제공합니다.
        </p>
      </section>

      <div className="mt-8 grid grid-cols-3 gap-4">
        {FEATURES.map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="group flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-panel transition-colors hover:border-brand-300"
          >
            <span className="inline-flex w-fit rounded-full border border-brand-100 bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
              {f.badge}
            </span>
            <h2 className="mt-3 text-lg font-semibold text-slate-900">{f.title}</h2>
            <p className="mt-1 flex-1 text-sm text-slate-600">{f.desc}</p>
            <span className="mt-4 text-sm font-semibold text-brand-600 group-hover:text-brand-700">
              시작하기 →
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}

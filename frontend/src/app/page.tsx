import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-bold">and-you</h1>
      <p className="mt-2 text-slate-600">AI Agent 활용·검증 역량 평가 플랫폼.</p>
      <ul className="mt-6 space-y-2">
        <li>
          <Link className="text-blue-600 hover:underline" href="/coding-test">
            코딩 테스트 →
          </Link>
        </li>
        <li>
          <Link className="text-blue-600 hover:underline" href="/rejection-eval">
            거부 능력 평가 →
          </Link>
        </li>
        <li>
          <Link className="text-blue-600 hover:underline" href="/test-design">
            테스트 설계 평가 →
          </Link>
        </li>
      </ul>
    </main>
  );
}

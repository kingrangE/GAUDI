import Link from "next/link";

export default function HomePage() {
  return (
    <main>
      <h1>and-you</h1>
      <p>AI Agent 활용·검증 역량 평가 플랫폼.</p>
      <p>
        <Link href="/rejection-eval">거부 능력 평가 시작하기 →</Link>
      </p>
    </main>
  );
}

"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { createSession } from "@/features/rejection-eval/api";

export default function StartPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const session = await createSession(name.trim());
      sessionStorage.setItem(
        `reval:topics:${session.session_id}`,
        JSON.stringify(session.topics),
      );
      router.push(`/rejection-eval/${session.session_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "세션 생성 실패");
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>거부 능력 평가</h1>
      <p>
        고정 주제 3개에 대해 AI에게 설계를 지시하고, AI가 만든 설계 항목 중
        잘못된 것을 찾아내세요.
      </p>
      <label style={{ display: "block", margin: "16px 0 8px" }}>응시자 이름</label>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="이름을 입력하세요"
        style={{ padding: 8, width: "100%", maxWidth: 320 }}
      />
      <div style={{ marginTop: 16 }}>
        <button onClick={start} disabled={loading || !name.trim()}>
          {loading ? "시작 중…" : "평가 시작"}
        </button>
      </div>
      {error && <p style={{ color: "#c5221f" }}>{error}</p>}
    </main>
  );
}

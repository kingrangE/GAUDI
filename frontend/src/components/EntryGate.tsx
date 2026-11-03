"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { classifyCode, normalize, setUserCode } from "@/lib/accessCodes";
import { ensureDemoSession, isDemoEnabled } from "@/features/demo/session";

import { Button } from "./ui/Button";
import { Logo } from "./ui/Logo";

/** Login-less first screen: route to admin or user area by entry code. */
export function EntryGate() {
  const router = useRouter();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  async function enterDemo() {
    setStarting(true);
    setError(null);
    try {
      await ensureDemoSession();
      router.push("/user");
    } catch (error) {
      setError(error instanceof Error ? error.message : "체험을 시작하지 못했습니다.");
    } finally {
      setStarting(false);
    }
  }

  function submit(event: React.FormEvent) {
    event.preventDefault();
    switch (classifyCode(code)) {
      case "admin":
        router.push("/admin/login");
        return;
      case "user":
        setUserCode(normalize(code));
        router.push("/user");
        return;
      default:
        setError("유효하지 않은 코드입니다. 다시 확인해 주세요.");
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-paper px-6">
      <div className="w-full max-w-md rounded-lg border border-line bg-surface p-8 shadow-panel">
        <div className="flex items-center gap-2">
          <Logo size="sm" />
          <span className="rounded-sm border border-brand-200 px-2 py-[2px] font-mono text-[10px] tracking-[0.18em] text-brand-600">
            EVAL
          </span>
        </div>
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-ink-900">
          {isDemoEnabled() ? "GAUDI 둘러보기" : "입장 코드를 입력하세요"}
        </h1>
        <p className="mt-2 text-sm text-ink-soft">
          {isDemoEnabled()
            ? "자유롭게 둘러보고 관심 있는 평가를 선택해 보세요."
            : "발급받은 코드를 입력하면 해당 페이지로 입장합니다."}
        </p>

        {isDemoEnabled() && (
          <Button className="mt-6 w-full" onClick={enterDemo} disabled={starting}>
            {starting ? "입장 중…" : "둘러보기"}
          </Button>
        )}

        <form onSubmit={submit} className="mt-6 flex flex-col gap-3">
          <label htmlFor="entry-code" className="text-sm font-semibold text-ink-900">
            입장 코드
          </label>
          <input
            id="entry-code"
            name="entry-code"
            value={code}
            autoComplete="off"
            autoFocus
            onChange={(event) => {
              setCode(event.target.value);
              if (error) setError(null);
            }}
            placeholder="예: AY-XXXXXX"
            className="rounded-md border border-line bg-paper px-3 py-2 font-mono text-sm text-ink-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-300"
          />
          {error ? (
            <p role="alert" className="text-sm font-medium text-bad-600">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="mt-1 w-full" disabled={code.trim().length === 0}>
            입장
          </Button>
        </form>
      </div>
    </div>
  );
}

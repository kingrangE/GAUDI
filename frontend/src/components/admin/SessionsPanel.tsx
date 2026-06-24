"use client";

import { Clipboard, Play, Plus, Square } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  getSessionProgress,
  problemSets,
  sessions,
  type EvaluationSession,
} from "@/lib/adminData";

import styles from "@/app/admin/sections.module.css";

const modeLabels = {
  demo: "데모",
  pilot: "파일럿",
  official: "공식",
};

const statusLabels = {
  ready: "준비",
  running: "진행",
  closed: "종료",
};

type FormState = {
  name: string;
  problemSetId: string;
  mode: EvaluationSession["mode"];
  duration: string;
  participants: string;
};

const initialForm: FormState = {
  name: "",
  problemSetId: problemSets[0]?.id ?? "",
  mode: "demo",
  duration: "60",
  participants: "0",
};

export function SessionsPanel() {
  const [sessionList, setSessionList] = useState<EvaluationSession[]>(sessions);
  const [form, setForm] = useState<FormState>(initialForm);
  const [isLoaded, setIsLoaded] = useState(false);
  const [message, setMessage] = useState("새 세션을 생성하면 이 화면에 즉시 추가됩니다.");

  const nextId = useMemo(() => `SE-${String(sessionList.length + 1).padStart(3, "0")}`, [
    sessionList.length,
  ]);

  useEffect(() => {
    const savedSessions = window.localStorage.getItem("and-you-admin-sessions");

    if (savedSessions) {
      setSessionList(JSON.parse(savedSessions) as EvaluationSession[]);
    }

    setIsLoaded(true);
  }, []);

  useEffect(() => {
    if (isLoaded) {
      window.localStorage.setItem("and-you-admin-sessions", JSON.stringify(sessionList));
    }
  }, [isLoaded, sessionList]);

  function updateSession(id: string, update: Partial<EvaluationSession>) {
    setSessionList((currentSessions) =>
      currentSessions.map((session) =>
        session.id === id ? { ...session, ...update } : session,
      ),
    );
  }

  function createSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedName = form.name.trim() || "새 평가 세션";
    const duration = Number(form.duration) || 60;
    const participants = Number(form.participants) || 0;

    setSessionList((currentSessions) => [
      {
        id: nextId,
        name: trimmedName,
        mode: form.mode,
        participants,
        completed: 0,
        remainingMinutes: duration,
        status: "ready",
      },
      ...currentSessions,
    ]);
    setMessage(`${trimmedName} 세션이 생성되었습니다.`);
    setForm(initialForm);
  }

  async function copyInvite(session: EvaluationSession) {
    const inviteUrl = `${window.location.origin}/exam/session/${session.id}`;

    try {
      await navigator.clipboard.writeText(inviteUrl);
      setMessage(`${session.name} 응시 링크를 복사했습니다.`);
    } catch {
      setMessage(inviteUrl);
    }
  }

  return (
    <div className={styles.twoColumn}>
      <section className={styles.grid} aria-label="평가 세션 목록">
        {sessionList.map((session) => {
          const progress = getSessionProgress(session);
          return (
            <article className={styles.card} key={session.id}>
              <div className={styles.cardHeader}>
                <div>
                  <p className={styles.eyebrow}>{modeLabels[session.mode]}</p>
                  <h2>{session.name}</h2>
                </div>
                <span className={`${styles.status} ${styles[session.status]}`}>
                  {statusLabels[session.status]}
                </span>
              </div>

              <div className={styles.metaGrid}>
                <div>
                  <span>응시</span>
                  <strong>{session.participants}</strong>
                </div>
                <div>
                  <span>완료</span>
                  <strong>{session.completed}</strong>
                </div>
                <div>
                  <span>남은 시간</span>
                  <strong>{session.remainingMinutes}m</strong>
                </div>
              </div>

              <div>
                <p className={styles.muted}>진행률 {progress}%</p>
                <div className={styles.progressTrack}>
                  <div className={styles.progressFill} style={{ width: `${progress}%` }} />
                </div>
              </div>

              <div className={styles.cardActions}>
                <button
                  onClick={() => updateSession(session.id, { status: "running" })}
                  type="button"
                >
                  <Play aria-hidden="true" size={15} />
                  시작
                </button>
                <button
                  onClick={() =>
                    updateSession(session.id, {
                      completed: session.participants,
                      remainingMinutes: 0,
                      status: "closed",
                    })
                  }
                  type="button"
                >
                  <Square aria-hidden="true" size={15} />
                  종료
                </button>
                <button onClick={() => void copyInvite(session)} type="button">
                  <Clipboard aria-hidden="true" size={15} />
                  링크
                </button>
              </div>
            </article>
          );
        })}
      </section>

      <aside className={styles.grid}>
        <section className={styles.panel} aria-labelledby="create-session-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>새 평가 열기</p>
              <h2 id="create-session-title">세션 생성</h2>
            </div>
            <Plus aria-hidden="true" size={20} />
          </div>

          <form className={styles.form} onSubmit={createSession}>
            <label>
              <span>세션 이름</span>
              <input
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="예: 해커톤 본 평가"
                value={form.name}
              />
            </label>
            <label>
              <span>문제 세트</span>
              <select
                onChange={(event) => setForm({ ...form, problemSetId: event.target.value })}
                value={form.problemSetId}
              >
                {problemSets.map((set) => (
                  <option key={set.id} value={set.id}>
                    {set.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>평가 모드</span>
              <select
                onChange={(event) =>
                  setForm({ ...form, mode: event.target.value as EvaluationSession["mode"] })
                }
                value={form.mode}
              >
                <option value="demo">데모</option>
                <option value="pilot">파일럿</option>
                <option value="official">공식</option>
              </select>
            </label>
            <label>
              <span>제한 시간</span>
              <input
                min="10"
                onChange={(event) => setForm({ ...form, duration: event.target.value })}
                type="number"
                value={form.duration}
              />
            </label>
            <label>
              <span>예상 응시자</span>
              <input
                min="0"
                onChange={(event) => setForm({ ...form, participants: event.target.value })}
                type="number"
                value={form.participants}
              />
            </label>
            <button type="submit">세션 생성</button>
            <p className={styles.formMessage} aria-live="polite">
              {message}
            </p>
          </form>
        </section>

        <section className={styles.panel} aria-labelledby="demo-flow-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>데모 플로우</p>
              <h2 id="demo-flow-title">현장 운영 체크</h2>
            </div>
          </div>
          <ul className={styles.tagList}>
            <li>문제 세트 선택</li>
            <li>평가 세션 생성</li>
            <li>응시 링크 배포</li>
            <li>종료 후 결과 리포트 확인</li>
          </ul>
        </section>
      </aside>
    </div>
  );
}

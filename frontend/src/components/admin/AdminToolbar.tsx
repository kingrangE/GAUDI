"use client";

import { Bell, Search, Users } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { candidateResults, problemSets, sessions, trackDashboards } from "@/lib/adminData";

import styles from "./AdminShell.module.css";

const staticTargets = [
  { label: "대시보드", detail: "평가 현황", href: "/admin" },
  { label: "문제 세트", detail: "평가 유형 구성", href: "/admin/problem-sets" },
  { label: "평가 세션", detail: "세션 생성/운영", href: "/admin/sessions" },
  { label: "결과 리포트", detail: "응시자별 진단", href: "/admin/results" },
];

export function AdminToolbar() {
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("알림 없음");

  const targets = useMemo(
    () => [
      ...staticTargets,
      ...candidateResults.map((result) => ({
        label: result.name,
        detail: `${result.role} · ${result.totalScore}점`,
        href: `/admin/results/${result.id}`,
      })),
      ...problemSets.map((set) => ({
        label: set.name,
        detail: set.category,
        href: "/admin/problem-sets",
      })),
      ...sessions.map((session) => ({
        label: session.name,
        detail: `${session.participants}명 세션`,
        href: "/admin/sessions",
      })),
      ...trackDashboards.map((track) => ({
        label: track.name,
        detail: track.shortName,
        href: track.resultRoute,
      })),
    ],
    [],
  );

  const results = query.trim()
    ? targets
        .filter((target) => `${target.label} ${target.detail}`.includes(query.trim()))
        .slice(0, 5)
    : [];

  return (
    <div className={styles.toolbar}>
      <div className={styles.searchBox}>
        <label className={styles.search}>
          <Search aria-hidden="true" size={17} />
          <input
            aria-label="관리 항목 검색"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="응시자, 세션, 문제 세트 검색"
            value={query}
          />
        </label>
        {results.length > 0 ? (
          <div className={styles.searchResults}>
            {results.map((result) => (
              <Link href={result.href} key={`${result.href}-${result.label}`}>
                <strong>{result.label}</strong>
                <span>{result.detail}</span>
              </Link>
            ))}
          </div>
        ) : null}
      </div>
      <button
        className={styles.iconButton}
        onClick={() => setNotice(`응시자 ${candidateResults.length}명`)}
        title="응시자"
        type="button"
      >
        <Users aria-hidden="true" size={18} />
      </button>
      <button
        className={styles.iconButton}
        onClick={() => setNotice("운영 로그가 최신 상태입니다")}
        title="알림"
        type="button"
      >
        <Bell aria-hidden="true" size={18} />
      </button>
      <span className={styles.notice} aria-live="polite">
        {notice}
      </span>
    </div>
  );
}

"use client";

import { Bell, Search } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import styles from "./AdminShell.module.css";

const targets = [
  { label: "대시보드", detail: "모의고사 현황", href: "/admin" },
  { label: "결과 리포트", detail: "응시자별 진단", href: "/admin/results" },
];

export function AdminToolbar() {
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("알림 없음");

  const results = useMemo(() => {
    const q = query.trim();
    if (!q) return [];
    return targets
      .filter((target) => `${target.label} ${target.detail}`.includes(q))
      .slice(0, 5);
  }, [query]);

  return (
    <div className={styles.toolbar}>
      <div className={styles.searchBox}>
        <label className={styles.search}>
          <Search aria-hidden="true" size={17} />
          <input
            aria-label="관리 메뉴 검색"
            onChange={(event) => setQuery(event.target.value)}
            placeholder="메뉴 검색"
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

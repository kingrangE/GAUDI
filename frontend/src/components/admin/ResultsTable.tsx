"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import {
  formatScore,
  formatTime,
  sortAttempts,
  statusLabel,
  type AttemptSort,
  type AttemptSummary,
} from "@/lib/adminApi";

import styles from "@/app/admin/sections.module.css";

type SortField = "time" | "score";

function nextSort(currentSort: AttemptSort, field: SortField): AttemptSort {
  if (field === "time") {
    return currentSort === "time-desc" ? "time-asc" : "time-desc";
  }

  return currentSort === "score-desc" ? "score-asc" : "score-desc";
}

function SortIcon({ active, sort }: { active: boolean; sort: AttemptSort }) {
  if (!active) {
    return <ArrowUpDown aria-hidden="true" size={14} />;
  }

  return sort.endsWith("asc") ? (
    <ArrowUp aria-hidden="true" size={14} />
  ) : (
    <ArrowDown aria-hidden="true" size={14} />
  );
}

export function ResultsTable({ attempts }: { attempts: AttemptSummary[] }) {
  const [sort, setSort] = useState<AttemptSort>("score-desc");
  const sorted = useMemo(() => sortAttempts(attempts, sort), [attempts, sort]);

  if (attempts.length === 0) {
    return <p className={styles.muted}>아직 모의고사 응시 결과가 없습니다.</p>;
  }

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>순위</th>
            <th>응시자</th>
            <th>상태</th>
            <th>
              <button
                className={styles.sortButton}
                onClick={() => setSort((currentSort) => nextSort(currentSort, "time"))}
                type="button"
              >
                완료 시간
                <SortIcon active={sort.startsWith("time")} sort={sort} />
              </button>
            </th>
            <th>
              <button
                className={styles.sortButton}
                onClick={() => setSort((currentSort) => nextSort(currentSort, "score"))}
                type="button"
              >
                종합 점수
                <SortIcon active={sort.startsWith("score")} sort={sort} />
              </button>
            </th>
            <th>기능 수</th>
            <th>상세</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((attempt, index) => (
            <tr key={attempt.id}>
              <td>{index + 1}</td>
              <td>{attempt.candidate_label}</td>
              <td>{statusLabel(attempt.status)}</td>
              <td>{formatTime(attempt.completed_at)}</td>
              <td>{formatScore(attempt.overall_normalized)}</td>
              <td>{attempt.feature_count}</td>
              <td>
                <Link className={styles.link} href={`/admin/results/${attempt.id}`}>
                  리포트 보기
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

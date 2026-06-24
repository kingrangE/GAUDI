"use client";

import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { candidateResults, sortCandidateResults } from "@/lib/adminData";

import styles from "@/app/admin/sections.module.css";

type ResultSort = "score-desc" | "score-asc" | "time-desc" | "time-asc";
type SortField = "time" | "score";

function nextSort(currentSort: ResultSort, field: SortField): ResultSort {
  if (field === "time") {
    return currentSort === "time-desc" ? "time-asc" : "time-desc";
  }

  return currentSort === "score-desc" ? "score-asc" : "score-desc";
}

function SortIcon({ active, sort }: { active: boolean; sort: ResultSort }) {
  if (!active) {
    return <ArrowUpDown aria-hidden="true" size={14} />;
  }

  return sort.endsWith("asc") ? (
    <ArrowUp aria-hidden="true" size={14} />
  ) : (
    <ArrowDown aria-hidden="true" size={14} />
  );
}

export function ResultsTable() {
  const [sort, setSort] = useState<ResultSort>("score-desc");
  const sortedResults = useMemo(() => sortCandidateResults(candidateResults, sort), [sort]);

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>순위</th>
            <th>응시자</th>
            <th>역할</th>
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
            <th>강점</th>
            <th>보완 필요</th>
            <th>상세</th>
          </tr>
        </thead>
        <tbody>
          {sortedResults.map((result, index) => (
            <tr key={result.id}>
              <td>{index + 1}</td>
              <td>{result.name}</td>
              <td>{result.role}</td>
              <td>{result.completedAt}</td>
              <td>{result.totalScore}</td>
              <td>{result.strengths.join(", ")}</td>
              <td>{result.weaknesses.join(", ")}</td>
              <td>
                <Link className={styles.link} href={`/admin/results/${result.id}`}>
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

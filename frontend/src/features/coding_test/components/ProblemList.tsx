"use client";

import Link from "next/link";

import { useProblems } from "../queries";

export function ProblemList() {
  const { data, isPending, isError } = useProblems();

  if (isPending) return <p className="text-slate-500">불러오는 중…</p>;
  if (isError || !data) return <p className="text-red-600">문제를 불러오지 못했습니다.</p>;

  return (
    <ul className="divide-y rounded border bg-white">
      {data.map((problem) => (
        <li key={problem.id}>
          <Link
            href={`/coding-test/${problem.id}`}
            className="flex items-center justify-between p-4 hover:bg-slate-50"
          >
            <span className="font-medium">{problem.title}</span>
            <span className="text-xs uppercase text-slate-500">{problem.difficulty}</span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

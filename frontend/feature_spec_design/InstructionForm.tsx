import type { FormEvent } from "react";

import styles from "./spec_design.module.css";

interface InstructionFormProps {
  brief: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

const PLACEHOLDER =
  "예) 회원 테이블 PK는 UUID, 비밀번호는 bcrypt로 해시, 인증은 JWT를 HttpOnly 쿠키로 …";

export function InstructionForm({ brief, value, onChange, onSubmit, loading }: InstructionFormProps) {
  const canSubmit = value.trim().length > 0 && !loading;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSubmit) onSubmit();
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className={styles.kicker}>과제</div>
      <p className={styles.brief}>{brief}</p>
      <div className={styles.kicker} style={{ marginTop: 16 }}>
        당신의 지시
      </div>
      <textarea
        className={styles.instructionInput}
        aria-label="지시 입력"
        placeholder={PLACEHOLDER}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <div className={styles.row}>
        <button type="submit" className={styles.btn} disabled={!canSubmit}>
          {loading ? "평가 중…" : "지시 평가"}
        </button>
      </div>
    </form>
  );
}

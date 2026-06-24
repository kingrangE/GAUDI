import type { ChangeEvent } from "react";

interface Props {
  flaws: string[];
  onChange: (flaws: string[]) => void;
}

export function FlawListInput({ flaws, onChange }: Props) {
  const updateAt = (i: number, value: string) =>
    onChange(flaws.map((f, idx) => (idx === i ? value : f)));
  const addOne = () => onChange([...flaws, ""]);
  const removeAt = (i: number) => onChange(flaws.filter((_, idx) => idx !== i));

  return (
    <div className="space-y-2">
      {flaws.map((flaw, i) => (
        <div className="flex items-center gap-2" key={i}>
          <input
            type="text"
            value={flaw}
            placeholder={`검증 항목 ${i + 1}`}
            aria-label={`검증 항목 ${i + 1}`}
            onChange={(e: ChangeEvent<HTMLInputElement>) => updateAt(i, e.target.value)}
            className="flex-1 rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
          />
          <button
            type="button"
            aria-label={`검증 항목 ${i + 1} 삭제`}
            onClick={() => removeAt(i)}
            className="rounded-lg px-2 py-1 text-sm text-ink-faint hover:text-bad-600"
          >
            삭제
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={addOne}
        className="text-sm font-medium text-brand-600 hover:text-brand-700"
      >
        + 검증 항목 추가
      </button>
    </div>
  );
}

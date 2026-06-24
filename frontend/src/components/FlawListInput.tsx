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
    <div>
      {flaws.map((flaw, i) => (
        <div className="row" key={i} style={{ marginBottom: "0.5rem" }}>
          <input
            type="text"
            value={flaw}
            placeholder={`발견한 결함 ${i + 1}`}
            aria-label={`발견한 결함 ${i + 1}`}
            onChange={(e: ChangeEvent<HTMLInputElement>) => updateAt(i, e.target.value)}
          />
          <button type="button" aria-label={`결함 ${i + 1} 삭제`} onClick={() => removeAt(i)}>
            삭제
          </button>
        </div>
      ))}
      <button type="button" onClick={addOne}>
        + 결함 추가
      </button>
    </div>
  );
}

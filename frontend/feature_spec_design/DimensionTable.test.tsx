import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { makeDimension } from "./fixtures";
import { DimensionTable } from "./DimensionTable";

describe("DimensionTable", () => {
  it("orders rows worst-score first and shows choice, agreement, status", () => {
    const dimensions = [
      makeDimension({
        key: "fw",
        label: "언어/프레임워크",
        top_value: "fastapi",
        agreement: 1,
        quality: "good",
        quality_score: 1,
        score: 1,
      }),
      makeDimension({
        key: "pw",
        label: "비밀번호 저장 방식",
        top_value: "md5",
        agreement: 1,
        quality: "bad",
        quality_score: 0,
        score: 0,
      }),
      makeDimension({
        key: "tok",
        label: "토큰 위치",
        top_value: "unspecified",
        agreement: 0.4,
        quality: "unspecified",
        quality_score: 0,
        score: 0,
        diverged: true,
      }),
    ];

    render(<DimensionTable dimensions={dimensions} />);
    const rows = screen.getAllByRole("row").slice(1);

    expect(rows[0]).toHaveTextContent("비밀번호 저장 방식");
    expect(rows[0]).toHaveTextContent("md5");
    expect(rows[0]).toHaveTextContent("위험"); // pinned bad
    expect(rows[1]).toHaveTextContent("토큰 위치");
    expect(rows[1]).toHaveTextContent("갈림"); // diverged
    expect(rows[2]).toHaveTextContent("언어/프레임워크");
    expect(rows[2]).toHaveTextContent("좋음");
  });
});

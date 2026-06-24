import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FlawListInput } from "./FlawListInput";

describe("FlawListInput", () => {
  it("appends an empty item on add", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={["a"]} onChange={onChange} />);
    fireEvent.click(screen.getByText("+ 검증 항목 추가"));
    expect(onChange).toHaveBeenCalledWith(["a", ""]);
  });

  it("edits the item at its index", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={[""]} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("검증 항목 1"), { target: { value: "x" } });
    expect(onChange).toHaveBeenCalledWith(["x"]);
  });

  it("removes the item at its index", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={["a", "b"]} onChange={onChange} />);
    fireEvent.click(screen.getByLabelText("검증 항목 1 삭제"));
    expect(onChange).toHaveBeenCalledWith(["b"]);
  });
});

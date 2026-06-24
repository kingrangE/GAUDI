import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { FlawListInput } from "./FlawListInput";

describe("FlawListInput", () => {
  it("appends an empty flaw on add", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={["a"]} onChange={onChange} />);
    fireEvent.click(screen.getByText("+ 결함 추가"));
    expect(onChange).toHaveBeenCalledWith(["a", ""]);
  });

  it("edits the flaw at its index", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={[""]} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText("발견한 결함 1"), { target: { value: "x" } });
    expect(onChange).toHaveBeenCalledWith(["x"]);
  });

  it("removes the flaw at its index", () => {
    const onChange = vi.fn();
    render(<FlawListInput flaws={["a", "b"]} onChange={onChange} />);
    fireEvent.click(screen.getByLabelText("결함 1 삭제"));
    expect(onChange).toHaveBeenCalledWith(["b"]);
  });
});

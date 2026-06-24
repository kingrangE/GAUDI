import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { InstructionForm } from "./InstructionForm";

describe("InstructionForm", () => {
  it("disables submit until the instruction is non-empty", () => {
    const { rerender } = render(
      <InstructionForm brief="과제 설명" value="  " onChange={() => {}} onSubmit={() => {}} loading={false} />,
    );
    expect(screen.getByText("과제 설명")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "지시 평가" })).toBeDisabled();

    rerender(
      <InstructionForm brief="과제 설명" value="FastAPI" onChange={() => {}} onSubmit={() => {}} loading={false} />,
    );
    expect(screen.getByRole("button", { name: "지시 평가" })).toBeEnabled();
  });

  it("calls onChange while typing and onSubmit on submit", () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    render(
      <InstructionForm brief="b" value="FastAPI" onChange={onChange} onSubmit={onSubmit} loading={false} />,
    );
    fireEvent.change(screen.getByLabelText("지시 입력"), { target: { value: "x" } });
    expect(onChange).toHaveBeenCalledWith("x");
    fireEvent.click(screen.getByRole("button", { name: "지시 평가" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("shows a running label and stays disabled while loading", () => {
    render(
      <InstructionForm brief="b" value="FastAPI" onChange={() => {}} onSubmit={() => {}} loading={true} />,
    );
    expect(screen.getByRole("button", { name: "평가 중…" })).toBeDisabled();
  });
});

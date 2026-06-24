import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SAMPLE_TASKS } from "./fixtures";
import { TaskPicker } from "./TaskPicker";

describe("TaskPicker", () => {
  it("renders tasks and marks the selected one as pressed", () => {
    render(<TaskPicker tasks={SAMPLE_TASKS} selectedId="login-signup" onSelect={() => {}} />);
    expect(screen.getByText("로그인 / 회원가입 기능 구현")).toBeInTheDocument();
    expect(screen.getByText("설계 결정 5개 평가")).toBeInTheDocument();
    expect(screen.getByRole("button", { pressed: true })).toHaveTextContent(
      "로그인 / 회원가입 기능 구현",
    );
  });

  it("fires onSelect with the clicked task id", () => {
    const onSelect = vi.fn();
    render(<TaskPicker tasks={SAMPLE_TASKS} selectedId={null} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("파일 업로드 API 구현"));
    expect(onSelect).toHaveBeenCalledWith("file-upload-api");
  });

  it("shows a loading hint when there are no tasks yet", () => {
    render(<TaskPicker tasks={[]} selectedId={null} onSelect={() => {}} />);
    expect(screen.getByText(/불러오는 중/)).toBeInTheDocument();
  });
});

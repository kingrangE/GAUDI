import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import type { PublicItem, TopicMeta } from "./types";
import { RejectionWorkbench } from "./RejectionWorkbench";

// next/navigation is used inside the workbench (router.push) — mock it so
// jsdom doesn't fail on the import.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const examTopic: TopicMeta = {
  index: 0,
  title: "CX 이탈 레이더",
  description: "고객 이탈 예측 시스템",
  requirements: ["실시간 이탈 예측", "알림 발송"],
};

const fakeItems: PublicItem[] = [
  { id: "i1", text: "배치 처리 파이프라인 설계" },
  { id: "i2", text: "실시간 스트리밍 엔진 구축" },
];

describe("RejectionWorkbench — exam mode", () => {
  it("calls onExamGenerate, renders returned items, then calls onExamSubmit on submit", async () => {
    const onExamGenerate = vi.fn().mockResolvedValue(fakeItems);
    const onExamSubmit = vi.fn().mockResolvedValue(undefined);

    render(
      <RejectionWorkbench
        examMode
        examTopic={examTopic}
        onExamGenerate={onExamGenerate}
        onExamSubmit={onExamSubmit}
      />,
    );

    // Topic picker must NOT appear in exam mode
    expect(screen.queryByLabelText("주제 선택")).toBeNull();

    // Exam topic title should be visible
    expect(screen.getByText("CX 이탈 레이더")).toBeInTheDocument();

    // Type a prompt and click generate
    const textarea = screen.getByPlaceholderText(/요구사항을 만족하도록/);
    fireEvent.change(textarea, { target: { value: "이탈 예측 설계해줘" } });
    fireEvent.click(screen.getByRole("button", { name: /AI 설계 생성/ }));

    // onExamGenerate must be called with the prompt
    await waitFor(() =>
      expect(onExamGenerate).toHaveBeenCalledWith("이탈 예측 설계해줘"),
    );

    // Both items from the response must render
    await waitFor(() =>
      expect(screen.getByText("배치 처리 파이프라인 설계")).toBeInTheDocument(),
    );
    expect(screen.getByText("실시간 스트리밍 엔진 구축")).toBeInTheDocument();

    // No score/채점 button visible at this stage
    expect(screen.queryByRole("button", { name: /채점/ })).toBeNull();

    // Submit
    fireEvent.click(screen.getByRole("button", { name: /제출/ }));

    await waitFor(() =>
      expect(onExamSubmit).toHaveBeenCalledWith([]),
    );

    // After submit: "제출 완료" text shown; score button still absent; no navigation
    await waitFor(() =>
      expect(screen.getByText("제출 완료")).toBeInTheDocument(),
    );
    expect(screen.queryByRole("button", { name: /채점/ })).toBeNull();
  });
});

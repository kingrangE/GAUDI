import { render, screen } from "@testing-library/react";

import type { ResultTopic } from "../types";
import { ScorePanel } from "./ScorePanel";

const topic: ResultTopic = {
  topic_index: 0,
  topic_title: "로그인 / 회원가입 기능",
  prompt: "...",
  items: [],
  precision: 1.0,
  recall: 0.333,
  f1: 0.5,
  report: "잘 찾았으나 일부 놓침",
};

describe("ScorePanel", () => {
  it("shows the F1 score, verdict, and precision/recall", () => {
    render(<ScorePanel topic={topic} />);
    expect(screen.getByText("50")).toBeTruthy(); // F1 * 100
    expect(screen.getByText("보통")).toBeTruthy(); // verdict for F1=0.5
    expect(screen.getByText("100%")).toBeTruthy(); // precision
    expect(screen.getByText("33%")).toBeTruthy(); // recall
    expect(screen.getByText("잘 찾았으나 일부 놓침")).toBeTruthy(); // report
  });
});

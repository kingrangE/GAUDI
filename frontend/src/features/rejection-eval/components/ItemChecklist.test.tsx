import { fireEvent, render, screen } from "@testing-library/react";

import type { PublicItem } from "../types";
import { ItemChecklist } from "./ItemChecklist";

const items: PublicItem[] = [
  { id: "a", text: "decision a" },
  { id: "b", text: "decision b" },
];

describe("ItemChecklist", () => {
  it("toggles an item by calling onToggle with its id", () => {
    const onToggle = vi.fn();
    render(<ItemChecklist items={items} flagged={[]} onToggle={onToggle} />);
    const boxes = screen.getAllByRole("checkbox");
    fireEvent.click(boxes[1]);
    expect(onToggle).toHaveBeenCalledWith("b");
  });

  it("reflects the flagged state as checked", () => {
    const onToggle = vi.fn();
    render(<ItemChecklist items={items} flagged={["a"]} onToggle={onToggle} />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes[0].checked).toBe(true);
    expect(boxes[1].checked).toBe(false);
  });
});

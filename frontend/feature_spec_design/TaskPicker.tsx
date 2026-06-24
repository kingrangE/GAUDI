import type { TaskPublic } from "./types";
import styles from "./spec_design.module.css";

interface TaskPickerProps {
  tasks: TaskPublic[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function TaskPicker({ tasks, selectedId, onSelect }: TaskPickerProps) {
  if (tasks.length === 0) {
    return <p className={styles.muted}>과제를 불러오는 중…</p>;
  }
  return (
    <div className={styles.taskList}>
      {tasks.map((task) => (
        <button
          key={task.id}
          type="button"
          className={styles.taskButton}
          aria-pressed={task.id === selectedId}
          onClick={() => onSelect(task.id)}
        >
          <div className={styles.taskTitle}>{task.title}</div>
          <div className={styles.taskSub}>설계 결정 {task.dimension_count}개 평가</div>
        </button>
      ))}
    </div>
  );
}

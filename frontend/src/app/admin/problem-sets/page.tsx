import { FileStack } from "lucide-react";

import { AdminShell } from "@/components/admin/AdminShell";
import { problemSets } from "@/lib/adminData";

import styles from "../sections.module.css";

export const dynamic = "force-dynamic";

const statusLabels = {
  draft: "초안",
  ready: "준비",
  running: "진행",
};

export default function ProblemSetsPage() {
  return (
    <AdminShell active="problem-sets" eyebrow="평가 유형 구성" title="문제 세트 관리">
      <div className={styles.twoColumn}>
        <section className={styles.panel} aria-labelledby="sets-title">
          <div className={styles.panelHeader}>
            <div>
              <p className={styles.eyebrow}>세트 목록</p>
              <h2 id="sets-title">평가 트랙</h2>
            </div>
            <FileStack aria-hidden="true" size={20} />
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>세트 ID</th>
                  <th>이름</th>
                  <th>유형</th>
                  <th>담당</th>
                  <th>문항</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {problemSets.map((set) => (
                  <tr key={set.id}>
                    <td>{set.id}</td>
                    <td>{set.name}</td>
                    <td>{set.category}</td>
                    <td>{set.owner}</td>
                    <td>{set.itemCount}</td>
                    <td>
                      <span className={`${styles.status} ${styles[set.status]}`}>
                        {statusLabels[set.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className={styles.grid}>
          {problemSets.map((set) => (
            <article className={styles.card} key={set.id}>
              <div className={styles.cardHeader}>
                <div>
                  <p className={styles.eyebrow}>{set.category}</p>
                  <h3>{set.name}</h3>
                </div>
                <span className={`${styles.status} ${styles[set.status]}`}>
                  {statusLabels[set.status]}
                </span>
              </div>
              <p className={styles.muted}>{set.primaryMetric}</p>
              <div className={styles.metaGrid}>
                <div>
                  <span>담당</span>
                  <strong>{set.owner}</strong>
                </div>
                <div>
                  <span>문항</span>
                  <strong>{set.itemCount}</strong>
                </div>
                <div>
                  <span>상태</span>
                  <strong>{statusLabels[set.status]}</strong>
                </div>
              </div>
            </article>
          ))}
        </aside>
      </div>
    </AdminShell>
  );
}

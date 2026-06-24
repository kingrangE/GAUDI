import { buildTree, type TreeNode } from "./tree";
import type { Project } from "./types";
import styles from "./workspace.module.css";

interface ProjectPaneProps {
  project: Project;
  selectedPath: string | null;
  onSelect: (node: TreeNode) => void;
}

interface BranchProps {
  nodes: TreeNode[];
  selectedPath: string | null;
  onSelect: (node: TreeNode) => void;
  root?: boolean;
}

function TreeBranch({ nodes, selectedPath, onSelect, root = false }: BranchProps) {
  return (
    <ul className={root ? styles.treeRoot : styles.treeChildren}>
      {nodes.map((node) =>
        node.kind === "dir" ? (
          <li key={node.path}>
            <span className={styles.dirRow}>{node.name}/</span>
            <TreeBranch nodes={node.children} selectedPath={selectedPath} onSelect={onSelect} />
          </li>
        ) : (
          <li key={node.path}>
            <button
              type="button"
              className={
                node.path === selectedPath ? `${styles.file} ${styles.fileActive}` : styles.file
              }
              aria-pressed={node.path === selectedPath}
              onClick={() => onSelect(node)}
            >
              {node.name}
            </button>
          </li>
        ),
      )}
    </ul>
  );
}

export function ProjectPane({ project, selectedPath, onSelect }: ProjectPaneProps) {
  const tree = buildTree(project.files);
  const fileCount = project.files.filter((f) => f.kind === "file").length;
  const dirCount = project.files.filter((f) => f.kind === "dir").length;

  return (
    <section className={styles.project} aria-label="프로젝트">
      <div className={styles.kicker}>PROJECT · {project.id}</div>
      <h1 className={styles.projectTitle}>{project.title}</h1>
      <div className={styles.meta}>
        <span>파일 {fileCount}</span>
        <span>디렉토리 {dirCount}</span>
      </div>
      <p className={styles.brief}>{project.brief}</p>
      <div className={styles.constraints}>
        <div className={styles.kicker}>FILE TREE</div>
        <nav className={styles.tree} aria-label="디렉토리 트리">
          <TreeBranch nodes={tree} selectedPath={selectedPath} onSelect={onSelect} root />
        </nav>
      </div>
    </section>
  );
}

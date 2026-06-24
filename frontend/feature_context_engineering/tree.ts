// Build a nested tree from the backend's flat (path-sorted) file list.
// The backend already emits directory nodes, sorted so a parent precedes its children.

import type { FileNode } from "./types";

export interface TreeNode {
  name: string;
  path: string;
  kind: "file" | "dir";
  content: string | null;
  children: TreeNode[];
}

export function buildTree(files: FileNode[]): TreeNode[] {
  const roots: TreeNode[] = [];
  const byPath = new Map<string, TreeNode>();
  const sorted = [...files].sort((a, b) => a.path.localeCompare(b.path));

  for (const file of sorted) {
    const node: TreeNode = {
      name: file.path.split("/").pop() ?? file.path,
      path: file.path,
      kind: file.kind,
      content: file.content,
      children: [],
    };
    byPath.set(file.path, node);

    const slash = file.path.lastIndexOf("/");
    const parent = slash >= 0 ? byPath.get(file.path.slice(0, slash)) : undefined;
    if (parent) {
      parent.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}

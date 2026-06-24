"use client";

import { python } from "@codemirror/lang-python";
import CodeMirror from "@uiw/react-codemirror";

export function CodeEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <CodeMirror
      value={value}
      height="100%"
      extensions={[python()]}
      onChange={onChange}
      basicSetup={{ lineNumbers: true }}
    />
  );
}

export default CodeEditor;

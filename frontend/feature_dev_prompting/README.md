# feature_dev_prompting (UI)

개발 프롬프팅(알고리즘 이해) 평가의 프론트엔드. 백엔드 `backend/feature_dev_prompting`의
`/dev-prompting` API와만 통신하며, **클라이언트에서 LLM을 직접 호출하지 않는다.**

## 화면 구성 (3-pane)

| 좌 | 중앙 | 우 |
|---|---|---|
| 문제(제목·설명·제약·예제 수) | 에이전트가 생성한 **읽기 전용** 코드 | 지시 프롬프트 + 채점 실행 + 채점 결과(verdict) |

응시자는 코드를 직접 수정할 수 없고, 우측에서 에이전트에게 지시만 한다. "채점 실행"을 누르면
지금까지의 프롬프트가 백엔드로 전송되어 멀티턴으로 코드 생성→샌드박스 실행→채점되고, 최신 턴의
코드와 테스트 통과 현황(AC/WA/TLE/RE)이 표시된다. 숨김 케이스는 통과 여부만 노출된다.

## 모듈

- `Workspace.tsx` — 상태/오케스트레이션(client). `ProblemPane` · `CodePane` · `PromptPane`(+`VerdictLedger`).
- `api.ts` — `fetchProblem`, `runEvaluation`. base URL은 `NEXT_PUBLIC_API_BASE`(기본 `http://localhost:8000`).
- `types.ts` — 백엔드 응답 모델 미러. `verdict.ts` — status→판정(AC/WA/TLE/RE) 매핑.
- `workspace.module.css` — 스타일(모노스페이스 기반 judge 콘솔 톤, 단일 강조색).
- `Workspace.test.tsx` — colocated Vitest(테스트에서 `fetch` 목킹).

## 조립 (assembly, 나중에)

라우트는 아직 `app/`에 마운트하지 않았다. 조립 시 라우트 파일에서 마운트:

```tsx
// app/dev-prompting/page.tsx
import { Workspace } from "@/feature_dev_prompting"; // 또는 상대경로

export default function Page() {
  return <Workspace problemId="sum-array" />;
}
```

서버에서 문제를 미리 받아 `initialProblem`으로 넘기면 클라이언트 fetch를 생략할 수 있다.

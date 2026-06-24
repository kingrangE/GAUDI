import { Workspace } from "../../../feature_dev_prompting";
import type { ProblemPublic } from "../../../feature_dev_prompting";

// Demo problem so the page renders standalone. During real assembly, fetch this
// from the backend (or pass it server-side) instead of hardcoding.
const demoProblem: ProblemPublic = {
  id: "stepping-stones",
  title: "징검다리 건너기",
  statement:
    "개울에 징검다리가 한 줄로 놓여 있고, 각 디딤돌에 적힌 숫자가 리스트 stones에 " +
    "순서대로 주어집니다. 친구들이 한 명씩 디딤돌을 밟고 개울을 건너는데, 누군가 " +
    "디딤돌을 밟을 때마다 그 디딤돌의 숫자가 1씩 줄어듭니다. 숫자가 0인 디딤돌은 밟을 " +
    "수 없습니다.\n\n" +
    "각 친구는 밟을 수 있는 디딤돌이 나올 때까지 앞으로 건너뛸 수 있지만, 밟을 수 " +
    "없는(0인) 디딤돌이 연속으로 k개 나오면 그 친구는 더 건너지 못하고 멈춥니다.\n\n" +
    "친구들이 차례로 건널 때, 무사히 건널 수 있는 친구의 최대 수를 return 하도록 " +
    "solution 함수를 완성하세요.",
  constraints: "1 <= len(stones) <= 200000, 1 <= 각 숫자 <= 200000000, 1 <= k <= len(stones)",
  entry_point: "solution",
  starter_code: "def solution(stones, k):\n    answer = 0\n    return answer\n",
  time_limit_sec: 2,
  examples: [{ args: [[2, 4, 5, 3, 2, 1, 4, 2, 5, 1], 3], expected: 3 }],
  public_example_count: 1,
};

export default function Page() {
  return <Workspace problemId="stepping-stones" initialProblem={demoProblem} />;
}

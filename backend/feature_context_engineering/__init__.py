"""컨텍스트 엔지니어링 (context-engineering) 평가 기능.

응시자에게 샘플 프로젝트(디렉토리 트리 + 파일 내용 + 짧은 설명)를 제공하고, 그 프로젝트용
CLAUDE.md를 서술형으로 작성하게 받아 저장한다. 채점은 별도 트랙(SPEC.md §5)이며, 본 기능은
ContextScorer seam만 제공한다.
"""

from feature_context_engineering.service import (
    create_submission,
    evaluate,
    get_project,
    list_projects,
)

__all__ = ["create_submission", "evaluate", "get_project", "list_projects"]

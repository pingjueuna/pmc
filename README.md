# PM 역량인증 문항개발 멀티 에이전트 MVP

PM 역량인증용 필기 문항을 자동 생성/검수/예측/분석하는 멀티 에이전트 예제입니다.

## 지원 파이프라인

1. 문항 생성 (`ItemGeneratorAgent`)
2. 자체 검수 (`InternalQAAgent`)
3. 외부 LLM 검수 모사 (`ExternalLLMReviewAgent`)
4. 이슈 기반 문항 업데이트 (`ItemRevisionAgent`)
5. 페르소나 기반 예상 오답률 추정 (`PersonaSimulationAgent`, `ErrorRatePredictorAgent`)
6. 실제 오답률 대비 편차 계산 (`PostExamAnalyticsAgent`)
7. 편차 기반 페르소나 가중치 업데이트 (`PersonaUpdaterAgent`)

## 실행단(Execution Layer)

실행단은 `ExecutionRunner`가 담당하며, 각 단계를 순서대로 실행하면서 단계별 메트릭/소요시간을 수집합니다.

- `generate_items`
- `internal_review`
- `external_review`
- `revise_items`
- `persona_simulation`
- `predict_wrong_rate`
- `compare_actuals`
- `update_personas`

코드 위치:
- `src/pmc_multi_agent/execution.py`

## 실행 방법

설치 없이 바로 실행:

```bash
PYTHONPATH=src python -m pmc_multi_agent.cli
```

실행단 로그까지 같이 보기:

```bash
PYTHONPATH=src python -m pmc_multi_agent.cli --show-stages
```

실제 오답률 입력 예시:

```bash
PYTHONPATH=src python -m pmc_multi_agent.cli --actual '{"PM-001":0.5,"PM-002":0.42,"PM-003":0.61}' --show-stages
```

## 실행 화면(웹 대시보드)

터미널이 아니라 브라우저 화면에서 단계 결과를 보고 싶다면:

```bash
PYTHONPATH=src python -m pmc_multi_agent.cli --dashboard
```

브라우저에서 `http://127.0.0.1:8000` 접속하면,
- 오답률 입력
- 단계별 실행 시간 테이블
- 원본 JSON
을 한 화면에서 확인할 수 있습니다.

## 구조

- `src/pmc_multi_agent/agents.py`: 에이전트 구현
- `src/pmc_multi_agent/workflow.py`: 오케스트레이션
- `src/pmc_multi_agent/execution.py`: 실행단(단계별 실행/계측)
- `src/pmc_multi_agent/ui.py`: 웹 대시보드 서버
- `src/pmc_multi_agent/models.py`: 데이터 모델
- `tests/test_workflow.py`: 핵심 동작 테스트

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

## 실행

```bash
python -m pmc_multi_agent.cli
```

또는 설치 후:

```bash
pmc-multi-agent
```

실제 오답률 입력 예시:

```bash
python -m pmc_multi_agent.cli --actual '{"PM-001":0.5,"PM-002":0.42,"PM-003":0.61}'
```

## 구조

- `src/pmc_multi_agent/agents.py`: 에이전트 구현
- `src/pmc_multi_agent/workflow.py`: 오케스트레이션
- `src/pmc_multi_agent/models.py`: 데이터 모델
- `tests/test_workflow.py`: 핵심 동작 테스트

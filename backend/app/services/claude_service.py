"""Claude Agent SDK를 활용한 문항 생성 서비스 (별도 API 키 불필요)"""
import json
import re
import asyncio
from typing import Optional
from .item_bank_service import format_item_bank_for_prompt
from .similarity_service import filter_duplicates


GENERATION_INSTRUCTIONS = """당신은 LG SW PM 시험 문항 생성 전문가입니다.
아래 조건에 맞는 객관식 문항을 PMBOK® Guide (6th/7th), Agile Practice Guide 기반으로 생성하세요.

## 난이도별 기준
### 하
- 오답률 목표: 60% / 단일 정답 / 4지선다 / 개념형+절차형
- 지문: 200~400자, 1~2개 개념

### 중
- 오답률 목표: 80% / 단일 정답 / 4지선다 / 절차형+판단형
- 지문: 400~800자, 복합 변수 2개 이상

### 상
- 오답률 목표: 98% / 복수 정답 2개 / 5지선다 / 판단형+통합형
- 지문: 600~1500자, 복합 변수 5개 이상

## 보기 설계
- 정답: PMBOK 개념에 충실, 명확하고 타당
- 오답: 즉시 배제 가능한 극단적 표현 금지, 부분적 사실 포함으로 변별력 강화

## 예상 오답률 산출
정보밀도(30%) + 보기변별력(40%) + 이론의존도(30%) 가중평균 (각 1~5점 척도)

## 오답 유형 Tag
개념오해 / 절차혼동 / 실무직관 / 부분정답 / 단일관점

## 정답 번호 분산
- 상(복수): 1,3 / 2,5 / 3,4 / 1,5 / 2,4
- 중(단일): 1/2/3/4 순환
- 하(단일): 2/3/1/4 순환

## 출제 전 필수 점검 (하나라도 해당하면 재작성)
1. 개념·정의 암기만으로 해결 가능한가?
2. PMBOK 없이 풀 수 있는가?
3. 하나의 관리 요소만으로 정답 도출 가능한가?
4. 상식만으로 판단 가능한가?

## 출력 형식
반드시 아래 JSON 배열만 출력하세요. 다른 텍스트 없이 JSON만:
```json
[
  {
    "competency": "역량명",
    "competency_no": "역량번호",
    "sub_goal": "세부역량 수행목표",
    "difficulty": "하/중/상",
    "methodology": "Waterfall/Agile",
    "title": "문항 제목",
    "question_type": "개념형/절차형/판단형/통합형",
    "expected_wrong_rate": "예상오답률%",
    "wrong_type_tag": "오답유형태그",
    "question_text": "문제 지문",
    "choice1": "① 보기1",
    "choice2": "② 보기2",
    "choice3": "③ 보기3",
    "choice4": "④ 보기4",
    "choice5": "⑤ 보기5 또는 N.A",
    "answer": "정답번호(복수시 1,3 형식)",
    "explanation": "정답 해설",
    "education_module": "출제 기준 교육 모듈",
    "reference": "참고 문서 및 기준",
    "validation_result": "검증 결과"
  }
]
```
"""


def build_prompt(
    competency_no: str,
    competency_info: Optional[dict],
    difficulty_spec: str,
    methodology: str,
    count: int,
    item_bank_context: str,
) -> str:
    comp_section = ""
    if competency_info:
        comp_section = f"""
## 역량 정보
- 역량번호: {competency_info.get('competency_no', competency_no)}
- 역량명: {competency_info.get('competency', '')}
- 세부역량 수행목표: {competency_info.get('sub_goal', '')}
- 수행 프로세스: {competency_info.get('process', '')}
- 결과물: {competency_info.get('output', '')}
"""
    else:
        comp_section = f"""
## 역량 정보
- 역량번호: {competency_no}
- (역량 정의서 미로드 - 역량번호 기반으로 PMBOK 지식 활용)
"""

    return f"""{GENERATION_INSTRUCTIONS}

{comp_section}

## 생성 요청
- 난이도: {difficulty_spec}
- 방법론: {methodology}
- 생성 수: 총 {count}개

## 중복 방지용 기존 문항 참고
{item_bank_context}

위 조건에 맞는 문항을 JSON 배열로만 출력하세요.
- Agile: 스프린트, 백로그, 스크럼, 반복주기 포함
- Waterfall: WBS, 계획 기반 프로세스, 변경관리 포함
- 상 난이도: 반드시 복수 정답(2개) + 5지선다
"""


async def generate_questions(
    competency_no: str,
    competency_info: Optional[dict],
    difficulty_spec: str,
    methodology: str,
    count: int,
) -> list[dict]:
    """Claude Agent SDK로 문항 생성 + TF-IDF 유사도 기반 중복 검사"""
    item_bank_context = format_item_bank_for_prompt(limit=20)

    questions = await _run_generation(
        competency_no=competency_no,
        competency_info=competency_info,
        difficulty_spec=difficulty_spec,
        methodology=methodology,
        count=count,
        item_bank_context=item_bank_context,
    )

    # 중복 검사 + 재생성 (최대 2회 추가 시도)
    passed, duplicates = filter_duplicates(questions)

    if duplicates:
        print(f"[중복] {len(duplicates)}개 중복 감지, 재생성 시도...")
        for attempt in range(2):
            if not duplicates:
                break
            retry_count = len(duplicates)
            retry_questions = await _run_generation(
                competency_no=competency_no,
                competency_info=competency_info,
                difficulty_spec=difficulty_spec,
                methodology=methodology,
                count=retry_count,
                item_bank_context=item_bank_context + "\n\n※ 아래 문항과 유사한 내용은 반드시 피하세요:\n" +
                    "\n".join(f"- {d.get('question_text', '')[:100]}" for d in duplicates),
            )
            new_passed, duplicates = filter_duplicates(retry_questions)
            passed.extend(new_passed)
            print(f"[재생성 {attempt+1}회] 통과: {len(new_passed)}개, 여전히 중복: {len(duplicates)}개")

    return passed


async def _run_generation(
    competency_no: str,
    competency_info: Optional[dict],
    difficulty_spec: str,
    methodology: str,
    count: int,
    item_bank_context: str,
) -> list[dict]:
    """실제 Claude 호출 및 결과 파싱 (내부 공통 함수)"""
    import subprocess
    import sys
    import os
    import tempfile
    import concurrent.futures

    prompt = build_prompt(
        competency_no=competency_no,
        competency_info=competency_info,
        difficulty_spec=difficulty_spec,
        methodology=methodology,
        count=count,
        item_bank_context=item_bank_context,
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(prompt)
        prompt_file = f.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        result_file = f.name

    runner_script_content = f"""import os, sys, asyncio
os.environ.pop('CLAUDECODE', None)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

async def run():
    with open({repr(prompt_file)}, 'r', encoding='utf-8') as f:
        prompt = f.read()
    result = ""
    async for msg in query(prompt=prompt, options=ClaudeAgentOptions(max_turns=3)):
        if isinstance(msg, ResultMessage):
            result = msg.result
            break
    with open({repr(result_file)}, 'w', encoding='utf-8') as f:
        f.write(result)

asyncio.run(run())
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(runner_script_content)
        runner_file = f.name

    env = os.environ.copy()
    env.pop('CLAUDECODE', None)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'

    def run_subprocess():
        return subprocess.run(
            [sys.executable, runner_file],
            env=env,
            capture_output=True,
            timeout=180,
        )

    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        proc_result = await asyncio.wait_for(
            loop.run_in_executor(pool, run_subprocess),
            timeout=200,
        )

    try:
        os.unlink(runner_file)
    except Exception:
        pass

    if proc_result.returncode != 0:
        err = proc_result.stderr.decode('utf-8', errors='replace')
        raise RuntimeError(f"문항 생성 프로세스 오류: {err[:1000]}")

    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_text = f.read()
    finally:
        for fp in [prompt_file, result_file]:
            try:
                os.unlink(fp)
            except Exception:
                pass

    return _parse_json_response(result_text)


def _parse_json_response(text: str) -> list[dict]:
    if not text:
        return []

    # 코드블록 제거
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()

    # JSON 배열 추출
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
    except json.JSONDecodeError:
        pass

    return []

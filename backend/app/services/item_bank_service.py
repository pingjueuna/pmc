"""기존 문항 Bank에서 중복 검증을 수행하는 서비스"""
import pandas as pd
from pathlib import Path
from ..config import DATA_DIR, ITEM_BANK_FILE

_item_bank_cache: list = []


def _load_item_bank() -> list:
    global _item_bank_cache
    if _item_bank_cache:
        return _item_bank_cache

    file_path = DATA_DIR / ITEM_BANK_FILE
    if not file_path.exists():
        return []

    try:
        df = pd.read_excel(file_path, sheet_name=None)
        items = []

        for sheet_name, sheet_df in df.items():
            sheet_df = sheet_df.dropna(how='all')
            for _, row in sheet_df.iterrows():
                row_dict = row.to_dict()
                question_text = _get_field(row_dict, ['문제', '문항', '지문', 'Question'])
                if question_text:
                    items.append({
                        'question': question_text,
                        'answer': _get_field(row_dict, ['정답', '정답번호', 'Answer']),
                        'competency_no': _get_field(row_dict, ['역량NO', '역량번호', 'CompetencyNo']),
                        'difficulty': _get_field(row_dict, ['난이도', 'Difficulty']),
                        'raw': row_dict,
                    })

        _item_bank_cache = items
        return items

    except Exception as e:
        print(f"문항 Bank 로드 오류: {e}")
        return []


def _get_field(row_dict: dict, keys: list) -> str:
    for key in keys:
        if key in row_dict and pd.notna(row_dict[key]):
            return str(row_dict[key]).strip()
    return ""


def get_item_bank_summary() -> dict:
    items = _load_item_bank()
    return {
        "total": len(items),
        "loaded": len(items) > 0,
        "file_exists": (DATA_DIR / ITEM_BANK_FILE).exists(),
    }


def format_item_bank_for_prompt(limit: int = 50) -> str:
    """Claude 프롬프트에 포함할 기존 문항 요약 텍스트 생성"""
    items = _load_item_bank()
    if not items:
        return "기존 문항 Bank 없음 (파일 미로드)"

    lines = [f"기존 문항 Bank (총 {len(items)}개 중 {min(limit, len(items))}개 샘플):"]
    for i, item in enumerate(items[:limit]):
        lines.append(f"\n[기존문항 {i+1}]")
        lines.append(f"역량NO: {item['competency_no']}")
        lines.append(f"난이도: {item['difficulty']}")
        lines.append(f"문제: {item['question'][:200]}...")

    return "\n".join(lines)


def reload_item_bank():
    global _item_bank_cache
    _item_bank_cache = []
    return _load_item_bank()

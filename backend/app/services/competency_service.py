"""LG SW PM 역량 정의서 Excel 파일을 파싱하여 역량 정보를 조회하는 서비스"""
import pandas as pd
from pathlib import Path
from typing import Optional
from ..config import DATA_DIR, COMPETENCY_FILE

_competency_cache: dict = {}


def _load_competency_data() -> dict:
    """역량 정의서 Excel을 읽어 딕셔너리로 반환 (캐싱)"""
    global _competency_cache
    if _competency_cache:
        return _competency_cache

    file_path = DATA_DIR / COMPETENCY_FILE
    if not file_path.exists():
        return {}

    try:
        df = pd.read_excel(file_path, sheet_name=None)
        competency_map = {}

        for sheet_name, sheet_df in df.items():
            sheet_df.columns = [str(c).strip() for c in sheet_df.columns]
            sheet_df = sheet_df.dropna(how='all')

            for _, row in sheet_df.iterrows():
                row_dict = row.to_dict()
                # 역량번호 컬럼 탐색 (다양한 컬럼명 대응)
                comp_no = None
                for key in ['역량번호', '역량NO', '번호', 'NO', 'No', 'ID']:
                    if key in row_dict and pd.notna(row_dict[key]):
                        comp_no = str(row_dict[key]).strip()
                        break

                if comp_no and comp_no.startswith('LG'):
                    competency_map[comp_no] = {
                        'competency_no': comp_no,
                        'competency': _get_field(row_dict, ['역량', '역량명', 'Competency']),
                        'sub_goal': _get_field(row_dict, ['세부역량 수행목표', '수행목표', '목표']),
                        'process': _get_field(row_dict, ['수행 프로세스', '프로세스', 'Process']),
                        'output': _get_field(row_dict, ['결과물', '산출물', 'Output']),
                        'expected_level': _get_field(row_dict, ['기대수준', '수준']),
                    }

        _competency_cache = competency_map
        return competency_map

    except Exception as e:
        print(f"역량 정의서 로드 오류: {e}")
        return {}


def _get_field(row_dict: dict, keys: list) -> str:
    for key in keys:
        if key in row_dict and pd.notna(row_dict[key]):
            return str(row_dict[key]).strip()
    return ""


def get_competency(competency_no: str) -> Optional[dict]:
    """역량번호로 역량 정보 조회"""
    data = _load_competency_data()
    return data.get(competency_no.strip())


def list_competencies() -> list:
    """전체 역량 목록 반환"""
    data = _load_competency_data()
    return list(data.values())


def reload_competency_data():
    """캐시 초기화 후 재로드"""
    global _competency_cache
    _competency_cache = {}
    return _load_competency_data()


def is_competency_file_loaded() -> bool:
    file_path = DATA_DIR / COMPETENCY_FILE
    return file_path.exists()

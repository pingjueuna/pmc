"""TF-IDF 코사인 유사도 기반 문항 중복 검사 서비스"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

DUPLICATE_THRESHOLD = 0.70  # 70% 이상이면 중복으로 판정


def _normalize(text: str) -> str:
    """공백/특수문자 정규화"""
    import re
    text = re.sub(r'\s+', ' ', text or '')
    return text.strip()


def check_similarity(new_question_text: str, existing_texts: list[str]) -> dict:
    """
    새 문항과 기존 문항 목록 간 최대 유사도 계산
    Returns: {"max_score": float, "is_duplicate": bool, "matched_index": int}
    """
    if not existing_texts or not new_question_text.strip():
        return {"max_score": 0.0, "is_duplicate": False, "matched_index": -1}

    corpus = [_normalize(t) for t in existing_texts]
    query = _normalize(new_question_text)

    try:
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',  # 한국어에 적합한 문자 n-gram
            ngram_range=(2, 4),
            min_df=1,
        )
        all_texts = corpus + [query]
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        query_vec = tfidf_matrix[-1]
        corpus_matrix = tfidf_matrix[:-1]

        scores = cosine_similarity(query_vec, corpus_matrix)[0]
        max_idx = int(np.argmax(scores))
        max_score = float(scores[max_idx])

        return {
            "max_score": round(max_score, 4),
            "is_duplicate": max_score >= DUPLICATE_THRESHOLD,
            "matched_index": max_idx if max_score >= DUPLICATE_THRESHOLD else -1,
        }
    except Exception as e:
        print(f"유사도 계산 오류: {e}")
        return {"max_score": 0.0, "is_duplicate": False, "matched_index": -1}


def get_all_existing_texts() -> list[str]:
    """DB 문항 + Item Bank 파일의 모든 문항 지문 수집"""
    texts = []

    # 1. DB에 저장된 생성 문항
    try:
        from ..database import SessionLocal, Question
        db = SessionLocal()
        try:
            rows = db.query(Question.question_text).all()
            texts.extend([r[0] for r in rows if r[0]])
        finally:
            db.close()
    except Exception as e:
        print(f"DB 문항 로드 오류: {e}")

    # 2. Item Bank 파일 문항
    try:
        from .item_bank_service import _load_item_bank
        items = _load_item_bank()
        texts.extend([item['question'] for item in items if item.get('question')])
    except Exception as e:
        print(f"Item Bank 로드 오류: {e}")

    return texts


def filter_duplicates(questions: list[dict], max_retries: int = 0) -> tuple[list[dict], list[dict]]:
    """
    생성된 문항 목록에서 중복 제거
    Returns: (통과 문항 목록, 중복 문항 목록)
    """
    existing_texts = get_all_existing_texts()
    passed = []
    duplicates = []

    for q in questions:
        q_text = q.get('question_text', '')
        # 이미 통과한 문항들도 비교 대상에 추가 (배치 내 중복 방지)
        compare_texts = existing_texts + [p['question_text'] for p in passed]

        result = check_similarity(q_text, compare_texts)
        q['_similarity_score'] = result['max_score']
        q['_is_duplicate'] = result['is_duplicate']

        if result['is_duplicate']:
            duplicates.append(q)
            print(f"[중복 감지] 유사도 {result['max_score']:.1%} - {q.get('title', '')[:40]}")
        else:
            passed.append(q)
            print(f"[통과] 유사도 {result['max_score']:.1%} - {q.get('title', '')[:40]}")

    return passed, duplicates

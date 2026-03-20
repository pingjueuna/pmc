"""시험 결과 업로드 및 분석 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import json
import io
from ..database import get_db, ExamResult

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/upload")
async def upload_exam_results(
    file: UploadFile = File(...),
    exam_name: str = "시험결과",
    db: Session = Depends(get_db),
):
    """시험 결과 Excel/CSV 업로드 및 분석"""
    suffix = file.filename.split(".")[-1].lower()
    content = await file.read()

    try:
        if suffix == "csv":
            df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
        elif suffix in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="CSV 또는 Excel 파일만 지원합니다.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"파일 파싱 오류: {str(e)}")

    analysis = _analyze_exam_results(df)

    # DB 저장
    exam_result = ExamResult(
        exam_name=exam_name,
        total_questions=analysis.get("total_questions", 0),
        total_participants=analysis.get("total_participants", 0),
        avg_score=analysis.get("avg_score", 0.0),
        pass_rate=analysis.get("pass_rate", 0.0),
        raw_data=json.dumps(df.to_dict(orient="records"), ensure_ascii=False),
        analysis_result=json.dumps(analysis, ensure_ascii=False),
    )
    db.add(exam_result)
    db.commit()
    db.refresh(exam_result)

    return {"success": True, "exam_id": exam_result.id, "analysis": analysis}


@router.get("/list")
def list_exam_results(db: Session = Depends(get_db)):
    results = db.query(ExamResult).order_by(ExamResult.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "exam_name": r.exam_name,
            "total_questions": r.total_questions,
            "total_participants": r.total_participants,
            "avg_score": r.avg_score,
            "pass_rate": r.pass_rate,
            "created_at": r.created_at.isoformat(),
        }
        for r in results
    ]


@router.get("/{exam_id}")
def get_exam_analysis(exam_id: int, db: Session = Depends(get_db)):
    result = db.query(ExamResult).filter(ExamResult.id == exam_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="시험 결과를 찾을 수 없습니다.")
    return {
        "id": result.id,
        "exam_name": result.exam_name,
        "analysis": json.loads(result.analysis_result),
        "created_at": result.created_at.isoformat(),
    }


def _analyze_exam_results(df: pd.DataFrame) -> dict:
    """시험 결과 데이터 분석"""
    analysis = {
        "total_participants": len(df),
        "columns": list(df.columns),
    }

    # 점수 컬럼 탐색
    score_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if any(k in col_lower for k in ["점수", "score", "총점", "total"]):
            score_col = col
            break

    if score_col:
        scores = pd.to_numeric(df[score_col], errors="coerce").dropna()
        max_score = scores.max()
        pass_threshold = max_score * 0.6  # 60% 합격 기준

        analysis.update({
            "total_questions": int(max_score) if max_score <= 200 else 0,
            "avg_score": round(float(scores.mean()), 2),
            "max_score": float(max_score),
            "min_score": float(scores.min()),
            "std_score": round(float(scores.std()), 2),
            "pass_threshold": float(pass_threshold),
            "pass_count": int((scores >= pass_threshold).sum()),
            "fail_count": int((scores < pass_threshold).sum()),
            "pass_rate": round(float((scores >= pass_threshold).mean() * 100), 1),
            "score_distribution": _get_distribution(scores),
        })
    else:
        analysis["warning"] = "점수 컬럼을 찾을 수 없습니다. 컬럼명에 '점수', 'score', '총점'을 포함해주세요."

    # 문항별 정답률 분석
    question_cols = [c for c in df.columns if str(c).startswith(("Q", "문항", "q"))]
    if question_cols:
        question_analysis = []
        for col in question_cols[:50]:  # 최대 50문항
            col_data = df[col].dropna()
            if len(col_data) > 0:
                # 정답을 1 또는 O로 가정
                correct_rate = float((col_data.isin([1, "1", "O", "o", "정답", True])).mean() * 100)
                question_analysis.append({
                    "question": str(col),
                    "correct_rate": round(correct_rate, 1),
                    "wrong_rate": round(100 - correct_rate, 1),
                })
        analysis["question_analysis"] = question_analysis

    return analysis


def _get_distribution(scores: pd.Series) -> list:
    bins = [0, 40, 50, 60, 70, 80, 90, 100, float("inf")]
    labels = ["~40", "41-50", "51-60", "61-70", "71-80", "81-90", "91-100", "100+"]
    dist = []
    for i, label in enumerate(labels):
        count = int(((scores >= bins[i]) & (scores < bins[i + 1])).sum())
        dist.append({"range": label, "count": count})
    return dist

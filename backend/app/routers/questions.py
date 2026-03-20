"""문항 생성 및 관리 API"""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from ..database import get_db, Question
from ..services.competency_service import get_competency, is_competency_file_loaded
from ..services.claude_service import generate_questions
from ..services.export_service import export_questions_to_excel
import json

router = APIRouter(prefix="/api/questions", tags=["questions"])


class GenerateRequest(BaseModel):
    competency_no: str
    difficulty_spec: str          # 예: "하 2, 중 2, 상 1" 또는 "중"
    methodology: str              # "Waterfall" 또는 "Agile"
    count: int = 1
    confirm_mapping: bool = False # 사전 확인 단계 스킵 여부


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    question_text: Optional[str] = None
    choice1: Optional[str] = None
    choice2: Optional[str] = None
    choice3: Optional[str] = None
    choice4: Optional[str] = None
    choice5: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    status: Optional[str] = None


@router.post("/preview-mapping")
async def preview_competency_mapping(competency_no: str):
    """역량번호 사전 매핑 결과 확인 (문항 생성 전 검증 단계)"""
    competency_info = get_competency(competency_no)

    if not competency_info:
        if not is_competency_file_loaded():
            return {
                "found": False,
                "message": "역량 정의서 파일이 로드되지 않았습니다. 파일을 먼저 업로드해주세요.",
                "competency_no": competency_no,
            }
        return {
            "found": False,
            "message": f"역량번호 '{competency_no}'을 찾을 수 없습니다.",
            "competency_no": competency_no,
        }

    return {
        "found": True,
        "competency_no": competency_info.get("competency_no"),
        "competency": competency_info.get("competency"),
        "sub_goal": competency_info.get("sub_goal"),
        "process": competency_info.get("process"),
        "output": competency_info.get("output"),
        "message": "매핑 정보가 정확한가요? 확인 후 문항 생성을 진행하세요.",
    }


@router.post("/generate")
async def generate(request: GenerateRequest, db: Session = Depends(get_db)):
    """문항 생성"""
    competency_info = get_competency(request.competency_no)

    # 난이도 스펙 파싱 및 총 문항수 계산
    total_count = _parse_difficulty_count(request.difficulty_spec, request.count)

    try:
        questions = await generate_questions(
            competency_no=request.competency_no,
            competency_info=competency_info,
            difficulty_spec=request.difficulty_spec,
            methodology=request.methodology,
            count=total_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문항 생성 오류: {str(e)}")

    if not questions:
        raise HTTPException(status_code=500, detail="문항이 생성되지 않았습니다.")

    # DB 저장
    saved_ids = []
    for q in questions:
        db_question = Question(
            competency=q.get("competency", ""),
            competency_no=q.get("competency_no", request.competency_no),
            sub_goal=q.get("sub_goal", ""),
            difficulty=q.get("difficulty", ""),
            methodology=q.get("methodology", request.methodology),
            title=q.get("title", ""),
            question_type=q.get("question_type", ""),
            expected_wrong_rate=q.get("expected_wrong_rate", ""),
            wrong_type_tag=q.get("wrong_type_tag", ""),
            question_text=q.get("question_text", ""),
            choice1=q.get("choice1", ""),
            choice2=q.get("choice2", ""),
            choice3=q.get("choice3", ""),
            choice4=q.get("choice4", ""),
            choice5=q.get("choice5", ""),
            answer=q.get("answer", ""),
            explanation=q.get("explanation", ""),
            education_module=q.get("education_module", ""),
            reference=q.get("reference", ""),
            validation_result=q.get("validation_result", ""),
            status="draft",
        )
        db.add(db_question)
        db.flush()
        saved_ids.append(db_question.id)
        q["id"] = db_question.id

    db.commit()

    return {
        "success": True,
        "count": len(questions),
        "questions": questions,
        "competency_info": competency_info,
    }


@router.get("/list")
def list_questions(
    status: Optional[str] = None,
    competency_no: Optional[str] = None,
    difficulty: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """문항 목록 조회"""
    query = db.query(Question)
    if status:
        query = query.filter(Question.status == status)
    if competency_no:
        query = query.filter(Question.competency_no == competency_no)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    total = query.count()
    questions = query.order_by(Question.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "questions": [_question_to_dict(q) for q in questions],
    }


@router.get("/{question_id}")
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문항을 찾을 수 없습니다.")
    return _question_to_dict(q)


@router.put("/{question_id}")
def update_question(question_id: int, update: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문항을 찾을 수 없습니다.")

    for field, value in update.dict(exclude_none=True).items():
        setattr(q, field, value)
    db.commit()
    return _question_to_dict(q)


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="문항을 찾을 수 없습니다.")
    db.delete(q)
    db.commit()
    return {"success": True}


@router.post("/export")
def export_questions(question_ids: List[int], db: Session = Depends(get_db)):
    """선택한 문항들을 Excel로 내보내기"""
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    if not questions:
        raise HTTPException(status_code=404, detail="선택한 문항이 없습니다.")

    question_dicts = [_question_to_dict(q) for q in questions]
    excel_bytes = export_questions_to_excel(question_dicts)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=questions.xlsx"},
    )


@router.post("/export-all")
def export_all_questions(db: Session = Depends(get_db)):
    """전체 문항 Excel 내보내기"""
    questions = db.query(Question).order_by(Question.created_at.desc()).all()
    if not questions:
        raise HTTPException(status_code=404, detail="저장된 문항이 없습니다.")

    question_dicts = [_question_to_dict(q) for q in questions]
    excel_bytes = export_questions_to_excel(question_dicts)

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=all_questions.xlsx"},
    )


def _parse_difficulty_count(difficulty_spec: str, default_count: int) -> int:
    """난이도 스펙에서 총 문항 수 계산"""
    import re
    total = 0
    matches = re.findall(r'[하중상]\s*(\d+)', difficulty_spec)
    for m in matches:
        total += int(m)
    return total if total > 0 else default_count


def _question_to_dict(q: Question) -> dict:
    return {
        "id": q.id,
        "competency": q.competency,
        "competency_no": q.competency_no,
        "sub_goal": q.sub_goal,
        "difficulty": q.difficulty,
        "methodology": q.methodology,
        "title": q.title,
        "question_type": q.question_type,
        "expected_wrong_rate": q.expected_wrong_rate,
        "wrong_type_tag": q.wrong_type_tag,
        "question_text": q.question_text,
        "choice1": q.choice1,
        "choice2": q.choice2,
        "choice3": q.choice3,
        "choice4": q.choice4,
        "choice5": q.choice5,
        "answer": q.answer,
        "explanation": q.explanation,
        "education_module": q.education_module,
        "reference": q.reference,
        "validation_result": q.validation_result,
        "status": q.status,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }

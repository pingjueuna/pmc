"""참조 파일 업로드 API"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import aiofiles
from ..config import DATA_DIR, COMPETENCY_FILE, ITEM_BANK_FILE, CURRICULUM_FILE
from ..services.competency_service import reload_competency_data
from ..services.item_bank_service import reload_item_bank, get_item_bank_summary

router = APIRouter(prefix="/api/files", tags=["files"])

ALLOWED_FILES = {
    "competency": COMPETENCY_FILE,
    "item_bank": ITEM_BANK_FILE,
    "curriculum": CURRICULUM_FILE,
}

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".pdf", ".doc", ".docx"}


@router.post("/upload/{file_type}")
async def upload_file(file_type: str, file: UploadFile = File(...)):
    """참조 파일 업로드"""
    if file_type not in ALLOWED_FILES and file_type != "custom":
        raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 유형: {file_type}")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식: {suffix}. 허용: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file_type in ALLOWED_FILES:
        save_name = ALLOWED_FILES[file_type]
    else:
        save_name = file.filename

    save_path = DATA_DIR / save_name

    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 캐시 초기화
    if file_type == "competency":
        reload_competency_data()
    elif file_type == "item_bank":
        reload_item_bank()

    return {
        "success": True,
        "file_type": file_type,
        "saved_as": save_name,
        "size_bytes": len(content),
        "message": f"파일이 업로드되었습니다: {save_name}",
    }


@router.get("/status")
def get_file_status():
    """업로드된 참조 파일 현황 확인"""
    status = {}
    for file_type, filename in ALLOWED_FILES.items():
        path = DATA_DIR / filename
        status[file_type] = {
            "filename": filename,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    # 기타 업로드 파일
    other_files = []
    for p in DATA_DIR.iterdir():
        if p.name not in ALLOWED_FILES.values():
            other_files.append({"filename": p.name, "size_bytes": p.stat().st_size})

    item_bank_info = get_item_bank_summary()

    return {
        "reference_files": status,
        "other_files": other_files,
        "item_bank_summary": item_bank_info,
    }

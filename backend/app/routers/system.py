"""시스템 및 Claude 정보 API"""
import subprocess
import sys
import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/system", tags=["system"])


def _get_claude_exe() -> str:
    import importlib.util
    spec = importlib.util.find_spec("claude_agent_sdk")
    if spec and spec.submodule_search_locations:
        bundled = os.path.join(list(spec.submodule_search_locations)[0], "_bundled", "claude.exe")
        if os.path.exists(bundled):
            return bundled
    return "claude"


@router.get("/info")
def get_system_info():
    """Claude 및 시스템 정보 조회"""
    info = {
        "claude": {},
        "sdk": {},
        "python": {},
        "services": {},
    }

    # Claude CLI 버전
    try:
        claude_exe = _get_claude_exe()
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        result = subprocess.run(
            [claude_exe, "--version"],
            capture_output=True, text=True, env=env, timeout=5
        )
        version_str = result.stdout.strip() or result.stderr.strip()
        info["claude"]["cli_version"] = version_str
        info["claude"]["cli_path"] = claude_exe
    except Exception as e:
        info["claude"]["cli_version"] = f"확인 실패: {e}"

    # claude-agent-sdk 버전
    try:
        import claude_agent_sdk
        info["sdk"]["version"] = getattr(claude_agent_sdk, "__version__", "unknown")
        info["sdk"]["package"] = "claude-agent-sdk"
    except Exception as e:
        info["sdk"]["version"] = f"미설치: {e}"

    # 현재 사용 모델 (claude_service 설정 기반)
    info["claude"]["model"] = "claude-sonnet-4-6 (기본값)"
    info["claude"]["max_turns"] = 3
    info["claude"]["thinking"] = "활성화 (ThinkingBlock)"
    info["claude"]["auth"] = "Claude Code 세션 (별도 API 키 불필요)"

    # Python 버전
    info["python"]["version"] = sys.version
    info["python"]["executable"] = sys.executable

    # 서비스 파일 상태
    try:
        from ..config import DATA_DIR, COMPETENCY_FILE, ITEM_BANK_FILE, CURRICULUM_FILE
        info["services"]["competency_file"] = {
            "name": COMPETENCY_FILE,
            "loaded": (DATA_DIR / COMPETENCY_FILE).exists(),
        }
        info["services"]["item_bank_file"] = {
            "name": ITEM_BANK_FILE,
            "loaded": (DATA_DIR / ITEM_BANK_FILE).exists(),
        }
        info["services"]["curriculum_file"] = {
            "name": CURRICULUM_FILE,
            "loaded": (DATA_DIR / CURRICULUM_FILE).exists(),
        }
    except Exception as e:
        info["services"]["error"] = str(e)

    # DB 문항 수
    try:
        from ..database import SessionLocal, Question
        db = SessionLocal()
        try:
            info["services"]["total_questions"] = db.query(Question).count()
            info["services"]["approved_questions"] = db.query(Question).filter(Question.status == "approved").count()
            info["services"]["validated_questions"] = db.query(Question).filter(Question.status == "validated").count()
        finally:
            db.close()
    except Exception as e:
        info["services"]["db_error"] = str(e)

    # 중복 검사 설정
    try:
        from ..services.similarity_service import DUPLICATE_THRESHOLD
        info["services"]["duplicate_threshold"] = f"{DUPLICATE_THRESHOLD * 100:.0f}%"
    except Exception:
        pass

    return info

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Claude Agent SDK 사용 - API 키 불필요
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/pmsolution.db")

# Reference file names
COMPETENCY_FILE = "LG SW PMCompetency_v1.2.xlsx"
ITEM_BANK_FILE = "PM Competency Item Bank.xlsx"
CURRICULUM_FILE = "Project_Management_Course_Curriculum_ver2025.xlsx"

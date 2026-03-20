from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    competency = Column(String(100))
    competency_no = Column(String(20))
    sub_goal = Column(Text)
    difficulty = Column(String(10))
    methodology = Column(String(20))
    title = Column(String(200))
    question_type = Column(String(20))
    expected_wrong_rate = Column(String(10))
    wrong_type_tag = Column(String(50))
    question_text = Column(Text)
    choice1 = Column(Text)
    choice2 = Column(Text)
    choice3 = Column(Text)
    choice4 = Column(Text)
    choice5 = Column(Text)
    answer = Column(String(20))
    explanation = Column(Text)
    education_module = Column(String(200))
    reference = Column(Text)
    validation_result = Column(Text)
    status = Column(String(20), default="draft")  # draft, validated, approved
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExamResult(Base):
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    exam_name = Column(String(200))
    total_questions = Column(Integer)
    total_participants = Column(Integer)
    avg_score = Column(Float)
    pass_rate = Column(Float)
    raw_data = Column(Text)  # JSON
    analysis_result = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

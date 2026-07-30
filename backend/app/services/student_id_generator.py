import re
from sqlalchemy.orm import Session
from app.models.models import School, User


class StudentIdGeneratorService:
    @staticmethod
    def _extract_school_prefix(school_name: str) -> str:
        # Ignore common filler words like "Senior", "High", "School", "Girls", "Boys"
        words = re.findall(r"\b[A-Za-z]+\b", school_name)
        ignore_words = {"SENIOR", "HIGH", "SCHOOL", "ACADEMY", "TECHNICAL", "INSTITUTE"}
        meaningful_words = [w.upper() for w in words if w.upper() not in ignore_words]

        if not meaningful_words:
            meaningful_words = [w.upper() for w in words]

        if len(meaningful_words) >= 2:
            prefix = "".join(w[0] for w in meaningful_words[:2])
        elif len(meaningful_words) == 1:
            prefix = meaningful_words[0][:2]
        else:
            prefix = "ST"

        return prefix.upper()

    @classmethod
    def generate_student_id(cls, db: Session, school: School) -> str:
        prefix = cls._extract_school_prefix(school.name)
        
        # Count existing students in this school to increment sequence
        existing_count = (
            db.query(User)
            .filter(User.school_id == school.id, User.role == "student")
            .count()
        )
        
        sequence_num = existing_count + 1
        return f"{prefix}-{sequence_num:04d}"

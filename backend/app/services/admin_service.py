import io
import csv
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Region, School, AuditLog
from app.core.security import get_password_hash
from app.services.student_id_generator import StudentIdGeneratorService
from app.services.password_generator import PasswordGeneratorService
from app.schemas.admin import (
    StudentImportData,
    StudentImportRowError,
    StudentImportCredentialItem,
)

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class AdminService:
    @staticmethod
    def validate_csv_headers(fieldnames: List[str]) -> Dict[str, str]:
        if not fieldnames:
            raise ValueError("CSV file is empty or missing headers.")

        normalized = {fn.strip().lower(): fn for fn in fieldnames}
        required_keys = ["first name", "last name", "email", "school", "region"]

        missing = [req for req in required_keys if req not in normalized]
        if missing:
            formatted_missing = ", ".join([m.title() for m in missing])
            raise ValueError(f"Invalid CSV header. Missing required column(s): {formatted_missing}")

        return normalized

    def import_students_csv(
        self,
        db: Session,
        file_bytes: bytes,
        current_user: User,
        mode: str = "create",
        include_credentials: bool = True,
        dry_run: bool = False,
    ) -> StudentImportData:
        try:
            content = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        stream = io.StringIO(content)
        reader = csv.DictReader(stream, skipinitialspace=True)

        if not reader.fieldnames:
            raise ValueError("CSV file is empty or missing headers.")

        header_map = self.validate_csv_headers(reader.fieldnames)
        fn_key = header_map["first name"]
        ln_key = header_map["last name"]
        email_key = header_map["email"]
        school_key = header_map["school"]
        region_key = header_map["region"]

        # Pre-fetch existing schools and regions for O(1) matching
        existing_schools: List[School] = db.query(School).all()
        schools_by_name: Dict[str, School] = {s.name.strip().lower(): s for s in existing_schools}

        total_rows = 0
        imported_count = 0
        duplicates_count = 0
        failed_count = 0

        failed_rows: List[StudentImportRowError] = []
        credentials: List[StudentImportCredentialItem] = []
        processed_emails_in_batch = set()

        for idx, row in enumerate(reader, start=2):  # 1-indexed (Row 1 is Header)
            total_rows += 1

            first_name = (row.get(fn_key) or "").strip()
            last_name = (row.get(ln_key) or "").strip()
            raw_email = (row.get(email_key) or "").strip().lower()
            school_str = (row.get(school_key) or "").strip()
            region_str = (row.get(region_key) or "").strip()

            full_name = f"{first_name} {last_name}".strip()

            # 1. Validate required fields
            if not first_name or not last_name or not raw_email or not school_str:
                failed_count += 1
                failed_rows.append(
                    StudentImportRowError(
                        row=idx,
                        email=raw_email or None,
                        reason="Missing required row fields (First Name, Last Name, Email, or School).",
                    )
                )
                continue

            # 2. Validate email syntax
            if not EMAIL_REGEX.match(raw_email):
                failed_count += 1
                failed_rows.append(
                    StudentImportRowError(
                        row=idx,
                        email=raw_email,
                        reason=f"Invalid email address format '{raw_email}'.",
                    )
                )
                continue

            # 3. Controlled Reference Data Lookup: School MUST already exist
            matched_school = schools_by_name.get(school_str.lower())
            if not matched_school:
                failed_count += 1
                failed_rows.append(
                    StudentImportRowError(
                        row=idx,
                        email=raw_email,
                        reason=f"School '{school_str}' does not exist in the database. Please create the school first.",
                    )
                )
                continue

            # 4. Check for existing user in database
            existing_user = db.query(User).filter(User.email == raw_email).first()

            if mode == "create" and (raw_email in processed_emails_in_batch or existing_user):
                duplicates_count += 1
                failed_rows.append(
                    StudentImportRowError(
                        row=idx,
                        email=raw_email,
                        reason=f"Duplicate user email address '{raw_email}'.",
                    )
                )
                continue

            if mode == "update" and not existing_user:
                failed_count += 1
                failed_rows.append(
                    StudentImportRowError(
                        row=idx,
                        email=raw_email,
                        reason=f"Student email '{raw_email}' not found for update mode.",
                    )
                )
                continue

            processed_emails_in_batch.add(raw_email)

            student_id: str = ""
            temp_password: str = "[REDACTED_FOR_SECURITY]"

            if existing_user and mode in ["update", "upsert"]:
                student_id = getattr(existing_user, "student_id") or ""
                if not dry_run:
                    try:
                        with db.begin_nested():
                            setattr(existing_user, "name", full_name)
                            setattr(existing_user, "school_id", matched_school.id)
                            setattr(existing_user, "region_id", matched_school.region_id)
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        failed_count += 1
                        failed_rows.append(
                            StudentImportRowError(
                                row=idx,
                                email=raw_email,
                                reason=f"Database update failed: {str(e)}",
                            )
                        )
                        continue
            else:
                student_id = StudentIdGeneratorService.generate_student_id(db, matched_school)
                raw_temp_password = PasswordGeneratorService.generate_temp_password()
                hashed_pass = get_password_hash(raw_temp_password)
                temp_password = raw_temp_password if include_credentials else "[REDACTED_FOR_SECURITY]"

                if not dry_run:
                    try:
                        with db.begin_nested():
                            new_student = User(
                                email=raw_email,
                                name=full_name,
                                student_id=student_id,
                                password_hash=hashed_pass,
                                role="student",
                                school_id=matched_school.id,
                                region_id=matched_school.region_id,
                                must_change_password=True,
                                is_active=True,
                            )
                            db.add(new_student)
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        failed_count += 1
                        failed_rows.append(
                            StudentImportRowError(
                                row=idx,
                                email=raw_email,
                                reason=f"Database insertion failed: {str(e)}",
                            )
                        )
                        continue

            imported_count += 1
            credentials.append(
                StudentImportCredentialItem(
                    row=idx,
                    student_id=student_id,
                    name=full_name,
                    email=raw_email,
                    school=matched_school.name,
                    temp_password=temp_password if include_credentials else "[REDACTED_FOR_SECURITY]",
                )
            )

        # Create Audit Log
        action_name = (
            "ADMIN_BULK_STUDENT_IMPORT_DRY_RUN"
            if dry_run
            else f"ADMIN_BULK_STUDENT_IMPORT_{mode.upper()}_SUCCESS"
        )
        admin_id = getattr(current_user, "id")
        audit_details = (
            f"Processed {total_rows} rows (Mode: {mode}): {imported_count} processed/imported, "
            f"{duplicates_count} duplicates, {failed_count} failed. (Dry Run: {dry_run})"
        )
        try:
            audit = AuditLog(user_id=admin_id, action=action_name, details=audit_details)
            db.add(audit)
            db.commit()
        except Exception:
            db.rollback()

        return StudentImportData(
            dry_run=dry_run,
            total_rows=total_rows,
            imported=imported_count,
            duplicates=duplicates_count,
            failed=failed_count,
            failed_rows=failed_rows,
            credentials=credentials if include_credentials else [],
        )

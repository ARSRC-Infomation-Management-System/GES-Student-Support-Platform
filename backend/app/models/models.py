from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    schools = relationship("School", back_populates="region", cascade="all, delete-orphan")
    users = relationship("User", back_populates="region")
    complaints = relationship("Complaint", back_populates="region")
    broadcasts = relationship("Broadcast", back_populates="target_region")


class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    
    region = relationship("Region", back_populates="schools")
    users = relationship("User", back_populates="school")
    complaints = relationship("Complaint", back_populates="school")
    broadcasts = relationship("Broadcast", back_populates="target_school")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # Nullable for privacy
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # 'admin', 'official', 'student'
    is_active = Column(Boolean, default=True)
    
    # Regional tracking for student routing & officials scope
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    region = relationship("Region", back_populates="users")
    school = relationship("School", back_populates="users")
    
    # Complaints they filed (only for identified complaints!)
    complaints = relationship("Complaint", back_populates="student")
    
    # Broadcasts published (only officials/admins can publish)
    published_broadcasts = relationship("Broadcast", back_populates="author")
    
    # Messages sent
    messages = relationship("Message", back_populates="sender")
    
    # Notifications received
    notifications = relationship("Notification", back_populates="user")
    
    # Audit logs triggered
    audit_logs = relationship("AuditLog", back_populates="user")


class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, nullable=False, index=True)  # Random unique ID for tracking
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # 'bullying', 'abuse', 'academic', 'infrastructure', etc.
    status = Column(String(20), nullable=False, default="pending")  # 'pending', 'investigating', 'resolved', 'rejected'
    
    is_anonymous = Column(Boolean, default=True, nullable=False)
    
    # Linked student record (always non-nullable in DB, application handles privacy redaction)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Geolocation routing metadata (needed even for anonymous complaints to route to region/school officials)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = relationship("User", back_populates="complaints")
    school = relationship("School", back_populates="complaints")
    region = relationship("Region", back_populates="complaints")
    
    attachments = relationship("Attachment", back_populates="complaint", cascade="all, delete-orphan")
    conversation = relationship("Conversation", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="attachments")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    complaint = relationship("Complaint", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Linked sender record (always non-nullable in DB, application handles privacy redaction)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_role = Column(String(20), nullable=False)  # 'student', 'official', 'admin'
    
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="messages")


class Broadcast(Base):
    __tablename__ = "broadcasts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Target filters (nullable means global broadcast)
    target_region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    target_school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)
    
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    target_region = relationship("Region", back_populates="broadcasts")
    target_school = relationship("School", back_populates="broadcasts")
    author = relationship("User", back_populates="published_broadcasts")


class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)  # Link to the resource
    category = Column(String(50), nullable=False)  # 'academic', 'health', 'safety', 'guideline'
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous/system actions
    action = Column(String(100), nullable=False)  # e.g., "LOGIN_SUCCESS", "COMPLAINT_STATUS_CHANGE", etc.
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")

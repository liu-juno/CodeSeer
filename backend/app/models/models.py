import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Integer, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class IterationStatus(str, enum.Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    RELEASED = "released"
    ARCHIVED = "archived"


class RequirementStatus(str, enum.Enum):
    DRAFT = "draft"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    COMPLETED = "completed"


class RequirementPriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    identifier = Column(String(50), nullable=True, unique=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)
    owner_id = Column(String(36), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    iterations = relationship("Iteration", back_populates="project")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")


class Iteration(Base):
    __tablename__ = "iterations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(IterationStatus), default=IterationStatus.PLANNING)
    planned_release_date = Column(DateTime, nullable=True)
    actual_release_date = Column(DateTime, nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="iterations")
    requirements = relationship("Requirement", back_populates="iteration")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    acceptance_criteria = Column(Text, nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    iteration_id = Column(String(36), ForeignKey("iterations.id"), nullable=True)
    status = Column(Enum(RequirementStatus), default=RequirementStatus.DRAFT)
    priority = Column(Enum(RequirementPriority), default=RequirementPriority.P2)
    assignee_id = Column(String(36), nullable=True)
    creator_id = Column(String(36), nullable=True)
    estimated_hours_min = Column(Integer, nullable=True)
    estimated_hours_max = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    due_date = Column(DateTime, nullable=True)
    custom_fields = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    iteration = relationship("Iteration", back_populates="requirements")
    tasks = relationship("Task", back_populates="requirement", cascade="all, delete-orphan")
    test_records = relationship("UnitTestRecord", back_populates="requirement", cascade="all, delete-orphan")
    phases = relationship("RequirementPhase", back_populates="requirement", cascade="all, delete-orphan")
    history = relationship("RequirementHistory", back_populates="requirement", cascade="all, delete-orphan")


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(RequirementPriority), default=RequirementPriority.P2)
    order = Column(Integer, default=0)
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    tdd_red = Column(String(20), default="pending")
    tdd_green = Column(String(20), default="pending")
    tdd_refactor = Column(String(20), default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="tasks")


class TestResult(str, enum.Enum):
    ALL_PASSED = "all_passed"
    FAILED = "failed"
    PARTIAL = "partial"


class UnitTestRecord(Base):
    __tablename__ = "unit_test_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    task_title = Column(String(200), nullable=True)
    test_type = Column(String(50), default="unit")
    total_count = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    failed_tests = Column(Text, nullable=True)
    coverage = Column(Integer, nullable=True)
    result = Column(Enum(TestResult), default=TestResult.ALL_PASSED)
    executed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="test_records")


# ── 文档管理 ─────────────────────────────────────────────────────────────────

class DocumentStatus(str, enum.Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class DocumentType(str, enum.Enum):
    ANALYSIS = "analysis"
    DESIGN = "design"
    DIAGRAM = "diagram"
    API = "api"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    title = Column(String(200), nullable=False)
    document_type = Column(Enum(DocumentType), default=DocumentType.DESIGN)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    version = Column(Integer, default=1)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    archived_at = Column(DateTime, nullable=True)
    source_document_ids = Column(Text, nullable=True)  # JSON list, 记录合并来源文档 ID

    requirement = relationship("Requirement", backref="documents")
    module = relationship("Module", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version.desc()")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    change_note = Column(String(500), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="versions")


# ── 模块知识库 ───────────────────────────────────────────────────────────────

class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    parent_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    path = Column(String(500), nullable=True)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("Module", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="module")
    skill = relationship("Skill", back_populates="module", foreign_keys="[Skill.module_id]")


# ── Skill 自动生成 ───────────────────────────────────────────────────────────

class SkillStatus(str, enum.Enum):
    GENERATING = "generating"
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class SkillSource(str, enum.Enum):
    AUTO_GENERATED = "auto_generated"
    MANUAL = "manual"


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    version = Column(String(20), default="1.0.0")
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)  # Skill 摘要
    project_id = Column(String(36), nullable=True)  # 所属项目 ID
    knowledge_base_url = Column(String(500), nullable=True)  # 知识库 URL
    source = Column(Enum(SkillSource), default=SkillSource.AUTO_GENERATED)
    status = Column(Enum(SkillStatus), default=SkillStatus.DRAFT)
    prompt_template = Column(Text, nullable=True)
    parameters = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    module = relationship("Module", back_populates="skill", foreign_keys=[module_id])


# ── 需求开发阶段 ─────────────────────────────────────────────────────────────

class PhaseType(str, enum.Enum):
    CLARIFICATION = "clarification"   # 需求澄清
    PLANNING = "planning"             # 任务规划
    EXECUTION = "execution"           # 任务执行
    TESTING = "testing"               # 单元测试
    REVIEW = "review"                 # 代码审查


class PhaseStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class RequirementPhase(Base):
    __tablename__ = "requirement_phases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    phase = Column(Enum(PhaseType), nullable=False)
    status = Column(Enum(PhaseStatus), default=PhaseStatus.PENDING)
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="phases")


# ── 活动日志 ────────────────────────────────────────────────────────────────

class HistoryAction(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    DOCUMENT_SUBMITTED = "document_submitted"
    DOCUMENT_ARCHIVED = "document_archived"
    TASK_SYNCED = "task_synced"
    TEST_SUBMITTED = "test_submitted"
    ITERATION_RELEASED = "iteration_released"


class RequirementHistory(Base):
    __tablename__ = "requirement_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    action = Column(Enum(HistoryAction), nullable=False)
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    actor = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("Requirement", back_populates="history")


# ── 状态机配置 ──────────────────────────────────────────────────────────────

class StateMachineConfig(Base):
    __tablename__ = "state_machine_config"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    state = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    allowed_transitions = Column(Text, nullable=True)  # JSON 数组
    is_initial = Column(Boolean, default=False)
    is_terminal = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── 自定义需求字段 ──────────────────────────────────────────────────────────

class CustomFieldType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    MULTISELECT = "multiselect"
    USER = "user"
    MODULE = "module"


class CustomField(Base):
    __tablename__ = "custom_fields"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    field_key = Column(String(50), nullable=False, unique=True)
    field_name = Column(String(100), nullable=False)
    field_type = Column(Enum(CustomFieldType), default=CustomFieldType.TEXT)
    required = Column(Boolean, default=False)
    options = Column(Text, nullable=True)  # JSON 数组 (for select)
    default_value = Column(Text, nullable=True)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Webhook 系统 ──────────────────────────────────────────────────────────────

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=True)
    events = Column(Text, nullable=True)  # JSON 数组字符串
    enabled = Column(Boolean, default=True)
    max_retries = Column(Integer, default=3)
    retry_interval = Column(Integer, default=60)
    timeout = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String(36), ForeignKey("webhooks.id"), nullable=False)
    event = Column(String(100), nullable=False)
    payload = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt = Column(Integer, default=1)
    success = Column(Boolean, default=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    webhook = relationship("Webhook", back_populates="deliveries")


# ── 用户 / 角色 / 权限 ──────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PRODUCT_MANAGER = "product_manager"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(200), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.DEVELOPER)
    password_hash = Column(String(200), nullable=True)
    avatar_color = Column(String(20), default="#6366f1")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project_memberships = relationship("ProjectMember", foreign_keys="ProjectMember.user_id", back_populates="user", cascade="all, delete-orphan")


# ── 代码变更记录 ─────────────────────────────────────────────────────────────

class CodeChangeStatus(str, enum.Enum):
    PENDING = "pending"
    STORED = "stored"
    FAILED = "failed"


class CodeChange(Base):
    __tablename__ = "code_changes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)

    title = Column(String(200), nullable=False)
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)

    modules_affected = Column(Text, nullable=True)  # JSON
    exceptions = Column(Text, nullable=True)        # JSON

    diff_path = Column(String(500), nullable=True)
    diff_size = Column(Integer, default=0)

    status = Column(Enum(CodeChangeStatus), default=CodeChangeStatus.PENDING)

    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement = relationship("Requirement", backref="code_changes")
    task = relationship("Task", backref="code_changes")


# ── MCP Access Token ───────────────────────────────────────────────────────────

class AccessToken(Base):
    __tablename__ = "access_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    token_prefix = Column(String(16), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="access_tokens")


class RequirementAttachment(Base):
    __tablename__ = "requirement_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=True)
    storage_path = Column(String(500), nullable=False)
    storage_backend = Column(String(20), default="local")
    created_at = Column(DateTime, default=datetime.utcnow)

    requirement = relationship("Requirement", backref="attachments")


# ── 缺陷管理 ──────────────────────────────────────────────────────────────────

class DefectStatus(str, enum.Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    FIXING = "fixing"
    VERIFYING = "verifying"
    CLOSED = "closed"


class DefectSeverity(str, enum.Enum):
    FATAL = "fatal"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class DefectPriority(str, enum.Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class Defect(Base):
    __tablename__ = "defects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(DefectSeverity), default=DefectSeverity.MAJOR)
    priority = Column(Enum(DefectPriority), default=DefectPriority.P2)
    status = Column(Enum(DefectStatus), default=DefectStatus.NEW)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    iteration_id = Column(String(36), ForeignKey("iterations.id"), nullable=True)
    assignees = Column(Text, nullable=True)
    labels = Column(Text, nullable=True)
    steps_to_reproduce = Column(Text, nullable=True)
    environment = Column(Text, nullable=True)
    creator_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    requirement = relationship("Requirement")
    module = relationship("Module")
    iteration = relationship("Iteration")
    comments = relationship("DefectComment", back_populates="defect", cascade="all, delete-orphan")
    logs = relationship("DefectLog", back_populates="defect", cascade="all, delete-orphan")


class DefectComment(Base):
    __tablename__ = "defect_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    defect_id = Column(String(36), ForeignKey("defects.id"), nullable=False)
    user_id = Column(String(36), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    defect = relationship("Defect", back_populates="comments")


class DefectLog(Base):
    __tablename__ = "defect_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    defect_id = Column(String(36), ForeignKey("defects.id"), nullable=False)
    user_id = Column(String(36), nullable=True)
    action = Column(String(50), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    defect = relationship("Defect", back_populates="logs")


# ── 项目成员 ──────────────────────────────────────────────────────────────────

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(String(20), nullable=False, default="dev")
    status = Column(String(20), nullable=False, default="approved")
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_memberships")
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uk_project_user'),
    )


# ── API 管理 ──────────────────────────────────────────────────────────────────

class ApiEndpointStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class ApiHttpMethod(str, enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class ApiTestResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class ApiEndpoint(Base):
    __tablename__ = "api_endpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    module_id = Column(String(36), ForeignKey("modules.id"), nullable=True)
    method = Column(String(10), nullable=False)
    path = Column(String(200), nullable=False)
    summary = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    request_schema = Column(Text, nullable=True)
    response_schema = Column(Text, nullable=True)
    headers = Column(Text, nullable=True)
    status = Column(Enum(ApiEndpointStatus), default=ApiEndpointStatus.DRAFT)
    version = Column(Integer, default=1)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    module = relationship("Module")
    versions = relationship("ApiEndpointVersion", back_populates="endpoint", cascade="all, delete-orphan", order_by="ApiEndpointVersion.version.desc()")
    test_cases = relationship("ApiTestCase", back_populates="endpoint", cascade="all, delete-orphan")
    test_records = relationship("ApiTestRecord", back_populates="endpoint", cascade="all, delete-orphan")


class ApiEndpointVersion(Base):
    __tablename__ = "api_endpoint_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id"), nullable=False)
    version = Column(Integer, nullable=False)
    request_schema = Column(Text, nullable=True)
    response_schema = Column(Text, nullable=True)
    change_note = Column(String(500), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    endpoint = relationship("ApiEndpoint", back_populates="versions")


class ApiEnvironment(Base):
    __tablename__ = "api_environments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    name = Column(String(50), nullable=False)
    base_url = Column(String(200), nullable=False)
    variables = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


class ApiTestCase(Base):
    __tablename__ = "api_test_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id"), nullable=False)
    name = Column(String(200), nullable=False)
    request_params = Column(Text, nullable=True)
    expected_status = Column(Integer, nullable=True)
    expected_response = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    endpoint = relationship("ApiEndpoint", back_populates="test_cases")


class ApiTestRecord(Base):
    __tablename__ = "api_test_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String(36), ForeignKey("api_endpoints.id"), nullable=False)
    test_case_id = Column(String(36), ForeignKey("api_test_cases.id"), nullable=True)
    environment_id = Column(String(36), ForeignKey("api_environments.id"), nullable=True)
    request_params = Column(Text, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    result = Column(Enum(ApiTestResult), nullable=True)
    error_message = Column(Text, nullable=True)
    executed_by = Column(String(36), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    endpoint = relationship("ApiEndpoint", back_populates="test_records")
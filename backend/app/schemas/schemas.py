from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    COMPLETED = "completed"


class IterationStatus(str, Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    TESTING = "testing"
    RELEASED = "released"
    ARCHIVED = "archived"


class RequirementStatus(str, Enum):
    DRAFT = "draft"
    PENDING_ANALYSIS = "pending_analysis"
    ANALYZED = "analyzed"
    ASSIGNED = "assigned"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    COMPLETED = "completed"


class RequirementPriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    owner_id: Optional[UUID] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    id: UUID
    status: ProjectStatus
    owner_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Iteration Schemas
class IterationBase(BaseModel):
    name: str
    description: Optional[str] = None


class IterationCreate(IterationBase):
    project_id: UUID
    planned_release_date: Optional[date] = None


class IterationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IterationStatus] = None
    planned_release_date: Optional[date] = None


class IterationResponse(IterationBase):
    id: UUID
    project_id: UUID
    status: IterationStatus
    planned_release_date: Optional[date] = None
    actual_release_date: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Requirement Schemas
class RequirementBase(BaseModel):
    title: str
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None


class RequirementCreate(RequirementBase):
    project_id: UUID
    iteration_id: Optional[UUID] = None
    priority: Optional[RequirementPriority] = RequirementPriority.P2
    due_date: Optional[datetime] = None


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    status: Optional[RequirementStatus] = None
    priority: Optional[RequirementPriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None


class RequirementAssign(BaseModel):
    assignee_id: str
    comment: Optional[str] = None


class StatusTransition(BaseModel):
    action: str
    comment: Optional[str] = None


# Task Schemas
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[RequirementPriority] = RequirementPriority.P2
    order: Optional[int] = 0
    estimated_hours: Optional[int] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    tdd_red: Optional[str] = None
    tdd_green: Optional[str] = None
    tdd_refactor: Optional[str] = None
    actual_hours: Optional[int] = None


class TaskResponse(BaseModel):
    id: UUID
    requirement_id: UUID
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    order: int
    estimated_hours: Optional[int] = None
    actual_hours: Optional[int] = None
    tdd_red: str
    tdd_green: str
    tdd_refactor: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Test Record Schemas
class UnitTestRecordCreate(BaseModel):
    task_id: Optional[UUID] = None
    task_title: Optional[str] = None
    test_type: Optional[str] = "unit"
    total_count: int
    passed_count: int
    failed_count: int
    failed_tests: Optional[str] = None
    coverage: Optional[int] = None
    result: str
    executed_at: Optional[datetime] = None


class UnitTestRecordResponse(BaseModel):
    id: UUID
    requirement_id: UUID
    task_id: Optional[UUID] = None
    task_title: Optional[str] = None
    test_type: str
    total_count: int
    passed_count: int
    failed_count: int
    failed_tests: Optional[str] = None
    coverage: Optional[int] = None
    result: str
    executed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# MCP Schemas
class MCPSyncTasksPayload(BaseModel):
    requirement_id: str
    tasks: List[TaskCreate]


class MCPUpdateTaskPayload(BaseModel):
    requirement_id: str
    task_id: str
    status: Optional[str] = None
    tdd_red: Optional[str] = None
    tdd_green: Optional[str] = None
    tdd_refactor: Optional[str] = None
    actual_hours: Optional[int] = None


class MCPSubmitTestPayload(BaseModel):
    requirement_id: str
    task_id: Optional[str] = None
    task_title: Optional[str] = None
    test_type: Optional[str] = "unit"
    total_count: int
    passed_count: int
    failed_count: int
    failed_tests: Optional[str] = None
    coverage: Optional[int] = None
    result: str
    executed_at: Optional[datetime] = None


class RequirementResponse(RequirementBase):
    id: UUID
    project_id: UUID
    iteration_id: Optional[UUID] = None
    status: RequirementStatus
    priority: RequirementPriority
    assignee_id: Optional[UUID] = None
    creator_id: Optional[UUID] = None
    estimated_hours_min: Optional[int] = None
    estimated_hours_max: Optional[int] = None
    actual_hours: Optional[int] = None
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Document Schemas
class DocumentBase(BaseModel):
    title: str
    document_type: Optional[str] = "design"
    content: Optional[str] = None
    module_id: Optional[str] = None


class DocumentCreate(DocumentBase):
    requirement_id: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    document_type: Optional[str] = None
    module_id: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: UUID
    requirement_id: Optional[UUID] = None
    status: str
    processing_status: str
    summary: Optional[str] = None
    key_points: Optional[str] = None
    version: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version: int
    content: Optional[str] = None
    summary: Optional[str] = None
    change_note: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Module Schemas
class ModuleBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    path: Optional[str] = None


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class ModuleResponse(ModuleBase):
    id: UUID
    is_active: bool
    skill_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    children: List["ModuleResponse"] = []
    document_count: int = 0

    class Config:
        from_attributes = True


# Skill Schemas
class SkillBase(BaseModel):
    name: str
    description: Optional[str] = None
    module_id: Optional[str] = None
    prompt_template: Optional[str] = None
    parameters: Optional[str] = None


class SkillCreate(SkillBase):
    version: Optional[str] = "1.0.0"
    source: Optional[str] = "manual"
    summary: Optional[str] = None
    project_id: Optional[str] = None
    knowledge_base_url: Optional[str] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_template: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
    project_id: Optional[str] = None
    knowledge_base_url: Optional[str] = None


class SkillResponse(SkillBase):
    id: UUID
    version: str
    source: str
    status: str
    summary: Optional[str] = None
    project_id: Optional[str] = None
    knowledge_base_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


ModuleResponse.model_rebuild()


# Webhook Schemas
class WebhookBase(BaseModel):
    name: str
    url: str
    secret: Optional[str] = None
    events: Optional[list] = []
    enabled: Optional[bool] = True
    max_retries: Optional[int] = 3
    retry_interval: Optional[int] = 60
    timeout: Optional[int] = 10


class WebhookCreate(WebhookBase):
    pass


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[list] = None
    enabled: Optional[bool] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None


class WebhookResponse(WebhookBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryResponse(BaseModel):
    id: UUID
    webhook_id: UUID
    event: str
    response_status: Optional[int] = None
    success: bool
    attempt: int
    error: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# State Machine & Custom Field Schemas
class StateMachineConfigCreate(BaseModel):
    state: str
    name: str
    description: Optional[str] = None
    allowed_transitions: List[str] = []
    is_initial: bool = False
    is_terminal: bool = False
    order: int = 0


class StateMachineConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    allowed_transitions: Optional[List[str]] = None
    is_initial: Optional[bool] = None
    is_terminal: Optional[bool] = None
    order: Optional[int] = None


class StateMachineConfigResponse(BaseModel):
    id: UUID
    state: str
    name: str
    description: Optional[str] = None
    allowed_transitions: List[str]
    is_initial: bool
    is_terminal: bool
    order: int

    class Config:
        from_attributes = True


class CustomFieldCreate(BaseModel):
    field_key: str
    field_name: str
    field_type: str = "text"
    required: bool = False
    options: List[str] = []
    default_value: Optional[str] = None
    order: int = 0


class CustomFieldUpdate(BaseModel):
    field_name: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    options: Optional[List[str]] = None
    default_value: Optional[str] = None
    order: Optional[int] = None


class CustomFieldResponse(BaseModel):
    id: UUID
    field_key: str
    field_name: str
    field_type: str
    required: bool
    options: List[str]
    default_value: Optional[str] = None
    order: int

    class Config:
        from_attributes = True


# CodeChange Schemas
import json


class CodeChangeCreate(BaseModel):
    requirement_id: Optional[str] = None
    task_id: Optional[str] = None
    title: str
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    modules_affected: List[Dict[str, Any]] = []
    exceptions: List[Dict[str, str]] = []
    diff_content: str


class CodeChangeResponse(BaseModel):
    id: str
    requirement_id: Optional[str]
    task_id: Optional[str]
    title: str
    files_changed: int
    lines_added: int
    lines_deleted: int
    modules_affected: List[Dict[str, Any]]
    exceptions: List[Dict[str, str]]
    diff_path: Optional[str]
    diff_size: int
    status: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    @field_validator('modules_affected', 'exceptions', mode='before')
    @classmethod
    def parse_json_list(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class CodeChangeListResponse(BaseModel):
    requirement_id: Optional[str]
    changes: List[CodeChangeResponse]
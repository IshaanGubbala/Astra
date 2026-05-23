from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Founder:
    id: str
    email: str
    plan: str = "launch"
    credit_balance: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Goal:
    id: str
    founder_id: str
    instruction: str
    status: str = "pending"
    constraints: dict = field(default_factory=dict)
    elapsed_seconds: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class Task:
    id: str
    goal_id: str
    founder_id: str
    agent: str
    instruction: str
    context_bundle: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    status: str = "pending"
    result: Optional[dict] = None
    approval_required: bool = False
    tools_available: list = field(default_factory=list)
    constraints: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class Approval:
    id: str
    task_id: str
    founder_id: str
    agent: str
    action: str
    consequence: str
    approval_token: str
    expires_at: datetime
    documents_ready: list = field(default_factory=list)
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemoryDocument:
    id: str
    founder_id: str
    namespace: str
    agent: str
    doc_type: str
    content: str
    summary: str
    task_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

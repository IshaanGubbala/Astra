from backend.db.models import Founder, Goal, Task, Approval, MemoryDocument

def test_founder_defaults():
    f = Founder(id="f1", email="a@b.com")
    assert f.plan == "launch"
    assert f.credit_balance == 0

def test_task_defaults():
    t = Task(id="t1", goal_id="g1", founder_id="f1", agent="legal", instruction="draft NDA")
    assert t.status == "pending"
    assert t.depends_on == []
    assert t.approval_required is False

def test_memory_document_fields():
    doc = MemoryDocument(
        id="d1", founder_id="f1", namespace="legal", agent="legal",
        doc_type="document", content="full text", summary="short summary"
    )
    assert doc.metadata == {}

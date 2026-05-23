from backend.db.models import Task
from backend.memory.vector_store import vector_store


async def build_context(task: Task, namespaces: list[str]) -> dict:
    memory_docs = await vector_store.retrieve(
        founder_id=task.founder_id,
        namespaces=namespaces,
        query=task.instruction,
        k=5,
    )
    context = {
        **task.context_bundle,
        "memory_docs": [
            f"[{doc.get('doc_type', 'doc')}] {doc.get('summary', '')}"
            for doc in memory_docs
        ],
    }
    return context

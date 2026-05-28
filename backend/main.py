from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router
from backend.api.admin import router as admin_router

app = FastAPI(title="Astra API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control", "X-Accel-Buffering"],
)

app.include_router(router)
app.include_router(admin_router)


@app.on_event("startup")
async def startup_background_jobs():
    from backend.tools.company_brain_scheduler import start_company_brain_scheduler
    start_company_brain_scheduler(interval_seconds=60)


@app.on_event("shutdown")
async def shutdown_background_jobs():
    from backend.tools.company_brain_scheduler import stop_company_brain_scheduler
    await stop_company_brain_scheduler()


@app.get("/health")
async def health():
    return {"status": "ok"}

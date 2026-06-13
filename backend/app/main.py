from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.analytics import router as analytics_router
from app.api.routes.channels import router as channels_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.videos import router as videos_router
from app.core.config import settings

app = FastAPI(title="YouTube Niche Radar API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router)
app.include_router(channels_router)
app.include_router(videos_router)
app.include_router(tasks_router)
app.include_router(dashboard_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.api_env, "version": "0.2.0"}
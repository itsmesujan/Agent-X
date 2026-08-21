"""Agent-X FastAPI Application Entrypoint."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentx.api.middleware import StructuredLoggingMiddleware, register_exception_handlers
from agentx.api.routes_approvals import router as approvals_router
from agentx.api.routes_health import router as health_router
from agentx.api.routes_missions import router as missions_router
from agentx.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup initialization
    yield
    # Graceful shutdown cleanup


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent-X Mission Control API",
        description=(
            "Autonomous Mission Operating System providing REST, SSE telemetry, "
            "and HITL approval protocols for Google Cloud."
        ),
        version="0.1.0",
        openapi_tags=[
            {"name": "Health", "description": "Liveness and Readiness Health Probes"},
            {
                "name": "Missions",
                "description": "Autonomous Mission Lifecycle, DAG, Resources, and Evidence",
            },
            {
                "name": "Approvals",
                "description": "Human-in-the-Loop Escalation and Approval Decisions",
            },
        ],
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Structured Logging Middleware
    app.add_middleware(StructuredLoggingMiddleware)

    # Exception Handlers
    register_exception_handlers(app)

    # Register Routers
    app.include_router(health_router)
    app.include_router(missions_router, prefix="/api/v1")
    app.include_router(approvals_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "agentx.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )

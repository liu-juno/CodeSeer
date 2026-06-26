from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api import projects, iterations, requirements, tasks, mcp, documents, modules, webhooks, users, config, knowledge, mcp_skills, code_changes, mcp_tokens, mcp_http, auth, attachments, defects

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


# Include routers
app.include_router(projects.router, prefix=settings.API_PREFIX)
app.include_router(iterations.router, prefix=settings.API_PREFIX)
app.include_router(requirements.router, prefix=settings.API_PREFIX)
app.include_router(tasks.router, prefix=settings.API_PREFIX)
app.include_router(mcp.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(modules.router, prefix=settings.API_PREFIX)
app.include_router(webhooks.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)
app.include_router(config.router, prefix=settings.API_PREFIX)
app.include_router(knowledge.router, prefix=settings.API_PREFIX)
app.include_router(mcp_skills.router, prefix=settings.API_PREFIX)
app.include_router(code_changes.router, prefix=settings.API_PREFIX)
app.include_router(mcp_tokens.router, prefix=settings.API_PREFIX)
app.include_router(mcp_http.router, prefix=settings.API_PREFIX)
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(attachments.router, prefix=settings.API_PREFIX)
app.include_router(defects.router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {"message": "CodeSeer API", "version": settings.VERSION}


@app.get("/health")
async def health():
    return {"status": "healthy"}
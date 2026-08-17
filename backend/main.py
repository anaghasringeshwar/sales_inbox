from fastapi import FastAPI

from .database import Base, engine
from .models import Task
from .routers.tasks import router as tasks_router
from .routers.ingest import router as ingest_router
from .routers.api_tasks import router as api_tasks_router
from .routers.stats import router as stats_router
from .routers.chat import router as chat_router          
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://sales-inbox-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(tasks_router)
app.include_router(ingest_router)
app.include_router(api_tasks_router)
app.include_router(stats_router)
app.include_router(chat_router)                          


@app.get("/")
def home():
    return {"message": "Sales Inbox Router is running!"}
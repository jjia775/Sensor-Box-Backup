from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sensors, ingest, readings
import os

app = FastAPI()
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(sensors.router)
app.include_router(ingest.router)
app.include_router(readings.router)


@app.get("/health")
def health():
    return {"ok": True}
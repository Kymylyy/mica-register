from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .routers import entities
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MiCA Register API", version="1.0.0")

# Configure CORS
# Allow origins from environment variable or default to localhost for development
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(entities.router, prefix="/api", tags=["entities"])


@app.get("/")
def root():
    return {"message": "MiCA Register API", "version": "1.0.0"}



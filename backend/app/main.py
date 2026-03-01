from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session
from .database import engine, get_db, Base
from .routers import entities, feeds
from .config.registers import RegisterType
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
app.include_router(feeds.router, prefix="/api", tags=["feeds"])


@app.get("/")
def root():
    return {"message": "MiCA Register API", "version": "1.0.0"}


@app.get("/robots.txt", include_in_schema=False)
def robots_txt(request: Request):
    base_url = str(request.base_url).rstrip("/")
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /docs",
            "Allow: /openapi.json",
            "Allow: /api/feeds",
            "Allow: /api/feeds/",
            "Disallow: /api/admin/",
            "",
            f"Sitemap: {base_url}/sitemap.xml",
            "",
        ]
    )
    return PlainTextResponse(content=content)


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap_xml(request: Request):
    base_url = str(request.base_url).rstrip("/")
    paths = ["/", "/docs", "/openapi.json", "/api/feeds"]
    for register in RegisterType:
        paths.append(f"/api/feeds/{register.value}.json")
        paths.append(f"/api/feeds/{register.value}.csv")

    url_rows = "\n".join(f"  <url><loc>{base_url}{path}</loc></url>" for path in paths)
    xml_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{url_rows}\n"
        "</urlset>\n"
    )
    return Response(content=xml_content, media_type="application/xml")

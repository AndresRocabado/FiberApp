import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.schema import initialize_database
from api.routers import nodes, links, reports

initialize_database()

app = FastAPI(title="Fiber Network API", version="1.0.0")

app.include_router(nodes.router)
app.include_router(links.router)
app.include_router(reports.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")

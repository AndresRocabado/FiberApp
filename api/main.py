import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database.schema import initialize_database
from api import auth
from api.routers import nodes, links, reports

initialize_database()

app = FastAPI(title="Fiber Network API", version="1.0.0")

# Public route — no auth required
app.include_router(auth.router)

# Protected routes
_auth = [Depends(auth.require_auth)]
app.include_router(nodes.router,   dependencies=_auth)
app.include_router(links.router,   dependencies=_auth)
app.include_router(reports.router, dependencies=_auth)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/")
def root():
    return FileResponse("frontend/index.html")

import traceback

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.interfaces.api.graph import router as graph_router
from app.interfaces.api.ontology import router as ontology_router

app = FastAPI(title="ontoNgn API")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500, content={"message": "Internal Server Error", "traceback": traceback.format_exc()}
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from ontoNgn"}


@app.get("/graph", response_class=HTMLResponse)
def get_graph_ui(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="graph.html")


app.include_router(ontology_router, prefix="/api/v1/ontology", tags=["ontology"])
app.include_router(graph_router, prefix="/api/v1/graph", tags=["graph"])

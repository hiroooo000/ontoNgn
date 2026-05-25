from fastapi import FastAPI

from app.interfaces.api.ontology import router as ontology_router

app = FastAPI(title="ontoNgn API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from ontoNgn"}


app.include_router(ontology_router, prefix="/api/v1/ontology", tags=["ontology"])

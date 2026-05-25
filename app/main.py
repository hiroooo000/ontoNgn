from fastapi import FastAPI

app = FastAPI(title="ontoNgn API", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from ontoNgn"}

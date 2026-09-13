from fastapi import FastAPI

app = FastAPI(title="Dummy Downstream Service")

@app.get("/{path:path}")
async def echo(path: str):
    return {"message": f"You reached the downstream service at /{path}"}

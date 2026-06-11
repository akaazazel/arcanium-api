from fastapi import FastAPI

from app.routes import auth

app = FastAPI()


@app.get("/")
async def ping():
    return {"message": "Hello World!"}


app.router.include_router(auth.router)

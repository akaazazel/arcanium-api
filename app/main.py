import asyncio
from fastapi import FastAPI
from app.database.init_db import init_db

app = FastAPI()

asyncio.run(init_db())


@app.get("/")
def ping():
    return {"message": "Hello World!"}

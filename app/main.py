from app.core.exceptions import (
    http_exception,
    internal_server_exception,
    validation_exception,
)
from app.routes import auth, notes
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware import cors
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from app.database import r_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Secure Vault API Started")

    try:
        yield
    finally:
        await r_db.aclose()
        print("✅ Redis DB Connections Closed")
        print("✅ Secure Vault API Stopped")


app = FastAPI(lifespan=lifespan)


# Middlewares

app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=["https://hei.com"],  # configure of productions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_middlelware(request: Request, call_next):
    response: Response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # Uncomment on production
    # response.headers["Strict-Transport-Security"] = "max-age=3153600; includeSubDomains"

    return response


# Routers

app.router.include_router(auth.router)
app.router.include_router(notes.router)

# Exception Handlers

app.add_exception_handler(
    exc_class_or_status_code=HTTPException,
    handler=http_exception,  # type: ignore
)
app.add_exception_handler(
    exc_class_or_status_code=RequestValidationError,
    handler=validation_exception,  # type: ignore
)
app.add_exception_handler(
    exc_class_or_status_code=Exception,
    handler=internal_server_exception,
)

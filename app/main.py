from app.routes import auth, notes
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    http_exception,
    validation_exception,
    internal_server_exception,
)

app = FastAPI()


app.router.include_router(auth.router)
app.router.include_router(notes.router)

app.add_exception_handler(
    exc_class_or_status_code=HTTPException,
    handler=http_exception,  # type: ignore
)
app.add_exception_handler(
    exc_class_or_status_code=RequestValidationError,
    handler=validation_exception,  # type: ignore
)
app.add_exception_handler(
    exc_class_or_status_code=Exception, handler=internal_server_exception
)

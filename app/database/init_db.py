from sqlalchemy_utils import database_exists, create_database
from app.database.database import engine
from app.database.models import *


async def init_db():
    if not database_exists(engine.url):
        create_database(engine.url)

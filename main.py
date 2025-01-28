import logfire
from fastapi import FastAPI

# from config import settings
from routers.chat import chat_router
from routers.supabase import supabase_router
from routers.test import test_router

app = FastAPI()
app.include_router(supabase_router)
app.include_router(chat_router)
app.include_router(test_router)

logfire.configure()
logfire.instrument_asyncpg()
logfire.instrument_fastapi(app)


@app.get("/")
def read_root():
    return {"Hello": "World"}

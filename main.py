import logfire
from dotenv import load_dotenv
from fastapi import FastAPI

from routers.chat import chat_router
from routers.supabase import supabase_router

load_dotenv()

app = FastAPI()
app.include_router(supabase_router)
app.include_router(chat_router)

logfire.configure()
logfire.instrument_asyncpg()
logfire.instrument_fastapi(app)


@app.get("/")
def read_root():
    return {"Hello": "World"}

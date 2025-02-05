import uvicorn
from fastapi import FastAPI

from app.core.exc_handlers import setup_exception_handlers
from app.links.router import router as links_router


app = FastAPI(
    title='URL Shortener',
    version="0.1",
)

setup_exception_handlers(app)
app.include_router(links_router)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=8000, reload=True)

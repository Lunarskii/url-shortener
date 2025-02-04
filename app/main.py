import uvicorn
from fastapi import FastAPI

from app.links.router import router as links_router
from app.core.exc_handlers import setup_exception_handlers


app = FastAPI(
    title='URL Shortener',
    version="0.1",
)
app.include_router(links_router)
setup_exception_handlers(app)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=8000, reload=True)

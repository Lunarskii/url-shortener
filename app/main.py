import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.links.router import router as links_router

app = FastAPI(
    title='URL Shortener',
    version="0.1",
)
app.include_router(links_router)


@app.get("/favicon.ico")
async def favicon() -> JSONResponse:
    return JSONResponse(content={}, status_code=204)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=8000, reload=True)

from fastapi import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

app = FastAPI(title="ScamGuard API", version="0.1.0")

# Restrict CORS to typical extension scheme + localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_origin_regex=r"^chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if "/api/v1/scan" in request.url.path:
        body_bytes = await request.body()
        with open("../payload.log", "w") as f:
            f.write(body_bytes.decode())
        
        # reconstruct the request since body is consumed
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive
        
    response = await call_next(request)
    return response

app.include_router(router)


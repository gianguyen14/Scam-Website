from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from src.api.feed_updater import update_threat_intel_feeds
from src.api.routes import router
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động lịch trình tự động update dữ liệu rủi ro
    scheduler = BackgroundScheduler()
    # Chạy lần đầu ngay lập tức
    scheduler.add_job(update_threat_intel_feeds, 'date')
    # Lặp lại sau mỗi 12 giờ
    scheduler.add_job(update_threat_intel_feeds, 'interval', hours=12)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="ScamGuard API", version="0.1.0", lifespan=lifespan)


# Restrict CORS to typical extension scheme + localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*',

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


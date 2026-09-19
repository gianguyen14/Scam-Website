from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router
import contextlib


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    # Khởi động lịch trình tự động update dữ liệu nếu KHÔNG chạy trên Vercel
    if not os.environ.get("VERCEL_BUILD") and not os.environ.get("VERCEL"):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from src.api.feed_updater import update_threat_intel_feeds
            scheduler = BackgroundScheduler()
            scheduler.add_job(update_threat_intel_feeds, 'date')
            scheduler.add_job(update_threat_intel_feeds, 'interval', hours=12)
            scheduler.start()
        except ImportError:
            pass
    yield


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



app.include_router(router)


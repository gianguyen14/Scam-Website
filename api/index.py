import os
import sys

# Thêm đường dẫn backend vào sys.path để import
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))

# Cấu hình biến môi trường Vercel 
os.environ["VERCEL_BUILD"] = "1"
os.environ["VERCEL"] = "1"

from src.main import app

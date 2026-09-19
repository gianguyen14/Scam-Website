
import sys
# fake missing torch and pandas
sys.modules['torch'] = None
sys.modules['pandas'] = None
sys.modules['torchvision'] = None

import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend"))
os.environ["VERCEL_BUILD"] = "1"
os.environ["VERCEL"] = "1"

from src.api.risk_model import CoreRiskEngine
e = CoreRiskEngine()

import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import joblib

# Ensure we can import our url feature extractor
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from api.url_detector import extract_url_features

print("--- TRAINING URL AI MODEL ---")
urls = [
    ("https://google.com", 0),
    ("http://yahoo.com", 0),
    ("https://github.com/login", 0),
    ("https://vietcombank.com.vn", 0),
    ("http://example.com/path?val=1", 0),
    ("http://192.168.1.1/update", 1),
    ("http://vietc0mbank-login.xyz", 1),
    ("https://secure-update-account.top", 1),
    ("http://bit.ly/2kjds9?login=true", 1),
    ("http://login.microsoft.hacker.com", 1),
    ("https://binance-reward.vip/withdraw", 1)
]

X_url = [extract_url_features(u[0]) for u in urls]
y_url = [u[1] for u in urls]

df = pd.DataFrame(X_url)

url_clf = RandomForestClassifier(n_estimators=50, random_state=42)
url_clf.fit(df, y_url)

joblib.dump({"model": url_clf, "features": list(df.columns)}, "../models/url_model.joblib")
print("Saved url_model.joblib")

print("--- TRAINING CONTENT AI MODEL (NLP) ---")
texts = [
    ("Welcome to our official website. Please read our documentation.", 0),
    ("This is a tutorial on how to use Python and machine learning.", 0),
    ("Contact support for any questions regarding your invoice.", 0),
    ("Tài khoản của bạn sẽ bị khóa khẩn cấp trong 24h. Đăng nhập ngay để giải quyết.", 1),
    ("Urgent: Your account is suspended. Verify your identity immediately.", 1),
    ("You have won a free iPhone. Click here to claim your prize and enter credit card.", 1),
    ("Xác nhận mã OTP để nhận tiền thưởng từ ngân hàng.", 1),
    ("Verify account wallet urgently.", 1)
]

df_txt = pd.DataFrame(texts, columns=["text", "label"])

content_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2))),
    ('clf', LogisticRegression())
])

content_pipeline.fit(df_txt['text'], df_txt['label'])
joblib.dump(content_pipeline, "../models/content_nlp_model.joblib")
print("Saved content_nlp_model.joblib")

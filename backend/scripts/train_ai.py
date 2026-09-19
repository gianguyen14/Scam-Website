import os
import json
import random
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import joblib

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from api.url_detector import extract_url_features

print("--- DOWNLOADING AND PARSING DATA SCAM ---")
# Merge data from translate
translate_scam = "/tmp/data_scam/translate/tele28k_scam_translate.json"
translate_harmless = "/tmp/data_scam/translate/tele28k_harmless_translate.json"

def load_data(file_path, limit, class_label):
    docs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        random.seed(42)
        sample = random.sample(data, min(limit, len(data)))
        
        for item in sample:
            conv = item.get('vi_dialogue', [])
            if not conv:
                conv = item.get('dialogue', []) # fallback
                
            # If it's a list of dicts with 'content'
            text_parts = []
            for msg in conv:
                if isinstance(msg, dict):
                    text_parts.append(msg.get('content', ''))
                elif isinstance(msg, str):
                    text_parts.append(msg)
                    
            docs.append((" ".join(text_parts), class_label))
    except Exception as e:
        print("Err loading", file_path, e)
    return docs

scam_docs = load_data(translate_scam, 3353, 1)
harmless_docs = load_data(translate_harmless, 3353, 0)
all_docs = scam_docs + harmless_docs

os.makedirs("../data", exist_ok=True)
with open("../data/scam_conversations.json", "w", encoding="utf-8") as f:
    json.dump([{"text": t, "label": l} for t, l in all_docs], f, ensure_ascii=False, indent=2)

print(f"Loaded {len(scam_docs)} scam docs and {len(harmless_docs)} harmless docs.")

df_txt = pd.DataFrame(all_docs, columns=["text", "label"])

print("--- TRAINING CONTENT AI MODEL (NLP) V2 ---")
# Using random forest or logistic regression
content_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(ngram_range=(1,2), max_features=3000)),
    ('clf', LogisticRegression(C=1.0, max_iter=1000))
])

content_pipeline.fit(df_txt['text'], df_txt['label'])
joblib.dump(content_pipeline, "../models/content_nlp_model_v2.joblib")
print("Saved content_nlp_model_v2.joblib")

# Retrain URL model just so we have it up to date
urls = [
    ("https://google.com", 0), ("http://yahoo.com", 0), ("https://github.com/login", 0),
    ("https://vietcombank.com.vn", 0), ("http://example.com/path?val=1", 0),
    ("http://192.168.1.1/update", 1), ("http://vietc0mbank-login.xyz", 1),
    ("https://secure-update-account.top", 1), ("http://bit.ly/2kjds9?login=true", 1),
    ("http://login.microsoft.hacker.com", 1), ("https://binance-reward.vip/withdraw", 1)
]
df_url = pd.DataFrame([extract_url_features(u[0]) for u in urls])
url_clf = RandomForestClassifier(n_estimators=100, random_state=42)
url_clf.fit(df_url, [u[1] for u in urls])
joblib.dump({"model": url_clf, "features": list(df_url.columns)}, "../models/url_model.joblib")
print("Saved url_model.joblib")

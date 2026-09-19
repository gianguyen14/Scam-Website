import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import joblib

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from api.url_detector import extract_url_features

print("--- TRAINING URL AI MODEL WITH CLD DATASET ---")
try:
    cld_df = pd.read_csv('/tmp/phishing-ml/Generate Dataset/dataset.csv', on_bad_lines='skip', nrows=50000)
    
    # Balance dataset
    df_safe = cld_df[cld_df['label'] == 0].sample(n=3000, random_state=42)
    df_phish = cld_df[cld_df['label'] == 1].sample(n=3000, random_state=42)
    df_balanced = pd.concat([df_safe, df_phish])
    
    urls = list(zip(df_balanced['url'], df_balanced['label']))
except Exception as e:
    print("Could not load CLD dataset, using fallback:", e)
    urls = [
        ("https://google.com", 0), ("http://yahoo.com", 0),
        ("http://192.168.1.1/update", 1), ("http://vietc0mbank-login.xyz", 1)
    ]

# Extract features using our own static high-speed engine
df_url = pd.DataFrame([extract_url_features(str(u[0])) for u in urls])
url_clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
url_clf.fit(df_url, [u[1] for u in urls])
joblib.dump({"model": url_clf, "features": list(df_url.columns)}, "models/url_model.joblib")
print("Saved url_model.joblib (ChongLuaDao Enriched)")

print("Done training URL AI!")

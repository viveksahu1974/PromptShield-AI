"""Optional offline baseline, NOT integrated into the API."""
import csv,sys
from pathlib import Path
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: python ml/train.py data.csv")
    with open(sys.argv[1],encoding="utf-8",newline="") as f: rows=list(csv.DictReader(f))
    X=[r["text"] for r in rows];y=[int(r["label"]) for r in rows]
    tx,vx,ty,vy=train_test_split(X,y,test_size=.2,stratify=y,random_state=42)
    model=Pipeline([("tfidf",TfidfVectorizer(ngram_range=(1,2),max_features=15000)),("classifier",LogisticRegression(max_iter=2000,class_weight="balanced"))])
    model.fit(tx,ty);print(classification_report(vy,model.predict(vx),zero_division=0))
    path=Path(__file__).parent/"promptshield_baseline.joblib";joblib.dump(model,path);print("Saved",path)

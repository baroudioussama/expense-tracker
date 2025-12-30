import os
import re
import joblib
import pandas as pd
import numpy as np
from typing import Tuple
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report


HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(HERE, "model.pkl")
DATA_PATH = os.path.join(HERE, "transactions.csv")

CONFIDENCE_THRESHOLD = 0.40
MIN_SAMPLES_PER_CLASS = 3
N_TRAINING_ITERATIONS = 5  

class CategoryClassifier:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pipeline = None
            cls._instance._load_or_train()
        return cls._instance

    # --------------------------------------------------
    # LOAD OR TRAIN
    # --------------------------------------------------
    def _load_or_train(self):
        if os.path.exists(MODEL_PATH):
            try:
                data = joblib.load(MODEL_PATH)
                self.pipeline = data["pipeline"]
                print(f"[ML] Model loaded. Accuracy: {data.get('accuracy', 'N/A'):.3f}")
                return
            except Exception as e:
                print("[ML] Failed to load model:", e)

        print("[ML] Training model with multiple iterations...")
        self._train_and_save()

    # --------------------------------------------------
    # TEXT CLEANING
    # --------------------------------------------------
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    # --------------------------------------------------
    # COMBINE DESCRIPTION + MERCHANT
    # --------------------------------------------------
    def _combine(self, description: str, merchant: str) -> str:
        d = self._clean_text(description)
        m = self._clean_text(merchant)

        # Description is more important → repeat it
        return f"{d} {d} {m}".strip()

    # --------------------------------------------------
    # TRAINING WITH MULTIPLE ITERATIONS
    # --------------------------------------------------
    def _train_and_save(self):
        df = pd.read_csv(DATA_PATH)

        required = {"description", "merchant", "category"}
        if not required.issubset(df.columns):
            raise ValueError("Dataset must contain description, merchant, category")

        df["description"] = df["description"].fillna("")
        df["merchant"] = df["merchant"].fillna("")
        df["category"] = df["category"].astype(str).str.strip()

        df["text"] = df.apply(
            lambda r: self._combine(r["description"], r["merchant"]),
            axis=1
        )

        df = df[df["text"] != ""]

        # Remove weak classes
        counts = df["category"].value_counts()
        df = df[df["category"].isin(counts[counts >= MIN_SAMPLES_PER_CLASS].index)]

        print(f"[ML] Training rows: {len(df)}")
        print(f"[ML] Categories: {df['category'].nunique()}")
        print(f"[ML] Distribution:\n{df['category'].value_counts()}\n")

        X = df["text"]
        y = df["category"]

        # Split data once
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )

        best_pipeline = None
        best_accuracy = 0
        best_cv_score = 0

        print(f"[ML] Training {N_TRAINING_ITERATIONS} models to find the best...")
        
        for iteration in range(N_TRAINING_ITERATIONS):
            print(f"\n--- Iteration {iteration + 1}/{N_TRAINING_ITERATIONS} ---")
            
            # Create pipeline with different random states
            pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    max_features=10000,  # Increased features
                    ngram_range=(1, 3),  # Include trigrams
                    analyzer="word",
                    stop_words="english",
                    sublinear_tf=True,
                    min_df=2,
                    max_df=0.95
                )),
                ("clf", LogisticRegression(
                    max_iter=2000,
                    solver="saga",
                    penalty="elasticnet",
                    l1_ratio=0.5,
                    C=1.0,  # Regularization
                    class_weight="balanced",
                    random_state=42 + iteration,  # Different seed each time
                    n_jobs=-1
                ))
            ])

            # Train
            pipeline.fit(X_train, y_train)

            # Evaluate on test set
            y_pred = pipeline.predict(X_test)
            test_acc = accuracy_score(y_test, y_pred)

            # Cross-validation on training set
            cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, n_jobs=-1)
            cv_mean = cv_scores.mean()

            print(f"Test Accuracy: {test_acc:.3f}")
            print(f"CV Accuracy: {cv_mean:.3f} (+/- {cv_scores.std():.3f})")

            # Keep best model based on CV score
            if cv_mean > best_cv_score:
                best_cv_score = cv_mean
                best_accuracy = test_acc
                best_pipeline = pipeline
                print("✅ New best model!")

        # Use the best model
        print(f"\n[ML] Best model selected:")
        print(f"  Test Accuracy: {best_accuracy:.3f}")
        print(f"  CV Accuracy: {best_cv_score:.3f}")

        # Final evaluation with classification report
        y_pred_best = best_pipeline.predict(X_test)
        print("\n[ML] Classification Report:")
        print(classification_report(y_test, y_pred_best, zero_division=0))

        # Save best model
        joblib.dump({
            "pipeline": best_pipeline,
            "accuracy": best_accuracy,
            "cv_score": best_cv_score
        }, MODEL_PATH)
        
        self.pipeline = best_pipeline
        print("\n[ML] Best model saved!")

    # --------------------------------------------------
    # PREDICT
    # --------------------------------------------------
    def predict(self, description: str, merchant: str = "") -> Tuple[str, float]:
        if not self.pipeline:
            raise RuntimeError("Model not loaded")

        text = self._combine(description, merchant)

        if not text:
            return "Other", 0.0

        proba = self.pipeline.predict_proba([text])[0]
        pred = self.pipeline.classes_[np.argmax(proba)]
        confidence = float(np.max(proba))

        # Penalize ultra-short inputs
        word_count = len(text.split())
        if word_count <= 1:
            confidence *= 0.7
        elif word_count == 2:
            confidence *= 0.85

        if confidence < CONFIDENCE_THRESHOLD:
            # Return top prediction anyway but mark as "Other" if too uncertain
            return "Other", confidence

        return pred, confidence

    def predict_simple(self, description: str, merchant: str = "") -> str:
        return self.predict(description, merchant)[0]

    def get_top_predictions(self, description: str, merchant: str = "", top_n: int = 3):
        """Get top N predictions with confidence scores"""
        if not self.pipeline:
            raise RuntimeError("Model not loaded")

        text = self._combine(description, merchant)
        if not text:
            return [("Other", 0.0)]

        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        
        # Get top N
        top_indices = np.argsort(proba)[-top_n:][::-1]
        return [(classes[i], float(proba[i])) for i in top_indices]


# FastAPI dependency
def get_classifier():
    return CategoryClassifier()


if __name__ == "__main__":
    clf = CategoryClassifier()

    tests = [
        ("bus ticket", "Metro"),
        ("electricity bill", "Power Company"),
        ("grocery shopping", "Walmart"),
        ("netflix subscription", "Netflix"),
        ("coffee", "Starbucks"),
        ("rent payment", "Apartment"),
        ("car insurance", "State Farm"),
        ("doctor visit", "Hospital"),
        ("phone bill", "Verizon"),
        ("gas fill up", "Shell"),
        ("loan payment", "Bank"),
        ("toy purchase", "Toy Store"),
        ("flight ticket", "Delta Airlines"),
        ("textbook", "Bookstore"),
        ("oil change", "Auto Shop"),
    ]

    print("\n" + "="*70)
    print("TESTING CLASSIFIER")
    print("="*70)
    
    for desc, merch in tests:
        cat, conf = clf.predict(desc, merch)
        
        print(f"📝 '{desc}' @ '{merch}' → {cat} ({conf:.1%})")
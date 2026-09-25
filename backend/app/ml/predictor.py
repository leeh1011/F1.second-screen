import os
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier

MODEL_FILE = os.path.join(os.path.dirname(__file__), "overtake_model.pkl")

class OvertakePredictor:
    def __init__(self):
        self.model = None
        self._load_or_train_model()

    def _load_or_train_model(self):
        if os.path.exists(MODEL_FILE):
            try:
                with open(MODEL_FILE, "rb") as f:
                    self.model = pickle.load(f)
                return
            except Exception as e:
                print(f"Failed to load model file, retraining: {e}")

        # Train a robust Random Forest Overtake Classifier on synthetic/FastF1 distributions
        np.random.seed(42)
        n_samples = 2000

        # Features: [gap_ahead_sec, tyre_age_diff (laps), speed_diff_kph, drs_active (0/1)]
        gaps = np.random.uniform(0.1, 2.5, n_samples)
        tyre_diffs = np.random.uniform(-20, 20, n_samples)  # positive = attacker has fresher tyres
        speed_diffs = np.random.uniform(-15, 25, n_samples) # positive = attacker is faster
        drs = np.random.choice([0, 1], size=n_samples, p=[0.4, 0.6])

        # True logit equation for overtake probability
        logit = (
            -2.5 * gaps +
            0.12 * tyre_diffs +
            0.15 * speed_diffs +
            1.8 * drs +
            0.5
        )
        probs = 1 / (1 + np.exp(-logit))
        labels = (probs > np.random.uniform(0, 1, n_samples)).astype(int)

        X = np.column_stack([gaps, tyre_diffs, speed_diffs, drs])
        y = labels

        clf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
        clf.fit(X, y)

        self.model = clf
        with open(MODEL_FILE, "wb") as f:
            pickle.dump(clf, f)
        print("ML Overtake Model trained and saved successfully.")

    def predict(
        self,
        gap_ahead_sec: float,
        tyre_age_diff: int,
        speed_diff_kph: float,
        drs_active: bool,
    ) -> dict:
        if not self.model:
            self._load_or_train_model()

        drs_val = 1 if drs_active else 0
        X_test = np.array([[gap_ahead_sec, tyre_age_diff, speed_diff_kph, drs_val]])
        prob = float(self.model.predict_proba(X_test)[0][1])

        # Determine key factors
        factors = []
        if drs_active:
            factors.append("DRS Zone Active (Wing Open)")
        if tyre_age_diff > 3:
            factors.append(f"Fresher Tyre Advantage (+{tyre_age_diff} Laps)")
        elif tyre_age_diff < -3:
            factors.append(f"Defender Tyre Advantage ({abs(tyre_age_diff)} Laps Fresher)")
        if speed_diff_kph > 3:
            factors.append(f"Straight Speed Advantage (+{speed_diff_kph:.1f} km/h)")
        if gap_ahead_sec < 0.6:
            factors.append(f"Under 0.6s DRS Slipstream Gap ({gap_ahead_sec:.2f}s)")

        if not factors:
            factors.append("Standard Pace Differential")

        return {
            "success_probability": round(prob, 2),
            "factors": factors,
            "inputs": {
                "gap_ahead_sec": gap_ahead_sec,
                "tyre_age_diff": tyre_age_diff,
                "speed_diff_kph": speed_diff_kph,
                "drs_active": drs_active,
            },
        }

predictor_engine = OvertakePredictor()

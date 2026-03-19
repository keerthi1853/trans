import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATASET_PATH = Path("upi_fraud_dataset.csv")
MODEL_PATH = Path("UPI_Fraud_Detection_Model_Fixed.pkl")


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH.resolve()}")

    df = pd.read_csv(DATASET_PATH)

    required_columns = [
        "Transaction_Amount",
        "Transaction_Type",
        "Time_of_Transaction",
        "Device_Used",
        "Location",
        "Previous_Fraudulent_Transactions",
        "Account_Age",
        "Number_of_Transactions_Last_24H",
        "Payment_Method",
        "Fraudulent",
    ]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    features = [
        "Transaction_Amount",
        "Transaction_Type",
        "Time_of_Transaction",
        "Device_Used",
        "Location",
        "Previous_Fraudulent_Transactions",
        "Account_Age",
        "Number_of_Transactions_Last_24H",
        "Payment_Method",
    ]
    target = "Fraudulent"

    X = df[features].copy()
    y = df[target].astype(int)

    categorical_cols = ["Transaction_Type", "Device_Used", "Location", "Payment_Method"]
    numeric_cols = [c for c in features if c not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("prep", preprocessor),
            ("model", RandomForestClassifier(n_estimators=200, random_state=42)),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)
    probs = pipeline.predict_proba(X_test)[:, 1]

    metrics = {
        "Accuracy": float(accuracy_score(y_test, preds)),
        "Precision": float(precision_score(y_test, preds, zero_division=0)),
        "Recall": float(recall_score(y_test, preds, zero_division=0)),
        "F1_Score": float(f1_score(y_test, preds, zero_division=0)),
        "ROC_AUC": float(roc_auc_score(y_test, probs)),
    }

    artifact = {
        "pipeline": pipeline,
        "features": features,
        "performance_metrics": metrics,
        "dataset": str(DATASET_PATH),
    }

    with MODEL_PATH.open("wb") as f:
        pickle.dump(artifact, f)

    print(f"Saved model: {MODEL_PATH.resolve()}")
    print("Metrics:")
    for k, v in metrics.items():
        print(f"- {k}: {v:.4f}")


if __name__ == "__main__":
    main()

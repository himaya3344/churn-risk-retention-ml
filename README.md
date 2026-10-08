# Customer Churn Prediction and Retention Targeting

End-to-end machine-learning project: predicts which subscription customers are most likely to churn, ranks them for a limited retention campaign (top 20%), explains the predictions, and estimates the business value under stated hypothetical assumptions.

## Project structure

```
churn_project/
├── data/
│   └── customer_churn_advanced_dataset.csv   # raw input (1,200 rows, 20 columns)
├── outputs/
│   ├── 02_cleaned_dataset.csv                # data + engineered features (1,200 x 28)
│   ├── 03_model_artifact.joblib              # final tuned Random Forest pipeline
│   ├── 04_business_report.pdf                # business report (built by build_report.py)
│   └── chart*.png                            # figures used in the notebook and report
├── 01_data_science_notebook.ipynb            # complete analysis
├── build_report.py                           # generates the PDF from saved charts
├── requirements.txt
└── 05_README.md
```

## Setup

1. Python 3.10 or newer.
2. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
3. Install packages: `pip install -r requirements.txt`
   (or: `pip install pandas numpy scikit-learn matplotlib seaborn shap scipy joblib ipykernel reportlab`)
4. Place the raw CSV in `data/`.

## Execution steps

1. Open `01_data_science_notebook.ipynb` in VS Code and select the `.venv` kernel.
2. Use **Restart, then Run All**. The notebook runs top to bottom and writes charts, the cleaned dataset and the model to `outputs/`.
3. Run `python build_report.py` to create `outputs/04_business_report.pdf`.

The hyperparameter search (RandomizedSearchCV) is the slowest step and can take a few minutes.

## Reproducibility

- Random seed: **42** (train/test split, CV folds, model seeds, random-contact simulation).
- Package versions seen during development: pandas 3.0.6, scikit-learn 1.9.1, numpy 2.5.3. Full versions: `requirements.txt` (`pip freeze`).
- Split: stratified 80/20 (960 train, 240 test). The test set is used once, at final evaluation.

## Method summary

| Stage | What was done |
|---|---|
| Data audit | Types, missing values (2-4% in four columns), duplicates (none), outliers, logical checks (total_charges vs monthly_charges x tenure), target balance (86.3% churn). No rows deleted. |
| Preprocessing | `Pipeline` + `ColumnTransformer`: median imputation and scaling for numeric; most-frequent imputation and one-hot encoding for categorical. Fitted on training data only. `customer_id` excluded. |
| EDA | Six charts: contract, satisfaction, usage (box and bands), contract x usage interaction, tenure / late payments / payment method. |
| Features | `charge_per_gb`, `charge_per_tenure`, `high_usage_flag`, `payment_risk_flag`, `risk_events`, `low_satisfaction_flag`, `mtm_x_usage`, plus the audit flag `charge_inconsistent`. All are row-wise and do not use the target. |
| Models | Logistic Regression, Random Forest, HistGradientBoosting; baseline and tuned versions. |
| Tuning | RandomizedSearchCV, 20 iterations per model, 5-fold stratified CV, scored by ROC-AUC. `class_weight` (None / balanced) was part of each search. |
| Imbalance | Class weights were tested (not selected). No resampling (only 164 stayers). Threshold chosen from the 20% contact budget, not 0.50. |
| Evaluation | Precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, threshold curve, calibration curve, Brier score. |
| Robustness | Fold-to-fold ROC-AUC variation and a sensitivity test excluding suspect-charge rows. |
| Explainability | Permutation importance, SHAP (TreeExplainer), three individual customer explanations. |
| Simulation | Rank-based top-20% targeting vs 5,000 random draws; cost-benefit at several save rates. |

## Key results

- Selected model: tuned Random Forest, CV ROC-AUC 0.884 +/- 0.020.
- Test set: ROC-AUC 0.905, PR-AUC 0.984 (no-skill baseline 0.862).
- Top-20% targeting: 48 of 48 contacted customers were churners (random: about 41); lift 1.16x, the maximum possible at 86% churn.
- Usage alone gives test ROC-AUC 0.848; the full model adds modestly.

## Assumptions

- Churn label `1` means the customer left (consistent with higher churn for month-to-month contracts and lower satisfaction).
- `monthly_usage_gb` is measured before the prediction window (cannot be verified from the file).
- The company can contact only 20% of customers.
- **Hypothetical business inputs:** contact cost $10; retained-customer value $300; save rate 15% (sensitivity 5-30%); no benefit from contacting non-churners; same save rate for all customers.
- Cells with fewer than about 30 customers (for example, two-year contract with 0-25 GB, n=18) are indicative only.

## Limitations

- Small dataset; the test set has only 33 customers who stayed, so test metrics are noisy.
- The 86% churn rate is atypical; verify against the real customer base.
- Model outputs show association, not causation. A controlled retention pilot is needed to measure real save rates.
- Churn probability is not the same as persuadability; an uplift model would be a natural next step.

## Output descriptions

| File | Description |
|---|---|
| `01_data_science_notebook.ipynb` | Full analysis with documented decisions |
| `outputs/02_cleaned_dataset.csv` | Cleaned data with engineered features |
| `outputs/03_model_artifact.joblib` | Fitted pipeline; load with `joblib.load(...)` and call `.predict_proba(X)[:, 1]` |
| `outputs/04_business_report.pdf` | Business report (7-8 pages) |
| `05_README.md` | This file |

### Using the saved model

```python
import joblib, pandas as pd
model = joblib.load("outputs/03_model_artifact.joblib")
X_new = pd.read_csv("new_customers.csv")          # same columns as the training features
X_new = X_new.drop(columns=["customer_id", "churn"], errors="ignore")
risk = model.predict_proba(X_new)[:, 1]            # churn probability; rank and contact the top 20%
```

New data must include the engineered features and `charge_inconsistent`, built exactly as in the notebook.

"""Builds 04_business_report.pdf from the charts saved in outputs/.
Run from the project folder:  python build_report.py
All numbers below come from the notebook results; update them if you re-run with a different seed.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image,
                                Table, TableStyle, PageBreak)

OUT = "outputs"
PDF = os.path.join(OUT, "04_business_report.pdf")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceAfter=6, textColor=colors.HexColor("#1f3a5f"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1f3a5f"))
BODY = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.3, leading=12.8, spaceAfter=4)
SMALL = ParagraphStyle("S", parent=BODY, fontSize=8, leading=10.5, textColor=colors.HexColor("#444444"))
BUL = ParagraphStyle("BL", parent=BODY, leftIndent=12, bulletIndent=2)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=21, textColor=colors.HexColor("#1f3a5f"), spaceAfter=4)


def p(t): return Paragraph(t, BODY)
def b(t): return Paragraph(t, BUL, bulletText="\u2022")
def s(t): return Paragraph(t, SMALL)


def img(name, width_cm):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        return Paragraph(f"[missing chart: {name}]", SMALL)
    iw, ih = ImageReader(path).getSize()
    w = width_cm * cm
    return Image(path, width=w, height=w * ih / iw)


def table(data, col_widths, header=True):
    cells = [[Paragraph(str(c), SMALL) for c in row] for row in data]
    t = Table(cells, colWidths=[w * cm for w in col_widths], repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if header:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6edf5")))
    t.setStyle(TableStyle(st))
    return t


def chart_grid(items, width_cm):
    """items = [(filename, caption), ...] laid out two per row."""
    rows = []
    for i in range(0, len(items), 2):
        row = []
        for name, cap in items[i:i + 2]:
            if name is None:
                row.append([cap])
            else:
                row.append([img(name, width_cm), s(cap)])
        while len(row) < 2:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[8.6 * cm, 8.6 * cm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "Customer Churn Prediction - Business Report")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


story = []

# ---------------- Page 1: summary ----------------
story += [Paragraph("Customer Churn Prediction and Retention Targeting", TITLE),
          s("Business report | Dataset: 1,200 subscription customers | Random seed 42"),
          Spacer(1, 8),
          Paragraph("1. Executive summary", H1),
          p("A subscription provider can contact only about 20% of customers in the next retention cycle. "
            "We built and compared three classification models to rank customers by churn risk and to explain the ranking. "
            "A tuned Random Forest was selected."),
          b("<b>Performance (held-out test set, 240 customers):</b> ROC-AUC 0.905; PR-AUC 0.984 against a no-skill baseline of 0.862."),
          b("<b>Usage is the dominant signal.</b> Churn rises from about 52% for customers using under 25 GB a month to about 99% above 75 GB. "
            "Usage alone gives ROC-AUC 0.848; the full model reaches 0.905."),
          b("<b>The data is unusual:</b> 86.3% of customers churned (typical real-world rates are 10-30%). Accuracy is therefore misleading: "
            "predicting 'churn' for everyone scores 86% accuracy and finds nothing. We judged models by ranking quality (ROC-AUC, PR-AUC, top-20% precision)."),
          b("<b>Targeting result:</b> the 48 highest-risk test customers were all real churners (precision 100%); a random 48 would contain about 41. "
            "Lift is 1.16x, which equals the theoretical maximum at this churn rate. Because almost everyone churns, the model's absolute advantage over random contact is small."),
          b("<b>Economics (hypothetical inputs):</b> with a $10 contact cost and $300 value per retained customer, model-based contact breaks even at a 3.3% save rate "
            "(random contact: 3.9%)."),
          Spacer(1, 6),
          Paragraph("Key results", H2),
          table([["Item", "Result"],
                 ["Selected model", "Random Forest (tuned), 5-fold CV ROC-AUC 0.884 +/- 0.020"],
                 ["Test ROC-AUC / PR-AUC", "0.905 / 0.984 (no-skill PR-AUC 0.862)"],
                 ["Operating rule", "Contact the top 20% by predicted churn probability (business budget)"],
                 ["Top-20% precision / recall (test, 48 of 240)", "1.000 / 0.232 (recall is capped near 23% by the 20% budget at 86% churn)"],
                 ["Calibration", "Close to the diagonal; Brier score 0.0845 vs 0.1178 for a constant predictor"],
                 ["Robustness", "Excluding 4 suspect-charge training rows: CV ROC-AUC 0.876 vs 0.884 (within fold noise)"]],
                [6.0, 11.2]),
          PageBreak()]

# ---------------- Page 2: data audit + features ----------------
story += [Paragraph("2. Data audit and preparation", H1),
          p("The file has 1,200 rows and 20 columns. No duplicate rows or duplicate customer IDs were found. "
            "<b>customer_id</b> is an identifier and was excluded from the model. No observation was deleted; every decision is listed below."),
          table([["Issue", "Finding", "Decision and reason"],
                 ["Missing values", "satisfaction_score 4.0%, monthly_usage_gb 3.0%, monthly_charges 2.5%, total_charges 2.0%; missingness not linked to churn (differences within sampling noise)",
                  "Median imputation inside the pipeline, fitted on training data only (prevents leakage)"],
                 ["Inconsistent charges", "5 customers have monthly_charges about 3x the value implied by total_charges / tenure",
                  "Kept and flagged (charge_inconsistent); sensitivity test run"],
                 ["High monthly charges (7 others)", "Consistent with total_charges / tenure", "Kept: legitimate high spenders"],
                 ["Usage outliers", "Values up to 467 GB, all churners", "Kept: plausible extreme users"],
                 ["Skewed totals", "IQR rule flags 14 high total_charges", "Kept: long-tenure, high-price customers"],
                 ["Categorical values", "No typos or mixed spellings", "No change"],
                 ["Target imbalance", "86.3% churned (1,036) vs 13.7% stayed (164)",
                  "Class weights tested in tuning; not selected. Resampling avoided (only 164 stayers); threshold set by business budget"]],
                [3.3, 7.2, 6.7]),
          Spacer(1, 6),
          Paragraph("3. Feature engineering (7 features, none uses the target)", H1),
          table([["Feature", "Rationale"],
                 ["charge_per_gb", "Value for money: price paid per GB used"],
                 ["charge_per_tenure", "Price pressure on newer customers"],
                 ["high_usage_flag (>= 75 GB)", "Threshold effect seen in the usage chart"],
                 ["payment_risk_flag (>= 2 late payments)", "Financial-stress signal; churn jumps from about 85% to 93% at 2+"],
                 ["risk_events", "Complaints plus late payments: cumulative service/payment friction"],
                 ["low_satisfaction_flag (<= 5)", "Dissatisfaction indicator"],
                 ["mtm_x_usage", "Interaction: month-to-month contract combined with usage"]],
                [5.3, 11.9]),
          Spacer(1, 4),
          p("<b>Leakage control.</b> Every feature is computed row by row from that customer's own attributes; none uses the churn column or statistics from other customers. "
            "Imputation and scaling are fitted inside cross-validation folds. Single-feature AUC (direction-adjusted) was at most 0.77, far from a target proxy. "
            "<b>Assumption:</b> monthly_usage_gb is measured before the prediction window; the file does not confirm this, and if usage were recorded during exit the model would overstate real-world performance. "
            "The 75 GB and satisfaction cut-offs were read from exploratory charts on the full data, a minor and documented risk."),
          PageBreak()]

# ---------------- Pages 3-4: EDA ----------------
story += [Paragraph("4. Exploratory analysis", H1),
          chart_grid([
              ("chart1_contract.png", "<b>Contract.</b> Month-to-month churn is about 91% vs about 79% for one- and two-year contracts, which look alike."),
              ("chart2_satisfaction.png", "<b>Satisfaction.</b> Churn falls steadily from about 94% (score 1-3) to about 78% (9-10)."),
              ("chart3_usage.png", "<b>Usage by outcome.</b> Churners use far more data (median about 70 GB vs about 30 GB); the extreme points are all churners."),
              ("chart4_usage_bands.png", "<b>Non-linear usage effect.</b> Churn rises from about 52% to about 99% by 75 GB, then plateaus."),
              ("chart5_interaction.png", "<b>Interaction.</b> Contract protects light users (two-year, 0-25 GB: 28%) but not heavy users (about 99-100% above 75 GB). "
                                         "The 28% cell has only 18 customers, so it is indicative."),
              (None, Paragraph("<b>Unusual observations.</b> Five customers show monthly charges about three times what their lifetime totals imply "
                               "(likely entry errors, not provable). Seven other high-charge customers match their totals and are treated as legitimate. "
                               "Customers with extreme usage (up to 467 GB) all churned and are plausible heavy users. "
                               "<b>Hypotheses</b> (untested): heavy users hit data limits or overage charges; or they are more price-sensitive and receive competitor offers.", SMALL)),
          ], 6.6),
          img("chart6_tenure_late_payment.png", 16.5),
          s("<b>Tenure, late payments, payment method.</b> Tenure and payment method show weak, overlapping effects; 2+ late payments lifts churn to about 93%. "
            "The y-axis is truncated (0.70-1.00) to show small differences."),
          Spacer(1, 8)]

# ---------------- Page: modeling ----------------
story += [Paragraph("5. Modeling and evaluation", H1),
          p("Stratified 80/20 split (960 train / 240 test); the test set was used once at the end. "
            "All preprocessing sits in a Pipeline/ColumnTransformer. Search strategy: RandomizedSearchCV, 20 iterations per model, 5-fold stratified CV on the training set, scored by ROC-AUC (seed 42)."),
          table([["Model", "ROC-AUC baseline", "ROC-AUC tuned", "PR-AUC tuned", "Top-20% precision tuned"],
                 ["Logistic Regression", "0.870 +/- 0.046", "0.875 +/- 0.045", "0.974", "0.990"],
                 ["Random Forest", "0.867 +/- 0.025", "0.884 +/- 0.020", "0.978", "0.990"],
                 ["HistGradientBoosting", "0.865 +/- 0.026", "0.885 +/- 0.024", "0.977", "0.985"]],
                [4.2, 3.4, 3.4, 2.7, 3.5]),
          Spacer(1, 4),
          p("<b>Model selection.</b> The three tuned models are statistically tied (differences are smaller than fold-to-fold noise). "
            "Random Forest was chosen for the best PR-AUC, the most stable folds (std 0.020) and straightforward explainability. "
            "class_weight=None won all three searches, so reweighting was not needed for ranking."),
          p("<b>Why accuracy is insufficient.</b> At 86% churn, 'always predict churn' reaches 86% accuracy. At the default 0.50 threshold the model reaches about 87% accuracy "
            "but identifies only 4 of 33 stayers. At the business threshold accuracy is just 38%, yet every flagged customer is a true churner."),
          table([["Test set, Random Forest", "Contacted", "Precision", "Recall", "F1", "Confusion matrix [[TN, FP], [FN, TP]]"],
                 ["Business threshold (0.991)", "25%", "1.000", "0.285", "0.444", "[[33, 0], [148, 59]]"],
                 ["Default 0.50", "97%", "0.876", "0.986", "0.927", "[[4, 29], [3, 204]]"]],
                [4.0, 1.9, 1.9, 1.6, 1.4, 6.4]),
          s("The 0.991 threshold was set from out-of-fold training predictions as the 80th percentile of risk. On new data it flagged 25%, not 20%, because many predictions cluster near 1.0; the simulation therefore uses an exact rank-based top 20%."),
          Spacer(1, 4),
          chart_grid([
              ("chart7_threshold.png", "<b>Precision/recall across thresholds</b> (out-of-fold, train). Precision stays above 0.89 everywhere; recall falls as the list shortens."),
              ("chart8_calibration.png", "<b>Calibration.</b> Points follow the diagonal within 2-3 points (slight over-prediction near 0.5-0.7). Probabilities can be read as risk estimates."),
          ], 7.4),
          PageBreak()]

# ---------------- Page: explainability ----------------
story += [Paragraph("6. Explainability", H1),
          p("We used permutation importance (drop in test ROC-AUC when a feature is shuffled, 20 repeats) and SHAP values for the Random Forest."),
          table([["Feature", "AUC drop when shuffled"],
                 ["monthly_usage_gb", "0.137"], ["mtm_x_usage", "0.020"], ["satisfaction_score", "0.013"],
                 ["charge_per_tenure", "0.006"], ["all others", "0.003 or less (mostly within noise)"]],
                [6.0, 6.0]),
          Spacer(1, 4),
          p("Usage is roughly seven times more important than the next feature. Contract type, late payments and tenure show little importance once usage is in the model, "
            "consistent with the heatmap (contract matters mainly for light users). Correlated usage features share credit, so each appears smaller than it would alone."),
          chart_grid([("chart10_permutation.png", "<b>Permutation importance</b> (test set)."),
                      ("chart11_shap_summary.png", "<b>SHAP summary</b>: effect of each feature on predicted churn probability.")], 7.6),
          img("chart12_individual_shap.png", 16.5),
          s("<b>Three customers.</b> Row 804: predicted 1.00, churned (96.5 GB, month-to-month; satisfaction missing and imputed). "
            "Row 505: predicted 0.40, stayed (14.4 GB, satisfaction 6.5). Row 1064: predicted 0.97, churned (140 GB, satisfaction 4.5, 8 months tenure). "
            "The 'mid-risk' customer sits at the median prediction, which is 0.97 because most customers are high risk."),
          p("<b>Association, not causation.</b> These results describe what the model uses to predict churn. High usage predicts churn, but this does not show that limiting usage "
            "or changing a customer's plan would retain them. Testing retention actions requires a controlled experiment."),
          PageBreak()]

# ---------------- Page: simulation ----------------
story += [Paragraph("7. Retention intervention simulation", H1),
          p("<b>Assumptions (hypothetical):</b> contact cost $10 per customer; value of a retained customer $300; save rate among contacted churners 15% "
            "(varied from 5% to 30%); contacting a customer who would not churn brings no benefit; the same save rate applies to everyone (no uplift modeling). "
            "Customers in the test set (240) were ranked by predicted churn probability and the top 20% (48) were 'contacted'."),
          table([["Strategy", "Churners reached (of 48)", "Precision", "Share of all 207 churners"],
                 ["Model top 20%", "48", "100%", "23.2%"],
                 ["Random 20% (5,000 draws)", "41.4 (95% range 37-45)", "86%", "20.0%"]],
                [5.0, 4.8, 3.0, 4.4]),
          s("Lift = 1.16x, equal to the maximum possible (1 / 0.862) at this churn rate."),
          Spacer(1, 4),
          table([["Save rate", "Net value, model ($)", "Net value, random ($)", "Model gain ($)"],
                 ["5%", "240", "141", "99"], ["10%", "960", "762", "198"], ["15%", "1,680", "1,383", "297"],
                 ["20%", "2,400", "2,004", "396"], ["30%", "3,840", "3,247", "593"]],
                [3.5, 4.5, 4.5, 4.0]),
          s("Break-even save rate: model 3.3%, random 3.9%. Figures are for the 240-customer test set; scale roughly 5x for all 1,200 customers."),
          p("<b>Interpretation.</b> The campaign is profitable under these assumptions for almost any save rate, but most of that value comes from the offer itself, not from the model, "
            "because random contact already reaches mostly churners. The model's value rises where churn is lower or where contact budgets are tighter. "
            "A more valuable next step is an uplift model or a controlled test to find customers who are <i>persuadable</i>, since a high churn probability does not mean an offer will work."),
          Spacer(1, 6),
          Paragraph("8. Findings and retention actions", H1),
          Paragraph("Patterns supported by the data (evidence)", H2),
          b("Heavy users leave: churn is about 93% at 50-75 GB and about 99% above 75 GB, against about 52% below 25 GB."),
          b("Contract commitment helps only light users; above about 75 GB all contracts churn at 99-100%."),
          b("Lower satisfaction goes with higher churn (about 94% vs 78%), and is the second independent signal after usage."),
          b("Two or more late payments go with about 93% churn vs 84-85% for 0-1; a moderate signal."),
          PageBreak()]

# ---------------- Page: recommendations ----------------
story += [Paragraph("Recommended actions (evidence vs assumption)", H1),
          table([["#", "Action", "Evidence from data", "Business assumption (untested)"],
                 ["1", "Proactive plan review for customers above about 50 GB: right-size the plan, offer a heavy-user tier or usage alerts",
                  "Churn 93-99% above 50 GB; usage is the top feature", "Heavy users hit limits or overage charges; an adapted plan would reduce exits"],
                 ["2", "Offer commitment discounts to light and moderate month-to-month users (under about 50 GB)",
                  "Contract lowers churn only at low usage (heatmap; small cells)", "A discount is cheaper than the lost revenue; customers accept contracts"],
                 ["3", "Service-recovery call for customers scoring satisfaction of 5 or below",
                  "Churn about 94% in the lowest band vs 78% in the highest; second-ranked feature", "A follow-up resolves the issue and lifts satisfaction"],
                 ["4", "Payment-friction outreach: autopay and flexible due dates after 2 late payments",
                  "About 93% churn at 2+ late payments vs 84-85%; weak importance in the model", "Late payments reflect friction, not intent to leave"],
                 ["5", "Run a randomized pilot (treat vs hold-out) to measure the real save rate before scaling",
                  "Simulation is highly sensitive to the assumed save rate; association is not causation", "A pilot is affordable and results transfer to the full base"]],
                [0.7, 5.4, 5.6, 5.5]),
          Spacer(1, 8),
          Paragraph("9. Limitations and reproducibility", H1),
          b("Small sample: 1,200 customers; the test set has only 33 stayers, so test metrics are noisy. Fold-to-fold ROC-AUC ranged from 0.86 to 0.92."),
          b("The 86% churn rate is atypical; confirm that the label 1 means 'churned' and that the data reflect the target population."),
          b("Usage timing relative to the prediction window is unverified (possible leakage if recorded at or after exit)."),
          b("All costs, values and save rates are hypothetical. Probability is not persuadability."),
          b("Reproducibility: random seed 42; package versions are in requirements.txt; steps are in the README and the notebook."),
          ]

doc = SimpleDocTemplate(PDF, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title="Customer Churn Prediction - Business Report")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("Saved", PDF)

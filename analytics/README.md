# Module 2 — Titanic Analytics and Machine Learning

## Overview

This module performs exploratory data analysis, statistical analysis, visualization, classification, class-imbalance analysis, Random Forest hyperparameter tuning, and multivariate linear regression using the classic Titanic dataset.

The dataset was loaded once using Seaborn's `load_dataset("titanic")` and immediately saved as `titanic.csv`. All subsequent analysis uses the saved dataset and the cleaned DataFrame derived from it.

---

## Project Structure

```text
analytics/
├── README.md
├── titanic.csv
├── titanic_analysis.ipynb
├── models/
│   └── best_titanic_classifier.joblib
├── plots/
└── outputs/
```

---

## 1. Dataset Profiling

The original Titanic dataset contains:

- 891 rows
- 15 columns

Important variables include:

- `survived`
- `pclass`
- `sex`
- `age`
- `sibsp`
- `parch`
- `fare`
- `embarked`

The original dataset contains missing values in:

| Column | Missing Count | Missing % |
|---|---:|---:|
| `age` | 177 | 19.87% |
| `embarked` | 2 | 0.22% |
| `deck` | 688 | 77.22% |
| `embark_town` | 2 | 0.22% |

---

## 2. Missing-Value Treatment

The missing-value strategy was selected according to the percentage of missing observations.

- `age` had 19.87% missing values and was imputed using the median.
- `embarked` had 0.22% missing values, so the two affected rows were removed.
- `embark_town` had 0.22% missing values and was removed because it duplicates the information represented by `embarked`.
- `deck` had 77.22% missing values and was removed because of its very high missingness.

After cleaning, the dataset contained:

- 889 rows
- 13 columns
- 0 remaining missing values

---

## 3. Univariate Analysis

Histograms and box plots were created for `age` and `fare`.

### Age

- Q1 = 22.00
- Q3 = 35.00
- IQR = 13.00
- Lower bound = 2.50
- Upper bound = 54.50
- IQR outliers = 65

### Fare

- Q1 = 7.90
- Q3 = 31.00
- IQR = 23.10
- Lower bound = -26.76
- Upper bound = 65.66
- IQR outliers = 114

Fare statistics:

- Mean = 32.0967
- Median = 14.4542
- Mode = 8.0500
- Skewness = 4.8014

Because mean > median > mode and skewness is strongly positive, fare is strongly right-skewed.

The detected outliers were retained because the analysis requirement was to identify and interpret them rather than automatically remove them.

---

## 4. Bivariate Analysis

### Survival by Sex

- Female survival rate = 74.04%
- Male survival rate = 18.89%

### Survival by Passenger Class

- 1st class = 62.62%
- 2nd class = 47.28%
- 3rd class = 24.24%

### Survival by Sex and Class

| Sex | Class | Survival Rate |
|---|---:|---:|
| Female | 1 | 96.74% |
| Female | 2 | 92.11% |
| Female | 3 | 50.00% |
| Male | 1 | 36.89% |
| Male | 2 | 15.74% |
| Male | 3 | 13.54% |

These results show a strong relationship between sex, passenger class, and survival.

---

## 5. Correlation Analysis

The required correlation matrix used:

- `survived`
- `pclass`
- `age`
- `sibsp`
- `parch`
- `fare`

The two strongest absolute off-diagonal correlations were:

1. `pclass` and `fare` = -0.548
2. `sibsp` and `parch` = 0.415

The negative correlation between passenger class and fare reflects the fact that lower numerical class values represent higher passenger classes, which generally paid higher fares.

---

## 6. Multivariate Analysis

Four distinct multivariate visualizations were created:

1. Age, Fare and Survival
2. Age, Sex and Survival
3. Fare, Passenger Class and Survival
4. Survival Rate by Sex and Passenger Class

These visualizations demonstrate relationships among demographic, socioeconomic, travel, and survival variables.

---

## 7. Exploratory Standardization

`age` and `fare` were standardized using `StandardScaler`.

Before standardization:

| Statistic | Age | Fare |
|---|---:|---:|
| Mean | 29.3152 | 32.0967 |
| Std | 12.9849 | 49.6975 |

After standardization:

| Statistic | Age | Fare |
|---|---:|---:|
| Mean | 0.0000 | 0.0000 |
| Std | 1.0006 | 1.0006 |

This transformation was used only for exploratory analysis and was not used as the modeling preprocessing step.

---

## 8. Classification

The classification target was `survived`.

Features used:

- `pclass`
- `sex`
- `age`
- `sibsp`
- `parch`
- `fare`
- `embarked`

An 80/20 stratified train/test split was used.

### Baseline Models

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.8090 | 0.7833 | 0.6912 | 0.7344 | 0.8610 |
| Decision Tree | 0.7640 | 0.7600 | 0.5588 | 0.6441 | 0.8374 |
| Random Forest | 0.8090 | 0.7656 | 0.7206 | 0.7424 | 0.8196 |

---

## 9. Class Imbalance

Two imbalance-handling approaches were compared with the baseline models:

- `class_weight="balanced"`
- SMOTE

The Balanced Random Forest achieved:

- Accuracy = 0.8146
- Precision = 0.7536
- Recall = 0.7647
- F1 = 0.7591
- ROC-AUC = 0.8204

This was the strongest overall configuration based on the balance between precision, recall, F1-score, and accuracy.

---

## 10. Random Forest Hyperparameter Tuning

GridSearchCV was used with 5-fold cross-validation.

Parameters searched:

- `n_estimators`
- `max_depth`
- `max_features`

Best parameters:

```text
n_estimators = 200
max_depth = 15
max_features = sqrt
```

Best cross-validation F1-score:

```text
0.7471
```

OOB score:

```text
0.8073
```

The tuned Random Forest achieved approximately 81% accuracy on the held-out test set.

---

## 11. Multivariate Linear Regression

The regression task predicted `fare` using the other available features.

Test-set results:

| Metric | Result |
|---|---:|
| MAE | 21.0986 |
| RMSE | 41.7021 |
| R² | 0.3482 |
| Adjusted R² | 0.3091 |

The model explains approximately 34.82% of the variation in fare.

The residual plot shows increasing residual spread at higher predicted fare values, indicating evidence of heteroscedasticity. This is consistent with the strong right-skewness and high-fare outliers identified during exploratory analysis.

---

## 12. Final Deployment Recommendation

The Balanced Random Forest is recommended as the final classifier.

It achieved:

- Accuracy = 81.46%
- Precision = 75.36%
- Recall = 76.47%
- F1-score = 75.91%

It provides the best overall balance between identifying survivors and avoiding excessive false-positive predictions among the evaluated configurations.

Logistic Regression achieved a higher ROC-AUC, while SMOTE Logistic Regression achieved the highest ROC-AUC overall at 0.8667. However, the Balanced Random Forest provided the strongest combined precision, recall, F1-score, and accuracy for the selected deployment objective.

---

## 13. Saved Model

The final complete preprocessing and classification pipeline was saved using Joblib:

```text
models/best_titanic_classifier.joblib
```

The pipeline contains:

- Missing-value preprocessing
- Numerical scaling
- Categorical encoding
- Balanced Random Forest classifier

The saved pipeline was successfully reloaded using `joblib.load()`.

A raw passenger record was then supplied directly to the reloaded pipeline, successfully producing a survival prediction and probability.

---

## Technologies Used

- Python
- Pandas
- NumPy
- Seaborn
- Matplotlib
- Scikit-learn
- Imbalanced-learn
- Joblib
- Jupyter Notebook
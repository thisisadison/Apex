# Formula 1 Top-5 Finish Predictor

A machine learning project that predicts whether a Formula 1 driver will finish in the top 5 of the Singapore Grand Prix, using only information available before qualifying. It started as an NTU SC1015 (Introduction to Data Science and AI) mini-project and has since been rebuilt as a reproducible pipeline with a Claude-powered question-answering agent on top.

## Highlights

- **Leakage-aware evaluation.** Models are tested on later seasons than they were trained on, and class balancing is applied to the training set only.
- **Pre-qualifying features only.** Grid position is a strong predictor, but it is not known until qualifying. It is deliberately excluded so the model can be used as soon as the previous race ends.
- **Four model families compared.** Random Forest, Logistic Regression, SVM and Histogram Gradient Boosting, each with a baseline and a grid-searched version.
- **Singapore-only vs multi-circuit.** The pipeline checks whether training on every circuit improves predictions for Singapore, and exports whichever model scores better.
- **Agent demo.** `f1_agent.py` lets Claude answer questions about drivers by calling the dataset lookup and the trained model as tools.

## Results

Held-out test set: 100 driver entries from the Singapore GP in 2019 and 2022-2025. All models are trained on 2008-2018 (plus 2020-2021 for the multi-circuit model).

| Model | Singapore-only (tuned) | Multi-circuit (tuned) |
|---|---|---|
| Random Forest | 83% | 85% |
| Logistic Regression | 82% | 87% |
| SVM | 81% | 82% |
| Histogram Gradient Boosting | **84%** | **88%** |

The exported model is the multi-circuit Histogram Gradient Boosting model (88% on the held-out Singapore races).

Results from one run of `python pipeline.py --data-dir data`. See Limitations before relying on these numbers.

## Approach

1. **Data.** Historical Formula 1 results, races, drivers, qualifying, lap times and pit stops for 2008-2022 (Kaggle and official Formula 1 data) in `data/`. Seasons from 2023 onward are fetched from the [Jolpica-F1](https://api.jolpi.ca/ergast) API with `fetch_data.py` and `fetch_all_circuits_data.py`.
2. **Features** (`pipeline.py`), all known before qualifying:
   - `driver_standing_before` and `constructor_standing_before`: championship standing coming into the race
   - `years_experience` and `is_rookie`
   - `driver_circuit_avg_finish`: the driver's average finishing position at that circuit in earlier years
   - `driver_recent_form` and `constructor_recent_form`: recency-weighted results over recent races
   - `circuit_id` (one-hot encoded, multi-circuit model)
3. **Target.** `top5`, whether the driver finished in the top 5.
4. **Split.** Chronological: the most recent Singapore GPs form the test set, so the model is never judged on a race that happened before part of its training data.
5. **Balancing.** The top-5 class is upsampled on the training set only, after the split.
6. **Training and selection.** Each model is run as a baseline and tuned with 5-fold `GridSearchCV`. The best tuned model is refit on all available data and saved to `model.pkl`.

### Design decision: dropping grid position

Starting grid position has a correlation of about -0.57 with a top-5 finish, second only to championship standing. Removing it costs roughly 4 points of accuracy (about 87% to 83% in earlier testing), but it makes the model usable well before qualifying instead of only the day before the race.

## Repository structure

| Path | Purpose |
|---|---|
| `pipeline.py` | Loads data, builds features, trains and compares models, exports `model.pkl` |
| `f1_agent.py` | Claude tool-use agent that looks up driver stats and calls the model |
| `fetch_data.py` | Fetches recent Singapore GP data from Jolpica-F1 |
| `fetch_all_circuits_data.py` | Fetches full-season results for all circuits (2023+) |
| `SC1015 Formula 1 Mini-Project.ipynb` | Original exploratory analysis and modelling |
| `SC1015 Mini-Project Slides.pptx` | Course presentation |
| `data/` | Historical and freshly fetched CSVs |
| `model.pkl` | Exported trained model |

## Getting started

```bash
pip install pandas numpy scikit-learn joblib requests matplotlib seaborn anthropic

# Train, compare and export the model
python pipeline.py --data-dir data --model-out model.pkl

# Optional: fetch more recent seasons first
python fetch_data.py --years 2023 2024 2025 --out data/singapore_fresh.csv
python fetch_all_circuits_data.py --years 2023 2024 2025 --out data/multi_circuit_fresh.csv
```

Training runs a grid search for four models on two datasets, so it takes several minutes.

### Agent demo

```bash
export ANTHROPIC_API_KEY="your-key"
python f1_agent.py
```

Ask questions such as "Did Hamilton finish in the top 5 in the 2018 Singapore GP, and would the model have predicted it?". The agent decides whether to call `get_driver_stats` (lap and pit data for a driver and year) or `predict_top5` (the trained model's prediction) and answers from the results.

## Limitations

- **Small test set.** The held-out set is 100 driver entries from five races, so a difference of a few points is within noise.
- **Selection on the test set.** The reported best model is chosen by its held-out test accuracy, so the headline figure is slightly optimistic. A separate validation split, or cross-validation by season, would give a cleaner estimate.
- **Accuracy only.** Reported figures are accuracy; the top-5 class is a minority class, and the per-class precision and recall printed by `pipeline.py` are worth checking.
- **Singapore focus.** The multi-circuit model is trained on all circuits but evaluated only on Singapore.
- **Not a betting tool.** The model uses pre-race standings and form and does not model race-day events such as safety cars, weather or crashes.

## Data sources

- Kaggle Formula 1 datasets and official Formula 1 data (2008-2022)
- [Jolpica-F1](https://api.jolpi.ca/ergast), an Ergast-compatible API (2023 onward)
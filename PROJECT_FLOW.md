# AI Logic for Analyst Project Flow

## Goal
Build a small AI-powered analyst workflow for security or system monitoring that reads Windows event logs, converts them into structured data, and highlights useful patterns.
## Simple Flow
1. Collect logs from `system_logs.evtx`
2. Parse important fields like event ID, provider, level, timestamp, and message
3. Save the parsed data into `logs_dataset.csv`
4. Generate a quick report in `analysis_summary.txt`
5. Use the CSV later for AI tasks such as anomaly detection, classification, or alert generation

## Current Files
- `python.py`: main pipeline script
- `system_logs.evtx`: input Windows event log file
- `logs_dataset.csv`: structured output dataset
- `analysis_summary.txt`: quick analysis report

## Suggested Project Architecture
1. Data ingestion
   Read `.evtx` log files
2. Data preprocessing
   Clean missing values and normalize fields
3. Feature extraction
   Use event IDs, providers, frequency, time patterns
4. AI analysis
   Train multiple machine learning models to detect suspicious events or anomalies
5. Reporting
   Show summary, charts, or alerts in a dashboard

## Machine Learning Training Flow
1. Run `python.py` to build the structured dataset
2. Run `train_models.py` to train multiple anomaly detection models
3. Save trained models inside `trained_models/`
4. Review `trained_models/model_training_report.txt`
5. Inspect `trained_models/
anomaly_scores.csv` for suspicious rows

## Frontend Flow
1. Run `python app.py`
2. Open `http://127.0.0.1:5000` in your browser
3. Browse all logs in a table
4. Filter by provider, level, event ID, or message text
5. View suspicious rows when anomaly scores are available

## DevOps Stack
1. Run `docker compose up --build`
2. Open the Flask app at `http://127.0.0.1:5000`
3. Open Prometheus at `http://127.0.0.1:9090`
4. Open Grafana at `http://127.0.0.1:3000`
5. Log in to Grafana with `admin` / `admin`
6. Review the preloaded `AI Logic for Analyst Overview` dashboard

## Models Included
- Isolation Forest
- Local Outlier Factor
- SGD One-Class SVM
- MiniBatch KMeans

## Future Improvements
- Add severity labels like low, medium, high
- Detect repeated failures or suspicious login events
- Train a machine learning model on historical logs
- Add charts, exports, or REST API endpoints to the Flask dashboard
- Export suspicious events into a separate CSV file
- Add alert rules for anomaly spikes and service health

## One-Line Project Explanation
AI Logic for Analyst is a project that converts Windows event logs into structured data and uses analysis or machine learning to find important patterns, anomalies, and security issues.

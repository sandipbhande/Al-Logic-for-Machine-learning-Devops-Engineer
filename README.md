# AI Logic for Analyst

AI Logic for Analyst is a small AI-powered analyst workflow for security and system monitoring. It reads Windows event logs from an `.evtx` file, converts them into structured data, generates a quick summary report, and prepares the dataset for anomaly detection, classification, and alerting workflows.

It also includes a small DevOps and observability stack with Docker Compose, Prometheus, and Grafana so analysts can view application health, dataset metrics, and request activity alongside the log analysis workflow.

## Project Flow

### Simple Flow

1. Collect logs from `system_logs.evtx`
2. Parse important fields like event ID, provider, level, timestamp, and message
3. Save the structured output into `logs_dataset.csv`
4. Generate a quick report in `analysis_summary.txt`
5. Use the CSV later for AI tasks such as anomaly detection, classification, or alert generation

## Current Files

- `python.py`: main ingestion and parsing pipeline
- `system_logs.evtx`: input Windows event log file
- `logs_dataset.csv`: structured output dataset
- `analysis_summary.txt`: quick analysis report
- `train_models.py`: anomaly detection training pipeline
- `app.py`: Flask dashboard and metrics endpoint
- `trained_models/`: saved models, anomaly scores, and training report

## Suggested Architecture

### Data Ingestion

Read `.evtx` log files and extract XML event records.

### Data Preprocessing

Clean missing values, normalize fields, and prepare timestamp and message content.

### Feature Extraction

Use event IDs, providers, computer names, message text, and time patterns such as hour and day of week.

### AI Analysis

Train multiple anomaly detection models to identify suspicious events and unusual behavior.

### Reporting

Present summary files, suspicious events, and live metrics in a lightweight dashboard.

### DevOps and Observability

Run the application stack with containerized services, scrape application metrics with Prometheus, and visualize operational trends in Grafana.

## Machine Learning Workflow

1. Run `python python.py` to build `logs_dataset.csv`
2. Run `python train_models.py` to train anomaly detection models
3. Save trained models inside `trained_models/`
4. Review `trained_models/model_training_report.txt`
5. Inspect `trained_models/anomaly_scores.csv` for suspicious rows

## Models Included

- Isolation Forest
- Local Outlier Factor
- SGD One-Class SVM
- MiniBatch KMeans

## Frontend Workflow

1. Run `python app.py`
2. Open `http://127.0.0.1:5000`
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

## DevOps Tools

- Docker Compose: starts the Flask app, Prometheus, and Grafana together
- Prometheus: scrapes the Flask `/metrics` endpoint every 15 seconds
- Grafana: shows the preloaded dashboard for loaded rows, anomaly rows, providers, event IDs, and request rate

## Grafana Dashboard

The bundled Grafana dashboard gives analysts and operators a quick operational view of the project:

- `Loaded Rows`: total rows currently loaded from the dataset
- `Anomaly Rows`: number of anomaly rows detected in the scored dataset
- `Providers`: unique Windows event providers in the dataset
- `Event IDs`: unique Windows event IDs in the dataset
- `Request Rate`: recent traffic to the Flask endpoints grouped by route and method

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the parser:

```bash
python python.py
```

Train anomaly models:

```bash
python train_models.py
```

Start the dashboard:

```bash
python app.py
```

Or run the full stack with Docker:

```bash
docker compose up --build
```

Then open:

- Flask UI: `http://127.0.0.1:5000`
- Prometheus UI: `http://127.0.0.1:9090`
- Grafana UI: `http://127.0.0.1:3000`

## Outputs

- `logs_dataset.csv`: parsed Windows events
- `analysis_summary.txt`: quick statistical summary
- `trained_models/model_training_report.txt`: model results and top suspicious rows
- `trained_models/anomaly_scores.csv`: scored dataset with anomaly flags

## Future Improvements

- Add severity labels like low, medium, high
- Detect repeated failures or suspicious login events
- Train on historical logs from multiple sources
- Add charts, exports, or REST API endpoints to the Flask dashboard
- Export suspicious events into a separate CSV file
- Add alert rules for anomaly spikes and service health

## One-Line Explanation
<img width="1887" height="922" alt="Screenshot 2026-03-30 131837" src="https://github.com/user-attachments/assets/5fc7ca92-0350-402f-ae84-d912af13dbc6" />

AI Logic for Analyst converts Windows event logs into structured data and uses analysis plus machine learning to find important patterns, anomalies, and security issues.

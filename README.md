<p align="center">

# LogNomaly

### Explainable AI System for Log Anomaly Detection

AI-powered platform for detecting and explaining anomalies in large-scale system logs.

</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Machine Learning](https://img.shields.io/badge/ScikitLearn-ML-orange)
![ASP.NET](https://img.shields.io/badge/Web-ASP.NET%20Core-purple)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

---

## Overview

LogNomaly is a hybrid anomaly detection platform that analyzes system logs using machine learning and explainable AI techniques.

The system parses raw logs, extracts features, detects anomalies using multiple models, and explains predictions through an interactive web dashboard.

---

## Architecture

<p align="center">

![architecture](docs/architecture.png)

</p>

Pipeline:

```
Raw Logs
   ↓
Log Parsing
   ↓
Feature Extraction
   ↓
Hybrid Detection Engine
   ↓
Explainable AI
   ↓
Web Dashboard
```

---

## Features

* Hybrid anomaly detection (Isolation Forest + Random Forest + Rule Engine)
* Explainable AI for anomaly interpretation
* Automated log feature extraction
* Interactive web-based dashboard
* Modular ML pipeline

---

## Tech Stack

| Layer          | Technology           |
| -------------- | -------------------- |
| ML Pipeline    | Python, Scikit-learn |
| API            | Flask                |
| Web Interface  | ASP.NET Core MVC     |
| Visualization  | HTML, CSS, JS        |
| Infrastructure | Docker               |

---

## Project Structure

```
LogNomaly
│
├── app/                # Python API
├── models/             # ML models
├── utils/              # log processing
├── data/               # log data for training
├── tests/              # unit tests
├── LogNomaly.Web/      # ASP.NET dashboard
└── saved_models/       # trained models
```

---

## Installation

Clone repository

```
git clone https://github.com/dogaece-koca/LogNomaly.git
cd LogNomaly
```

Install dependencies

```
pip install -r requirements.txt
```

---

## Datasets

The system log datasets (BGL and HDFS) used for training and evaluating the machine learning models in this project were obtained from **[LogHub](https://github.com/logpai/loghub)**. 

LogHub is a freely available collection of system log datasets maintained by LogPAI, specifically curated for AI-powered log analytics, anomaly detection, and research purposes. We would like to acknowledge and thank the creators and contributors of LogHub for providing these invaluable open-source resources to the academic community. The log datasets we used are as follows:

This project uses the **Blue Gene/L (BGL) log dataset**, a widely used benchmark for log anomaly detection research.

Download link: [🔗](https://zenodo.org/records/8196385/files/BGL.zip?download=1)

Place it inside:

```
data/BGL.log
```

This project uses the **Hadoop Distributed File System (HDFS) v1 log dataset**, a popular benchmark generated in a private cloud environment.

Download link: [🔗](https://zenodo.org/records/8196385/files/HDFS_v1.zip?download=1)

Place it inside:

```
data/HDFS.log
```

---

## Train the Models

Before running the training script, open `train.py` and set the `DATASET_MODE` variable to your target dataset (either `"BGL"` or `"HDFS"`). Once configured, execute the following command:

```
python train.py
```
---

## Pre-trained Models

Due to GitHub's file size limits, the trained machine learning models for LogNomaly are hosted via GitHub Releases rather than directly in the repository.

**To run the project locally:**
1. Navigate to the [Releases](../../releases) page of this repository.
2. Download the latest release asset (`saved_models.zip`).
3. Extract the contents and place the `.joblib` model files into your designated models directory (`/saved_models`).
4. Run the application.

---
   
## Run the API

```
python app/app.py
```

---

## Run the Web Dashboard

```
cd LogNomaly.Web
dotnet run
```

Open:

```
http://localhost:5000
```
(or a specific port assigned by your local environment)

---

## Authors

Doğa Ece Koca —
Computer Engineering Student at Dokuz Eylül University

Fatmagül Fırtına —
Computer Engineering Student at Dokuz Eylül University

---

## License

MIT License

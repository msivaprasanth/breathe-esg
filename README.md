# Breathe ESG — Enterprise Emissions Data Platform

## Overview

Breathe ESG is a multi-tenant enterprise sustainability data ingestion and review platform designed to normalize heterogeneous operational ESG datasets into standardized emissions workflows.

The system ingests operational sustainability data from:

* SAP Fuel & Procurement exports
* Utility electricity exports
* Corporate travel datasets

and transforms them into normalized ESG emission records aligned to:

* Scope 1
* Scope 2
* Scope 3

under the GHG Protocol.

---

# Problem Statement

Enterprise ESG reporting systems frequently rely on fragmented operational datasets originating from:

* ERP systems
* utility providers
* procurement platforms
* travel systems

These exports are operationally inconsistent:

| Problem                 | Example                  |
| ----------------------- | ------------------------ |
| inconsistent headers    | consumption_kwh vs usage |
| mixed units             | gallons vs liters        |
| incomplete records      | missing employee IDs     |
| operational identifiers | opaque plant codes       |

The objective of this project was to design a normalized ESG ingestion workflow capable of:

* standardizing operational data
* validating anomalies
* supporting analyst review
* preserving auditability

---

# Core Features

## Multi-Source ESG Ingestion

Supports:

* SAP procurement/fuel data
* utility electricity consumption
* corporate travel exports

---

# Schema Normalization

Normalizes heterogeneous operational schemas into unified ESG records.

Examples:

```text id="h2v8n4"
consumption_kwh → consumption
billing_period_start → period_start
transport_mode → category
```

---

# Unit Normalization

Converts operational units into canonical ESG units.

| Domain      | Canonical Unit |
| ----------- | -------------- |
| Fuel        | Liters         |
| Electricity | kWh            |
| Distance    | Kilometers     |
| Mass        | Kilograms      |

---

# Scope Classification

Automatically classifies operational activities into:

| Scope   | Example               |
| ------- | --------------------- |
| Scope 1 | fuel combustion       |
| Scope 2 | purchased electricity |
| Scope 3 | travel & procurement  |

---

# Validation & Flagging

Detects operational anomalies:

* zero quantities
* missing identifiers
* unrealistic energy values
* invalid travel distances

Flagged records require analyst review.

---

# Analyst Review Workflow

Supports:

* pending review
* flagged review
* approvals
* rejections
* edit workflows

---

# Auditability

Stores:

* upload batches
* source metadata
* review actions
* deterministic row hashes

to preserve operational traceability.

---

# Technology Stack

| Layer          | Technology     |
| -------------- | -------------- |
| Backend        | Django + DRF   |
| Frontend       | React + Vite   |
| Database       | SQLite         |
| Parsing        | Pandas         |
| Authentication | DRF Token Auth |

---

# Why These Technologies?

## Django REST Framework

Selected because it provides:

* rapid API development
* ORM support
* admin tooling
* authentication primitives

This allowed focus on ESG ingestion logic rather than framework plumbing.

---

# React + Vite

Selected because:

* lightweight setup
* fast iteration
* modern frontend tooling

The frontend was designed as an operational analyst interface rather than a marketing site.

---

# Why SQLite Instead of PostgreSQL?

SQLite was intentionally selected for prototype simplicity.

Advantages:

* zero infrastructure setup
* easy portability
* fast local development

Tradeoff:

SQLite is not suitable for large-scale concurrent enterprise workloads.

Production systems should migrate to PostgreSQL.

---

# System Architecture

```text id="n8x4m1"
Enterprise CSV/XLSX Sources
        ↓
Parser Layer
        ↓
Normalization Engine
        ↓
Validation & Flagging
        ↓
Emission Records
        ↓
Analyst Review Workflow
```

---

# Supported Data Sources

## SAP Fuel & Procurement

Examples researched:

* SAP MB51
* SAP ME2M

Supports:

* fuel procurement
* operational materials
* plant normalization

---

# Utility Electricity

Supports:

* utility portal exports
* energy billing datasets
* electricity normalization

---

# Corporate Travel

Supports:

* SAP Concur-style exports
* travel reimbursement datasets
* airport distance estimation

---

# Project Structure

```text id="r4m8q6"
Breathe_ESG/
│
├── backend/
├── frontend/
├── sample_data/
│
├── README.md
├── MODEL.md
├── DECISIONS.md
├── TRADEOFFS.md
├── SOURCES.md
├── APIs.md
```

---

# Local Setup

## Backend

```bash id="p7x2m5"
cd backend

python -m venv env

env\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

---

# Frontend

```bash id="t3q9w1"
cd frontend

npm install

npm run dev
```

---

# Environment Variables

Frontend:

```env id="z6m1v4"
VITE_API_URL=http://127.0.0.1:8000
```

---

# Demo Credentials

```text id="f5r8q2"
Username: analyst1
Password: analyst123
```

---

# Sample Data

Sample datasets included:

| Dataset          | Purpose           |
| ---------------- | ----------------- |
| sap_test.csv     | Scope 1 + Scope 3 |
| utility_test.csv | Scope 2           |
| travel_test.csv  | Scope 3           |

---

# Deployment

## Frontend

Deployed using:

* Vercel

## Backend

Deployed using:

* Render

---

# Current Limitations

The prototype intentionally excludes:

* live SAP APIs
* OCR PDF parsing
* async ingestion
* SSO
* AI anomaly detection
* real emission factor engines

These are documented in:

```text id="m9v3q7"
TRADEOFFS.md
```

---

# Future Improvements

Potential roadmap:

* PostgreSQL migration
* Celery ingestion workers
* OCR utility ingestion
* supplier APIs
* real emissions calculations
* ML anomaly detection

---

# Conclusion

This project focuses on the operational realities of enterprise ESG ingestion:

* heterogeneous source systems
* inconsistent operational schemas
* normalization workflows
* governance review
* auditability

The platform prioritizes explainable ESG operational workflows over infrastructure complexity, while maintaining a foundation that can evolve toward enterprise-scale sustainability reporting systems.

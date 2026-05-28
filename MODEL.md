# MODEL.md

# Breathe ESG — Data Model & System Architecture

## Overview

Breathe ESG is a multi-tenant emissions data ingestion and review platform designed to normalize heterogeneous operational sustainability data into a unified emissions review workflow.

The platform ingests enterprise sustainability data from:

* SAP Fuel & Procurement exports
* Utility electricity consumption exports
* Corporate travel exports

The system converts these operational datasets into normalized ESG emission records aligned to GHG Protocol Scope 1, Scope 2, and Scope 3 classifications.

---

# High-Level Architecture

```text
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
        ↓
Approved ESG Dataset
```

---

# Multi-Tenant Architecture

The platform was designed as a multi-tenant system because ESG reporting systems typically serve multiple business entities, subsidiaries, or customers.

Each tenant has isolated:

* uploads
* records
* review workflows
* plant mappings
* audit logs

Tenant separation is enforced at the application layer.

---

# Main Database Models

## 1. Tenant (Organization)

Represents a company or reporting entity.

### Key Fields

| Field      | Purpose                   |
| ---------- | ------------------------- |
| id         | UUID primary key          |
| name       | organization name         |
| slug       | unique tenant identifier  |
| created_at | tenant creation timestamp |

### Purpose

Provides logical isolation for ESG datasets.

---

## 2. TenantMembership

Associates users with tenants and defines roles.

### Key Fields

| Field  | Purpose           |
| ------ | ----------------- |
| user   | Django auth user  |
| tenant | associated tenant |
| role   | analyst/admin     |

### Purpose

Supports scoped access control.

---

## 3. IngestionBatch (RawUpload)

Represents a single uploaded file.

### Key Fields

| Field             | Purpose                  |
| ----------------- | ------------------------ |
| original_filename | uploaded filename        |
| source_type       | SAP / Utility / Travel   |
| status            | processing state         |
| parsed_rows       | successfully parsed rows |
| failed_rows       | invalid rows             |
| uploaded_by       | user                     |
| created_at        | upload timestamp         |

### Purpose

Provides operational traceability and ingestion observability.

---

## 4. EmissionRecord (Normalized Record)

Core normalized ESG entity.

### Key Fields

| Field           | Purpose                  |
| --------------- | ------------------------ |
| scope           | Scope 1/2/3              |
| category        | emissions category       |
| quantity        | normalized quantity      |
| quantity_unit   | canonical unit           |
| status          | review status            |
| source_metadata | original contextual data |
| flag_reasons    | validation anomalies     |
| row_hash        | deduplication hash       |

### Purpose

Represents a normalized ESG operational activity.

---

## 5. AuditTrail (Approval Log)

Tracks review actions.

### Key Fields

| Field     | Purpose             |
| --------- | ------------------- |
| record    | emission record     |
| actor     | reviewing analyst   |
| action    | approve/reject/edit |
| note      | reviewer comment    |
| timestamp | event time          |

### Purpose

Supports auditability and governance.

---

## 6. PlantCodeLookup

Maps operational plant codes to readable business locations.

### Purpose

SAP exports frequently contain opaque operational identifiers.

The lookup table normalizes:

```text
PLANT01 → Mumbai Plant
```

---

# Relationships

```text
Tenant
 ├── TenantMembership
 ├── IngestionBatch
 ├── EmissionRecord
 └── PlantCodeLookup

EmissionRecord
 └── AuditTrail
```

---

# Normalization Strategy

## Objective

Operational enterprise systems expose inconsistent schemas.

The platform standardizes them into a unified ESG schema.

---

# Column Normalization

Input headers are normalized using:

```python
c.strip().lower().replace('_', ' ')
```

This allows:

```text
billing_period_start
billing period start
Billing_Period_Start
```

to resolve consistently.

---

# Unit Normalization

The system converts heterogeneous operational units into canonical reporting units.

| Domain      | Canonical Unit |
| ----------- | -------------- |
| Fuel Volume | Liters         |
| Mass        | Kilograms      |
| Electricity | kWh            |
| Distance    | Kilometers     |

Examples:

```text
gallons → liters
miles → kilometers
MWh → kWh
```

---

# Scope Classification Strategy

## Scope 1

Direct emissions:

* diesel
* petrol
* LPG combustion

## Scope 2

Purchased electricity.

## Scope 3

Indirect operational emissions:

* business travel
* hotel stays
* procurement materials

---

# Validation Strategy

The ingestion pipeline performs deterministic validations.

Examples:

| Validation            | Reason               |
| --------------------- | -------------------- |
| zero quantity         | operational anomaly  |
| missing employee ID   | audit incompleteness |
| >1 GWh electricity    | probable unit issue  |
| invalid airport route | travel quality issue |

Flagged records require analyst review.

---

# Deduplication Strategy

Each normalized row generates a deterministic hash:

```python
SHA256(...)
```

based on operational attributes.

This supports future duplicate detection and replay protection.

---

# Audit Trail Strategy

All review actions are persisted.

The system records:

* actor
* action
* timestamp
* review note

This creates traceable ESG governance workflows.

---

# Data Retention Strategy

The platform stores:

* normalized records
* raw metadata
* upload batches
* review actions

This enables:

* traceability
* explainability
* ESG audit support

---

# Technology Rationale

| Layer          | Technology     |
| -------------- | -------------- |
| Backend        | Django + DRF   |
| Frontend       | React + Vite   |
| Database       | SQLite         |
| Parsing        | Pandas         |
| Authentication | DRF Token Auth |

---

# Why SQLite Instead of PostgreSQL

SQLite was selected because:

* minimal infrastructure overhead
* fast local setup
* no external dependency
* sufficient for prototype scale

Production systems should migrate to PostgreSQL for:

* concurrency
* transactional guarantees
* scalability
* analytics workloads

---

# Future Evolution

Potential next steps:

* background ingestion jobs
* PostgreSQL migration
* OCR utility bill ingestion
* real SAP APIs
* emission factor engine
* supplier APIs
* AI anomaly detection
* warehouse-scale ESG analytics

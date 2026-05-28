# SOURCES.md

# Data Source Research & Format Selection

## Overview

This document explains:

* which real-world enterprise ESG data formats were researched
* what operational exports typically look like
* why specific prototype formats were selected
* how realistic operational issues were simulated

The objective was not to create synthetic toy datasets, but to model realistic operational ESG ingestion workflows.

---

# 1. SAP Fuel & Procurement

## Researched Sources

The following operational SAP reporting patterns were researched:

### SAP MB51

Material document reporting export commonly used for:

* fuel movement tracking
* inventory transactions
* material consumption

### SAP ME2M

Procurement reporting export used for:

* purchasing data
* vendor procurement
* material acquisition

### Common SAP Operational Exports

Typical export formats:

* CSV
* XLSX
* flat-file operational extracts

---

# Real-World Characteristics

SAP operational exports commonly contain:

| Characteristic              | Example                         |
| --------------------------- | ------------------------------- |
| inconsistent headers        | material_group vs material type |
| opaque plant codes          | PLANT01                         |
| procurement classifications | DIESEL / LPG / CEMENT           |
| operational identifiers     | document numbers                |
| mixed units                 | liters / kg / tons              |

---

# Chosen Prototype Format

## Selected Format

CSV/XLSX operational export.

## Why

CSV exports realistically simulate:

* analyst workflows
* procurement operations
* ERP reporting exports

without requiring live SAP infrastructure.

---

# Sample Data Realism

The prototype intentionally includes:

| Simulated Issue              | Reason                   |
| ---------------------------- | ------------------------ |
| zero quantity rows           | operational anomalies    |
| mixed procurement categories | scope classification     |
| vendor variation             | procurement realism      |
| plant mappings               | enterprise normalization |

---

# Example Operational Row

```csv id="b5q1z7"
2024-03-15,PLANT01,DIESEL,Indian Oil,5000,L
```

---

# ESG Mapping Logic

| Material | ESG Scope |
| -------- | --------- |
| DIESEL   | Scope 1   |
| PETROL   | Scope 1   |
| STEEL    | Scope 3   |
| CEMENT   | Scope 3   |

---

# Limitations

The prototype does not include:

* live SAP APIs
* IDoc integration
* BAPI integration
* procurement hierarchy resolution
* supplier master synchronization

---

# 2. Utility Electricity Data

## Researched Sources

### Utility Portal CSV Exports

Many enterprise utility providers support:

* CSV usage exports
* XLSX billing summaries
* operational meter downloads

### Green Button Connect

Standardized utility energy data sharing initiative.

### Urjanet

Enterprise utility aggregation platform.

---

# Real-World Characteristics

Utility exports frequently contain:

| Characteristic               | Example                      |
| ---------------------------- | ---------------------------- |
| inconsistent billing periods | start/end date variations    |
| meter identifiers            | MTR001                       |
| mixed consumption naming     | kWh / usage / units consumed |
| provider-specific schemas    | Tata Power vs BSES           |

---

# Chosen Prototype Format

## Selected Format

CSV operational export.

## Why

Utility CSVs best demonstrate:

* operational normalization
* energy standardization
* anomaly detection

without OCR complexity.

---

# Simulated Realistic Problems

The prototype intentionally includes:

| Simulated Problem            | Reason                  |
| ---------------------------- | ----------------------- |
| >1 GWh consumption           | unit anomaly            |
| inconsistent facility naming | normalization realism   |
| varying providers            | multi-source ingestion  |
| billing period mapping       | operational variability |

---

# Example Operational Row

```csv id="s7x4v1"
2024-01-01,2024-01-31,MTR001,Mumbai Plant,24100
```

---

# ESG Mapping Logic

| Activity              | ESG Scope |
| --------------------- | --------- |
| Purchased Electricity | Scope 2   |

---

# Limitations

The prototype does not include:

* PDF OCR parsing
* utility APIs
* smart meter streaming
* interval energy telemetry

---

# 3. Corporate Travel Data

## Researched Sources

### SAP Concur

Enterprise travel & expense platform.

### Navan

Corporate travel management platform.

### Common Travel Exports

Typical exports include:

* CSV expense exports
* travel booking summaries
* expense reconciliation reports

---

# Real-World Characteristics

Travel operational data commonly contains:

| Characteristic           | Example             |
| ------------------------ | ------------------- |
| airport IATA codes       | BLR / DEL           |
| travel class             | economy / business  |
| incomplete traveler info | missing employee ID |
| hotel stays              | nights              |
| multiple transport modes | air / rail / taxi   |

---

# Chosen Prototype Format

## Selected Format

CSV operational travel export.

## Why

Travel CSVs allow demonstration of:

* geospatial normalization
* travel classification
* distance estimation
* operational traceability

---

# Simulated Realistic Problems

The prototype intentionally includes:

| Simulated Issue       | Reason                   |
| --------------------- | ------------------------ |
| missing employee ID   | governance validation    |
| international routes  | long-haul calculations   |
| mixed transport types | category normalization   |
| hotel stays           | alternate quantity logic |

---

# Example Operational Row

```csv id="n4w8r2"
2024-01-10,EMP-00234,AIR,BLR,DEL,economy
```

---

# ESG Mapping Logic

| Travel Type      | ESG Scope |
| ---------------- | --------- |
| Air Travel       | Scope 3   |
| Hotel Stay       | Scope 3   |
| Ground Transport | Scope 3   |

---

# Distance Calculation Strategy

The platform estimates travel distance using:

* airport coordinate lookup
* great-circle distance calculation

This approximates operational emissions activity.

---

# Limitations

The prototype does not include:

* live travel APIs
* booking synchronization
* itinerary parsing
* mileage reimbursement systems

---

# Conclusion

The selected source formats intentionally reflect realistic enterprise operational workflows while remaining implementable within prototype constraints.

The project prioritizes:

* ingestion architecture
* normalization logic
* operational governance
* ESG workflow realism

over direct enterprise integrations.

# DECISIONS.md

# Architectural & Product Decisions

## Overview

This document explains key architectural decisions, ambiguities, and tradeoffs made during implementation.

The system was intentionally designed as an operational ESG ingestion workflow rather than a simple CSV viewer.

---

# Why CSV Instead of SAP APIs?

## Decision

Use CSV/XLSX exports instead of direct SAP integration.

## Reasoning

Real SAP integrations typically require:

* SAP Gateway access
* IDoc configuration
* BAPI contracts
* VPN/network connectivity
* enterprise credentials

Those integrations are operationally heavy for a prototype assignment.

CSV exports simulate realistic operational workflows because many ESG teams still rely on exported operational reports.

Examples researched:

* SAP MB51
* SAP ME2M
* procurement operational reports

---

# Why Utility CSV Instead of PDF Parsing?

## Decision

Use utility CSV exports instead of OCR-based PDF ingestion.

## Reasoning

PDF parsing introduces:

* OCR complexity
* layout variability
* extraction instability
* vendor-specific formats

The goal of the assignment was operational normalization architecture rather than OCR engineering.

CSV ingestion better demonstrates:

* normalization logic
* schema mapping
* review workflows

---

# Why Analyst Approval Workflow?

## Decision

Introduce review states:

* pending
* flagged
* approved
* rejected

## Reasoning

Operational ESG data often contains:

* missing values
* unit inconsistencies
* duplicate submissions
* incorrect operational mappings

Blind auto-approval creates governance risks.

Analyst review workflows improve:

* auditability
* traceability
* operational trust

---

# Why Multi-Tenant Design?

## Decision

Support isolated tenants.

## Reasoning

Enterprise ESG systems commonly serve:

* subsidiaries
* business units
* multiple customers
* reporting entities

Tenant isolation was included early because it affects:

* schema design
* access control
* ingestion boundaries
* review permissions

---

# Why Django + DRF?

## Decision

Use Django REST Framework.

## Reasoning

DRF provides:

* rapid API development
* authentication primitives
* admin tooling
* ORM support
* serialization support

This allowed focus on ingestion and normalization logic.

---

# Why React + Vite?

## Decision

Use React frontend with Vite.

## Reasoning

Vite provides:

* fast iteration
* lightweight configuration
* modern React tooling

The frontend primarily supports operational workflows rather than public marketing pages.

---

# Why SQLite?

## Decision

Use SQLite for persistence.

## Reasoning

The assignment prioritized:

* rapid iteration
* portability
* easy setup

SQLite reduced infrastructure complexity.

Production systems would migrate to PostgreSQL.

---

# Why Scope-Based Classification?

## Decision

Normalize records into Scope 1/2/3.

## Reasoning

GHG Protocol alignment is central to ESG reporting.

The ingestion engine translates operational activity into emissions categories aligned to reporting standards.

---

# Product Ambiguities Considered

## Should Approved Records Be Editable?

### Decision

Edits are currently allowed through review workflows.

### Reasoning

Operational ESG corrections frequently occur after review.

However, production systems should likely:

* freeze approved records
* require versioned corrections
* create immutable audit revisions

---

# How Should Emission Factors Be Versioned?

### Current Decision

Emission factors are placeholder logic only.

### Future Design

Production systems should:

* version factors annually
* support geography-specific factors
* track source methodology
* preserve historical calculations

---

# What SLA Should Exist For Ingestion Failures?

### Current State

Failures are surfaced synchronously during upload.

### Production Expectation

Enterprise ingestion systems would likely require:

| Severity                   | SLA                    |
| -------------------------- | ---------------------- |
| Critical ingestion failure | immediate alert        |
| partial parse failure      | analyst review         |
| delayed batch              | operational escalation |

---

# Why Synchronous Processing?

## Decision

Uploads process inline.

## Reasoning

Simplifies prototype architecture.

Production systems would likely use:

* Celery
* Kafka
* background workers
* retry queues

---

# Why Deterministic Validation Instead of AI?

## Decision

Use rule-based validations.

## Reasoning

ESG governance systems require explainability.

Deterministic validations are easier to audit than opaque anomaly models.

---

# Why Store Raw Metadata?

## Decision

Preserve source metadata alongside normalized records.

## Reasoning

This supports:

* traceability
* explainability
* audit workflows
* operational debugging

Without source metadata, normalized ESG records lose operational lineage.

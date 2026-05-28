# TRADEOFFS.md

# Deliberate Tradeoffs & Deferred Features

## Overview

This prototype intentionally prioritizes:

* ingestion architecture
* normalization workflows
* ESG review operations

over enterprise-scale infrastructure.

Several production-grade capabilities were intentionally deferred.

---

# No Real SAP Integration

## Skipped

Direct SAP APIs:

* IDoc
* BAPI
* OData
* RFC integrations

## Why

Requires enterprise SAP environments and connectivity.

CSV exports were sufficient to model operational ingestion workflows.

## Future Improvement

Add:

* SAP Gateway integration
* scheduled procurement pulls
* ERP synchronization

---

# No OCR Utility PDF Parsing

## Skipped

OCR-based PDF extraction.

## Why

Utility PDFs vary significantly by provider.

OCR engineering would dominate project scope.

## Future Improvement

Add:

* OCR pipeline
* layout detection
* invoice extraction
* provider templates

---

# No Real Emission Factor Engine

## Skipped

Formal emissions calculations.

## Why

The project focused on ingestion and normalization architecture.

Production emissions engines require:

* regulatory methodologies
* geography mappings
* versioning
* annual factor updates

## Future Improvement

Integrate:

* DEFRA factors
* EPA factors
* location-based electricity factors

---

# No Background Jobs

## Skipped

Asynchronous ingestion processing.

## Why

Synchronous processing simplified development and debugging.

## Future Improvement

Use:

* Celery
* Redis
* Kafka
* queue-based pipelines

---

# No Async Processing

## Skipped

Distributed ingestion execution.

## Why

Prototype scale did not require distributed compute.

---

# No Live APIs

## Skipped

Live utility and travel APIs.

## Why

Operational exports were sufficient for demonstrating ingestion workflows.

## Future Improvement

Integrate:

* SAP Concur APIs
* Green Button APIs
* supplier APIs

---

# No Single Sign-On (SSO)

## Skipped

Enterprise identity federation.

## Why

Out of scope for prototype implementation.

## Future Improvement

Add:

* OAuth2
* SAML
* Azure AD
* Okta

---

# No Role Hierarchy

## Skipped

Granular RBAC.

## Why

Simple analyst/admin roles were sufficient.

## Future Improvement

Support:

* approvers
* auditors
* tenant admins
* global admins

---

# No AI Anomaly Detection

## Skipped

Machine learning anomaly models.

## Why

Deterministic validations are more explainable for ESG governance.

## Future Improvement

Add anomaly scoring for:

* unusual energy spikes
* duplicate travel
* abnormal procurement

---

# No Bulk Retry Pipeline

## Skipped

Replay/retry orchestration.

## Why

Prototype batches are processed directly.

## Future Improvement

Add:

* dead-letter queues
* replay workflows
* ingestion recovery tooling

---

# No PostgreSQL

## Skipped

Enterprise-grade relational database.

## Why

SQLite accelerated local development.

## Future Improvement

Migrate to PostgreSQL for:

* concurrency
* scaling
* analytics
* transactional safety

---

# No Object Storage

## Skipped

Cloud file storage.

## Why

Local media storage simplified deployment.

## Future Improvement

Add:

* S3
* GCS
* Azure Blob Storage

---

# No Multi-Region Support

## Skipped

Geo-distributed infrastructure.

## Why

Prototype scale did not require regional deployment.

---

# No Streaming Ingestion

## Skipped

Real-time event ingestion.

## Why

Batch-oriented ESG reporting was prioritized.

## Future Improvement

Support:

* Kafka
* streaming meters
* IoT telemetry

---

# Conclusion

The project intentionally prioritizes:

* correctness
* explainability
* operational workflows
* ESG normalization logic

over infrastructure complexity.

The architecture was designed to evolve incrementally toward enterprise-scale capabilities.

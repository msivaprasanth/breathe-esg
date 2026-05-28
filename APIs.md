# APIs.md

# Breathe ESG — REST API Documentation

## Overview

The platform exposes REST APIs for:

* authentication
* ingestion
* review workflows
* dashboard metrics
* record management

The backend is implemented using Django REST Framework.

Base URL:

```text id="k2x7p9"
http://localhost:8000/api/
```

Production:

```text id="h5m1q8"
https://your-render-backend.onrender.com/api/
```

---

# Authentication

The system uses token authentication.

## Login

### Endpoint

```http id="j8r4w2"
POST /api/auth/login/
```

### Request

```json id="a6v1n5"
{
  "username": "analyst1",
  "password": "analyst123"
}
```

### Response

```json id="d3q7m4"
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "username": "analyst1"
  },
  "tenant": {
    "id": "uuid",
    "name": "Acme Corporation",
    "role": "analyst"
  }
}
```

---

# Current User

### Endpoint

```http id="r9w6k1"
GET /api/auth/me/
```

### Headers

```text id="m2p8x7"
Authorization: Token <token>
```

---

# Upload APIs

## Upload ESG Dataset

### Endpoint

```http id="t4v1n8"
POST /api/upload/
```

### Content-Type

```text id="g7q3r5"
multipart/form-data
```

### Form Fields

| Field       | Type   |
| ----------- | ------ |
| file        | file   |
| source_type | string |

---

# Supported Source Types

| Source Type | Description        |
| ----------- | ------------------ |
| SAP         | Fuel & procurement |
| UTILITY     | electricity usage  |
| TRAVEL      | corporate travel   |

---

# Response

```json id="u6x2m9"
{
  "batch_id": "uuid",
  "parsed_rows": 8,
  "flagged_rows": 1,
  "failed_rows": 0
}
```

---

# Review APIs

## Review Queue

### Endpoint

```http id="f8w4p2"
GET /api/review/
```

### Query Parameters

| Parameter   | Purpose             |
| ----------- | ------------------- |
| status      | filter by status    |
| scope       | filter by ESG scope |
| source_type | filter by source    |

---

# Example

```http id="c7v5q1"
GET /api/review/?status=FLAGGED
```

---

# Response

```json id="z3k8m6"
[
  {
    "id": "uuid",
    "scope": "3",
    "category": "BUSINESS_TRAVEL_AIR",
    "quantity": 1736.3,
    "quantity_unit": "km",
    "status": "FLAGGED"
  }
]
```

---

# Record Detail

### Endpoint

```http id="x5m7n1"
GET /api/review/<record_id>/
```

---

# Edit Record

### Endpoint

```http id="q4v8w3"
PATCH /api/review/<record_id>/edit/
```

### Request Example

```json id="b1x9r4"
{
  "quantity": 1800
}
```

---

# Approval APIs

## Approve Records

### Endpoint

```http id="w6p3m8"
POST /api/approve/
```

### Request

```json id="n8r5q2"
{
  "record_ids": [
    "uuid1",
    "uuid2"
  ],
  "note": "Reviewed and approved."
}
```

---

# Reject Records

### Endpoint

```http id="k9m2v7"
POST /api/reject/
```

### Request

```json id="f4x1q6"
{
  "record_ids": [
    "uuid1"
  ],
  "note": "Missing supporting information."
}
```

---

# Dashboard APIs

## Dashboard Metrics

### Endpoint

```http id="r7n3p1"
GET /api/dashboard/
```

### Response

```json id="v2q8m5"
{
  "total_records": 45,
  "scope1": 10,
  "scope2": 15,
  "scope3": 20,
  "flagged": 5
}
```

---

# Batch APIs

## List Upload Batches

### Endpoint

```http id="u5r1m9"
GET /api/batches/
```

---

# Response

```json id="p3v8q6"
[
  {
    "id": "uuid",
    "original_filename": "travel_test.csv",
    "status": "DONE",
    "parsed_rows": 8
  }
]
```

---

# Error Handling

## Validation Error

```json id="s4w7n2"
{
  "error": "Could not find category column."
}
```

---

# Authentication Error

```json id="t6x3m1"
{
  "error": "Invalid credentials."
}
```

---

# Security Notes

Current authentication:

* token-based authentication
* tenant-scoped access
* session fallback for admin

Future improvements:

* OAuth2
* SSO
* RBAC hierarchy
* API rate limiting

---

# API Design Philosophy

The APIs prioritize:

* operational simplicity
* deterministic behavior
* explainable workflows
* ESG governance traceability

over hyper-optimized distributed architectures.

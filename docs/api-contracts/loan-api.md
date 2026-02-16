# Loan API Contract
**Frontend ↔ Backend Agreement**

---

## Base URL
```
Production: https://api.bancafiel.com/v1
Development: http://localhost:3001/v1
```

---

## Authentication

All requests require JWT token in header:
```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Get Pending Applications

**GET** `/api/loans?status=pending`

**Response:**
```json
{
  "applications": [
    {
      "id": "uuid",
      "applicantName": "Juan Pérez",
      "applicantEmail": "juan@email.com",
      "loanAmount": 50000,
      "monthlyIncome": 15000,
      "requestedDate": "2026-02-15T10:00:00Z",
      "status": "pending",
      "fraudScore": 0.23,
      "creditScore": 720,
      "documents": [
        {
          "type": "INE",
          "url": "s3://bucket/path/ine.pdf"
        },
        {
          "type": "income_proof",
          "url": "s3://bucket/path/income.pdf"
        }
      ]
    }
  ],
  "total": 15
}
```

---

### 2. Get Application by ID

**GET** `/api/loans/:id`

**Response:**
```json
{
  "id": "uuid",
  "applicantName": "Juan Pérez",
  "applicantEmail": "juan@email.com",
  "curp": "PEJJ850101HDFRNN09",
  "phone": "+52 55 1234 5678",
  "address": "Calle Principal 123, CDMX",
  "loanAmount": 50000,
  "monthlyIncome": 15000,
  "existingDebt": 20000,
  "requestedDate": "2026-02-15T10:00:00Z",
  "status": "pending",
  "fraudScore": 0.23,
  "fraudRiskLevel": "low",
  "creditScore": 720,
  "creditRecommendation": "approve",
  "documents": [...],
  "extractedData": {
    "fullName": "Juan Pérez",
    "curp": "PEJJ850101HDFRNN09",
    "monthlyIncome": 15000
  },
  "history": [
    {
      "timestamp": "2026-02-15T10:00:00Z",
      "action": "submitted",
      "user": "system"
    },
    {
      "timestamp": "2026-02-15T10:05:00Z",
      "action": "processed",
      "user": "system"
    }
  ]
}
```

---

### 3. Approve Application

**POST** `/api/loans/:id/approve`

**Request Body:**
```json
{
  "notes": "Income verified. Good credit history.",
  "approvedBy": "analyst@bancafiel.com"
}
```

**Response:**
```json
{
  "success": true,
  "loanId": "uuid",
  "status": "approved",
  "message": "Application approved successfully",
  "timestamp": "2026-02-15T11:00:00Z"
}
```

---

### 4. Reject Application

**POST** `/api/loans/:id/reject`

**Request Body:**
```json
{
  "reason": "Insufficient income for requested amount",
  "rejectedBy": "analyst@bancafiel.com"
}
```

**Response:**
```json
{
  "success": true,
  "loanId": "uuid",
  "status": "rejected",
  "message": "Application rejected",
  "timestamp": "2026-02-15T11:00:00Z"
}
```

---

### 5. Get Analytics

**GET** `/api/analytics?startDate=2026-02-01&endDate=2026-02-15`

**Response:**
```json
{
  "totalApplications": 150,
  "approved": 120,
  "rejected": 25,
  "pending": 5,
  "approvalRate": 0.80,
  "averageProcessingTime": 45,
  "fraudAlerts": 10,
  "volumeByDay": [
    {
      "date": "2026-02-01",
      "applications": 12
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Bad Request",
  "message": "Invalid loan amount",
  "statusCode": 400
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token",
  "statusCode": 401
}
```

### 404 Not Found
```json
{
  "error": "Not Found",
  "message": "Application not found",
  "statusCode": 404
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "statusCode": 500
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

---

**Last Updated:** February 15, 2026
**Maintained By:** Backend & Frontend Developers

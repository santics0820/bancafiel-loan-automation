# review-security

Pre-deploy security checklist for BancaFiel. Run before every `sam deploy`.

---

## Checklist

### 1. Secrets Exposure
- [ ] No hardcoded passwords, API keys, or tokens anywhere in `src/`
- [ ] `DB_PASSWORD` is read from `os.environ.get('DB_PASSWORD')` only — never a literal string
- [ ] `samconfig.toml` is listed in `.gitignore` (it contains `DBPassword=BancaFiel2024Secure!`)
- [ ] No credentials in CloudWatch logs (check `logger.info` calls don't log `event` bodies with sensitive data)

### 2. SQL Injection
- [ ] All DB queries use parameterized form: `execute_query("... WHERE id = %s", (value,))`
- [ ] No string concatenation in SQL: no `f"SELECT ... WHERE id = {user_input}"`
- [ ] `_convert_placeholders()` is used — never pass raw user input directly to `conn.run()`

### 3. Input Validation
- [ ] All POST/PUT routes validate required fields before processing
- [ ] `application_type` is checked against an allowlist (e.g., `["personal", "business", "mortgage"]`)
- [ ] `loan_amount` is validated as a positive number (`> 0`)
- [ ] CURP format is validated before use in DB queries (18-char alphanumeric)

### 4. IAM Least Privilege
- [ ] No `s3:*` wildcard actions — only specific actions (`s3:GetObject`, `s3:PutObject`)
- [ ] No `Resource: '*'` on S3 policies — use `!Sub "arn:aws:s3:::bancafiel-incoming-${AWS::AccountId}-${Environment}/*"`
- [ ] Lambda cross-invocation policies use specific function ARNs, not wildcards
- [ ] Only `textract:*` and `frauddetector:*` use `Resource: '*'` (AWS-required for those services)

### 5. Error Handling
- [ ] No raw exception messages returned in API responses
- [ ] 500 responses return only `{"error": "Internal server error"}` — no tracebacks
- [ ] All handlers have top-level `try/except Exception as e: logger.error(...)` blocks
- [ ] Lambda timeouts are reasonable (30s default, 60s for Textract/Fraud lambdas)

### 6. API Security
- [ ] CORS `AllowOrigin: '*'` is acceptable for dev — confirm this is NOT prod
- [ ] No sensitive fields (passwords, CURP, full account numbers) returned in list endpoints
- [ ] `Authorization` header is present in CORS AllowHeaders (ready for Cognito in Week 3)

---

## How to run this review

1. Read through each Lambda handler in `backend/src/lambdas/`
2. Check each item above — mark PASS / FAIL
3. For a deep automated review, use the `security-reviewer` agent instead

## Deployment gate

**Do not run `sam deploy` if any item in sections 1, 2, or 4 is FAIL.**
Sections 3, 5, 6 failures should be fixed before deploy but use judgment for dev iterations.

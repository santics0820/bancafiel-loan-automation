# db-connect

Connect to BancaFiel RDS PostgreSQL and manage schema.

## Step 1 — Get DB endpoint from CloudFormation

```bash
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

aws cloudformation describe-stacks \
  --stack-name bancafiel-backend-dev \
  --region us-east-1 \
  --query "Stacks[0].Outputs[?OutputKey=='DatabaseEndpoint'].OutputValue" \
  --output text
```

Save the returned hostname (e.g., `bancafiel-postgres-dev.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com`).

## Step 2 — Connect via psql

```bash
psql -h <DB_ENDPOINT> -U bancafiel_admin -d bancafiel -p 5432
# Password: BancaFiel2024Secure!
```

## Step 3 — Apply schema (first deploy only)

```bash
psql -h <DB_ENDPOINT> -U bancafiel_admin -d bancafiel -p 5432 \
  -f /Users/santiagocairesanchez/KPMG/backend/src/database/schema.sql
```

## Step 4 — Quick Python query (pg8000)

```python
import pg8000.native as pg
conn = pg.Connection(
    user="bancafiel_admin",
    password="BancaFiel2024Secure!",
    host="<DB_ENDPOINT>",
    port=5432,
    database="bancafiel",
    ssl_context=True          # required for RDS
)
rows = conn.run("SELECT COUNT(*) FROM applications")
print(rows)
conn.close()
```

## Security Notes
- DB is `PubliclyAccessible: true` — **dev environment only**
- Password is in `samconfig.toml` — never commit samconfig.toml to a public repository
- In prod, migrate password to AWS Secrets Manager
- Security group allows `0.0.0.0/0` on port 5432 — tighten to specific CIDRs before prod

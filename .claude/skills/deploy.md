# deploy

Deploy BancaFiel backend to AWS using SAM.

## Steps

### Step 1 — Fix PATH (always required first)
```bash
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/santiagocairesanchez/Library/Python/3.13/bin:$PATH"
```

### Step 2 — Enter backend directory
```bash
cd /Users/santiagocairesanchez/KPMG/backend
```

### Step 3 — Validate template
```bash
sam validate
```
Must show `template.yaml is valid` before continuing.

### Step 4 — Build
```bash
sam build
```
Builds all Lambda functions and the CommonLayer.

### Step 5 — Deploy
```bash
sam deploy --config-file samconfig.toml
```
Uses `bancafiel-backend-dev` stack, region `us-east-1`, account `466901690437`.

### Step 6 — Extract outputs after deploy
```bash
aws cloudformation describe-stacks \
  --stack-name bancafiel-backend-dev \
  --region us-east-1 \
  --query "Stacks[0].Outputs" \
  --output table
```
Record `APIGatewayURL` and `DatabaseEndpoint` from the outputs. Save to MEMORY.md.

---

## Common Failures

| Symptom | Cause | Fix |
|---|---|---|
| `sam: command not found` | PATH not set | Run Step 1 first |
| `UPDATE_ROLLBACK_COMPLETE` | CloudFormation error | Run `aws cloudformation describe-stack-events --stack-name bancafiel-backend-dev --region us-east-1` and look for `FAILED` events |
| Circular dependency error | `!Ref`/`!GetAtt` in IAM Resource | Use `!Sub` ARN pattern: `!Sub "arn:aws:s3:::bancafiel-incoming-${AWS::AccountId}-${Environment}/*"` |
| `S3 bucket already exists` | Bucket name collision | Check account ID in bucket name matches 466901690437 |
| `CAPABILITY_NAMED_IAM` error | Missing capability flag | Already in samconfig.toml — verify it's set |
| `NoSuchBucket` on deploy | SAM deploy bucket missing | Create: `aws s3 mb s3://bancafiel-sam-deploy-466901690437 --region us-east-1` |

---

## Notes
- `samconfig.toml` contains `DBPassword=BancaFiel2024Secure!` — never commit to public repo
- For prod deploy: `sam deploy --config-env prod` (requires `confirm_changeset = true`)
- Run `/review-security` before every deploy

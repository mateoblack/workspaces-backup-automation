# WorkSpaces Backup Automation

Automated backup and restore solution for AWS WorkSpaces using native image creation.

## Problem

Manual WorkSpaces snapshots to S3 are time-consuming and slow to restore. This solution automates the backup process using AWS WorkSpaces native image functionality for faster, more reliable backups and restores.

## Solution

Fully automated WorkSpaces image creation with EventBridge scheduling, Lambda automation, and SSM self-service restore capabilities.

## Architecture

```
EventBridge (Daily 2 AM UTC)
    ↓
Lambda Function
    ↓
WorkSpaces API (Create Images)
    ↓
Automatic Cleanup (30+ days)
    
SSM Document → Self-Service Restore
```

**Key Features:**
- EventBridge triggers Lambda daily at 2 AM UTC
- Lambda discovers WorkSpaces tagged with `AutoBackup=enabled`
- Creates native WorkSpace images (stored in AWS WorkSpaces service)
- Automatically deletes images older than 30 days (configurable)
- SSM runbook provides user-friendly restore interface

## Components

### 1. Lambda Function (`lambda/index.py`)
- Discovers tagged WorkSpaces
- Creates WorkSpace images
- Manages image lifecycle and cleanup
- Runs on scheduled basis

### 2. EventBridge Rule
- Triggers Lambda on cron schedule
- Default: `cron(0 2 * * ? *)` (2 AM UTC daily)

### 3. SSM Document (`ssm/restore_runbook.yaml`)
- Self-service restore interface
- Rebuilds WorkSpace from selected image
- Accessible via AWS Console or CLI

### 4. Terraform Infrastructure (`main.tf`)
- Complete infrastructure as code
- IAM roles and policies
- All AWS resources configured

## Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Usage

### Enable Backup for a WorkSpace

Tag your WorkSpace to enable automatic backups:

```bash
aws workspaces create-tags \
  --resource-id ws-abc123 \
  --tags Key=AutoBackup,Value=enabled
```

### Restore from Image

**Via AWS Console:**
1. Navigate to Systems Manager → Documents
2. Search for "RestoreWorkspaceFromImage"
3. Execute the document
4. Select the image and WorkSpace to restore

**Via AWS CLI:**
```bash
aws ssm start-automation-execution \
  --document-name "RestoreWorkspaceFromImage" \
  --parameters "ImageId=wsi-xyz789,WorkspaceId=ws-abc123"
```

## Configuration

Customize these variables in `terraform/variables.tf`:

| Variable | Description | Default |
|----------|-------------|---------|
| `backup_schedule` | Cron expression for backup timing | `cron(0 2 * * ? *)` |
| `retention_days` | Days to retain images | `30` |
| `backup_tag_key` | Tag key to identify WorkSpaces | `AutoBackup` |
| `backup_tag_value` | Required tag value | `enabled` |

## Requirements

- **Terraform:** >= 1.0
- **AWS CLI:** Configured with appropriate credentials
- **AWS Permissions:** 
  - `workspaces:*`
  - `lambda:*`
  - `events:*`
  - `ssm:*`
  - `iam:CreateRole`, `iam:AttachRolePolicy`

## Cost Considerations

- Lambda execution costs (minimal, runs once daily)
- WorkSpaces image storage (charged per image)
- No additional S3 storage costs (uses native WorkSpaces images)

## Monitoring

Check Lambda CloudWatch Logs for:
- Backup success/failure
- Images created
- Images deleted

## License

MIT

## Contributing

Pull requests welcome. Please ensure Terraform formatting with `terraform fmt` before submitting.

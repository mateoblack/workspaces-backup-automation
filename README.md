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
    ↓
Creates Bundle → Terminates Old → Creates New WorkSpace
```

**Key Features:**
- EventBridge triggers Lambda daily at 2 AM UTC
- Lambda discovers WorkSpaces tagged with `AutoBackup=enabled`
- Creates native WorkSpace images (stored in AWS WorkSpaces service)
- Automatically deletes images older than 30 days (configurable)
- SSM runbook provides restore interface (creates temporary bundle, terminates old WorkSpace, creates new one)

**Important Notes:**
- Images are tied to the AWS Directory Service directory and user account
- Restoring requires the original directory and user to still exist
- Restore process is destructive (terminates the original WorkSpace)
- New WorkSpace gets a different ID but same user credentials

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

**⚠️ CRITICAL LIMITATIONS:**
- **Destructive Operation**: The original WorkSpace is permanently deleted
- **Directory Dependency**: Restore only works if the original AWS Directory Service directory still exists
- **User Dependency**: The user account must still exist in the directory
- **New WorkSpace ID**: You get a new WorkSpace ID (old ID becomes invalid)
- **Timing**: Restore automation completes in ~3 minutes, but WorkSpace provisioning takes 20-60 minutes
- **No Cross-Directory Restore**: Cannot restore to a different directory or different user

**What Gets Restored:**
- OS, applications, and system settings from the backup image
- User profile and data:
  - All user files (Desktop, Documents, Downloads, etc.)
  - Application data and settings
  - Browser bookmarks and saved passwords
  - Installed user applications
  - Complete C: drive (Windows) or root volume (Linux)
  - User volume (D: drive on Windows)

**What Doesn't Get Restored:**
- Original WorkSpace ID (you get a new one)
- WorkSpace properties (running mode, auto-stop timeout, etc.)
- Data stored outside the WorkSpace (network drives, cloud storage)

**Via AWS Console:**
1. Navigate to Systems Manager → Documents
2. Search for "RestoreWorkspaceFromImage"
3. Execute the document
4. Select the image and WorkSpace to restore
5. **WARNING**: This will terminate the selected WorkSpace

**Via AWS CLI:**
```bash
aws ssm start-automation-execution \
  --document-name "RestoreWorkspaceFromImage" \
  --parameters "ImageId=wsi-xyz789,WorkspaceId=ws-abc123"
```

Check restore status:
```bash
aws ssm describe-automation-executions \
  --filters "Key=ExecutionId,Values=<execution-id>" \
  --query 'AutomationExecutionMetadataList[0].AutomationExecutionStatus'
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

## ⚠️ Critical Warnings

### Directory Deletion
**DO NOT delete the AWS Directory Service directory if you have WorkSpace backups.**

If you delete the directory:
- All backup images become unusable with automated restore
- Images remain but cannot be deployed via the SSM runbook
- Images continue to cost money

**Planning to migrate or delete your directory?**
(e.g., switching from Simple AD to Microsoft Entra ID)

1. **Contact AWS Support BEFORE deleting** the directory
2. They can help migrate WorkSpace images to the new directory setup
3. Do not rely on automated restore after directory changes

**If directory already deleted:**
- Automated restore will not work
- Contact AWS Support for assistance recovering data from orphaned images
- Manual recovery is complex and may result in authentication/domain join issues

### User Account Deletion
Deleting a user from the directory makes their WorkSpace backups unrestorable to that username. The images remain but cannot be deployed.

## License

MIT

## Contributing

Pull requests welcome. Please ensure Terraform formatting with `terraform fmt` before submitting.

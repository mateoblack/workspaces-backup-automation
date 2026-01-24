# WorkSpaces Backup Automation

Automated backup and restore solution for **Amazon WorkSpaces** using **native WorkSpaces images** as point-in-time backups.

This project provides a **fully automated, self-service backup system** without S3 snapshots or manual intervention.

---

## Problem

Traditional WorkSpaces backup approaches (manual file copies, S3 syncs, ad-hoc snapshots) are:

* Slow to restore
* Operationally fragile
* Incomplete (often miss apps, config, or user state)

There is no first-class “snapshot” button for WorkSpaces.

---

## Solution

This solution uses **Amazon WorkSpaces native image creation** as a **point-in-time backup mechanism**, fully automated with:

* **EventBridge** for scheduling
* **Lambda** for discovery, image creation, and lifecycle management
* **SSM Automation** for self-service restore

The result is fast, consistent, whole-desktop backups that can be restored without admin intervention.

---

## Architecture

```
EventBridge (Daily 2 AM UTC)
    ↓
Lambda Function
    ↓
WorkSpaces API (CreateWorkspaceImage)
    ↓
Image Lifecycle Cleanup (Retention-based)

SSM Automation Document (Self-Service Restore)
    ↓
Create Temporary Bundle
    ↓
Terminate Old WorkSpace
    ↓
Create New WorkSpace from Image
```

---

## Key Features

* Scheduled, fully automated backups
* Uses **native WorkSpaces images** (no S3 snapshots)
* Tag-based opt-in (`AutoBackup=enabled`)
* Configurable retention policy (default: 30 days)
* Self-service restore via AWS Systems Manager
* No agents, no user interaction required

---

## Important Notes

* Images are **tied to the AWS Directory Service directory and user**
* Restores **require the original directory and user to still exist**
* Restore is **destructive** (old WorkSpace is terminated)
* Restored WorkSpace receives a **new WorkSpace ID**
* Credentials and user login remain the same

---

## Components

### 1. Lambda Function (`lambda/index.py`)

* Discovers tagged WorkSpaces
* Creates WorkSpaces images
* Applies naming, tagging, and retention logic
* Deletes expired images

### 2. EventBridge Rule

* Triggers the Lambda function on a cron schedule
* Default: `cron(0 2 * * ? *)` (2 AM UTC daily)

### 3. SSM Automation Document (`ssm/restore_runbook.yaml`)

* Self-service restore interface
* Creates a bundle from an image
* Terminates and recreates the WorkSpace

### 4. Terraform Infrastructure (`main.tf`)

* Infrastructure as code
* IAM roles and least-privilege policies
* Fully reproducible deployment

---

## Deployment

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## Usage

### Enable Backup for a WorkSpace

Tag a WorkSpace to opt it into automatic backups:

```bash
aws workspaces create-tags \
  --resource-id ws-abc123 \
  --tags Key=AutoBackup,Value=enabled
```

---

### WorkSpace State Requirements

WorkSpaces **must be in AVAILABLE (running) state** during the backup window.

#### AUTO_STOP WorkSpaces

* Skipped if stopped at backup time
* Recommended options:

  * Use `ALWAYS_ON` for WorkSpaces requiring daily backups
  * Use Step Functions or SSM to:

    * Start WorkSpaces before backup
    * Stop them afterward

> **Note:** Image creation can take 10–45 minutes and temporarily locks the WorkSpace.

---

## Restore from Image

### ⚠️ Critical Limitations

* **Destructive Operation** – original WorkSpace is permanently deleted
* **Directory Dependency** – directory must still exist
* **User Dependency** – user must still exist
* **New WorkSpace ID** – old ID becomes invalid
* **Provisioning Time** – 20–60 minutes after automation completes
* **No Cross-Directory Restore** – same directory and user only

---

### What Gets Restored

* OS, applications, and system configuration
* Full user profile and data:

  * Desktop, Documents, Downloads
  * Application data and settings
  * Browser profiles
  * Installed user applications
  * Entire system volume
  * User volume (D: on Windows)

---

### What Does *Not* Get Restored

* Original WorkSpace ID
* WorkSpace running mode and auto-stop settings
* External data (network drives, cloud storage)

---

### Restore via AWS Console

1. Systems Manager → Documents
2. Open `RestoreWorkspaceFromImage`
3. Execute automation
4. Select image and WorkSpace
5. **Confirm destruction of the existing WorkSpace**

---

### Restore via AWS CLI

```bash
aws ssm start-automation-execution \
  --document-name "RestoreWorkspaceFromImage" \
  --parameters "ImageId=wsi-xyz789,WorkspaceId=ws-abc123"
```

Check status:

```bash
aws ssm describe-automation-executions \
  --filters "Key=ExecutionId,Values=<execution-id>" \
  --query 'AutomationExecutionMetadataList[0].AutomationExecutionStatus'
```

---

## Configuration

Edit `terraform/variables.tf`:

| Variable           | Description          | Default             |
| ------------------ | -------------------- | ------------------- |
| `backup_schedule`  | Backup cron schedule | `cron(0 2 * * ? *)` |
| `retention_days`   | Image retention      | `30`                |
| `backup_tag_key`   | Backup tag key       | `AutoBackup`        |
| `backup_tag_value` | Backup tag value     | `enabled`           |

---

## Requirements

* Terraform ≥ 1.0
* AWS CLI configured
* IAM permissions for:

  * WorkSpaces
  * Lambda
  * EventBridge
  * SSM
  * IAM role creation

---

## Cost Considerations

* **Lambda:** negligible (runs once daily)
* **EventBridge:** negligible
* **WorkSpaces images:**

  * AWS currently does **not expose a separate pricing line item** for custom WorkSpaces images
  * No S3 storage is used
  * Costs are incurred only when **WorkSpaces are running**

> **Recommendation:** Always verify billing behavior in Cost Explorer for your region and account.

---

## Monitoring

* CloudWatch Logs (Lambda):

  * Backup success/failure
  * Image creation
  * Retention cleanup

---

## ⚠️ Critical Warnings

### Directory Deletion

**DO NOT delete the AWS Directory Service directory if backups exist.**

If deleted:

* Images become unusable for automated restore
* SSM automation will fail
* Recovery requires AWS Support intervention

**If planning directory migration (e.g., Simple AD → Entra ID):**

1. Contact AWS Support **before** deleting
2. Request guidance on image migration
3. Do not rely on this automation during directory changes

---

### User Account Deletion

Deleting a directory user makes their images **unrestorable** to that username. Images remain but cannot be deployed.

---

## License

MIT

---

## Contributing

Pull requests welcome.
Please run `terraform fmt` before submitting.

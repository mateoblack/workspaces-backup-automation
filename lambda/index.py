# lambda/index.py
import boto3
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

workspaces = boto3.client('workspaces')

def handler(event, context):
    tag_key = os.environ.get('BACKUP_TAG_KEY')
    tag_value = os.environ.get('BACKUP_TAG_VALUE')
    retention_days = int(os.environ.get('RETENTION_DAYS', 30))

    if not tag_key or not tag_value:
        raise ValueError("BACKUP_TAG_KEY and BACKUP_TAG_VALUE environment variables are required")

    backup_count = 0
    error_count = 0

    # Get all WorkSpaces with pagination
    paginator = workspaces.get_paginator('describe_workspaces')

    for page in paginator.paginate():
        for workspace in page['Workspaces']:
            workspace_id = workspace['WorkspaceId']

            # Check if workspace has backup tag
            try:
                tags_response = workspaces.describe_tags(ResourceId=workspace_id)
                tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}

                if tags.get(tag_key) == tag_value:
                    # Only backup if AVAILABLE and not being modified
                    if workspace['State'] == 'AVAILABLE':
                        if create_image(workspace_id, workspace.get('ComputerName', workspace_id)):
                            backup_count += 1
                        else:
                            error_count += 1
            except Exception as e:
                logger.error(f"Failed to process workspace {workspace_id}: {str(e)}")
                error_count += 1

    # Cleanup old images
    deleted_count = cleanup_old_images(retention_days)

    result = {
        'statusCode': 200,
        'body': {
            'backups_created': backup_count,
            'images_deleted': deleted_count,
            'errors': error_count
        }
    }

    logger.info(f"Backup complete: {result['body']}")

    if error_count > 0:
        logger.warning(f"Completed with {error_count} errors")

    return result

def create_image(workspace_id, computer_name):
    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
    image_name = f"{computer_name}-backup-{timestamp}"

    try:
        workspaces.create_workspace_image(
            Name=image_name,
            Description=f"Automated backup created on {timestamp}",
            WorkspaceId=workspace_id,
            Tags=[
                {'Key': 'AutomatedBackup', 'Value': 'true'},
                {'Key': 'CreatedDate', 'Value': timestamp}
            ]
        )
        logger.info(f"Created image {image_name} for {workspace_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create image for {workspace_id}: {str(e)}")
        return False

def cleanup_old_images(retention_days):
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    deleted_count = 0

    # Get all owned images with pagination
    next_token = None

    while True:
        if next_token:
            images_response = workspaces.describe_workspace_images(
                ImageType='OWNED',
                NextToken=next_token
            )
        else:
            images_response = workspaces.describe_workspace_images(ImageType='OWNED')

        for image in images_response.get('Images', []):
            # Check if it's an automated backup
            tags = {tag['Key']: tag['Value'] for tag in image.get('Tags', [])}

            if tags.get('AutomatedBackup') == 'true':
                created_date = tags.get('CreatedDate')
                if created_date:
                    try:
                        image_date = datetime.strptime(created_date, '%Y-%m-%d-%H%M')

                        if image_date < cutoff_date:
                            try:
                                workspaces.delete_workspace_image(ImageId=image['ImageId'])
                                logger.info(f"Deleted old image {image['Name']}")
                                deleted_count += 1
                            except Exception as e:
                                logger.error(f"Failed to delete {image['Name']}: {str(e)}")
                    except ValueError as e:
                        logger.warning(f"Invalid date format for image {image['Name']}: {created_date}")

        next_token = images_response.get('NextToken')
        if not next_token:
            break

    return deleted_count

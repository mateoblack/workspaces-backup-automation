# lambda/index.py
import boto3
import os
from datetime import datetime, timedelta

workspaces = boto3.client('workspaces')

def handler(event, context):
    tag_key = os.environ['BACKUP_TAG_KEY']
    tag_value = os.environ['BACKUP_TAG_VALUE']
    retention_days = int(os.environ['RETENTION_DAYS'])
    
    # Get all WorkSpaces
    response = workspaces.describe_workspaces()
    
    for workspace in response['Workspaces']:
        workspace_id = workspace['WorkspaceId']
        
        # Check if workspace has backup tag
        tags_response = workspaces.describe_tags(ResourceId=workspace_id)
        tags = {tag['Key']: tag['Value'] for tag in tags_response.get('TagList', [])}
        
        if tags.get(tag_key) == tag_value:
            # Only backup if AVAILABLE and not being modified
            if workspace['State'] == 'AVAILABLE':
                create_image(workspace_id, workspace.get('ComputerName', workspace_id))
    
    # Cleanup old images
    cleanup_old_images(retention_days)
    
    return {'statusCode': 200, 'body': 'Backup complete'}

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
        print(f"Created image {image_name} for {workspace_id}")
    except Exception as e:
        print(f"Failed to create image for {workspace_id}: {str(e)}")

def cleanup_old_images(retention_days):
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    images_response = workspaces.describe_workspace_images(ImageType='OWNED')
    
    for image in images_response.get('Images', []):
        # Check if it's an automated backup
        tags = {tag['Key']: tag['Value'] for tag in image.get('Tags', [])}
        
        if tags.get('AutomatedBackup') == 'true':
            created_date = tags.get('CreatedDate')
            if created_date:
                image_date = datetime.strptime(created_date, '%Y-%m-%d-%H%M')
                
                if image_date < cutoff_date:
                    try:
                        workspaces.delete_workspace_image(ImageId=image['ImageId'])
                        print(f"Deleted old image {image['Name']}")
                    except Exception as e:
                        print(f"Failed to delete {image['Name']}: {str(e)}")
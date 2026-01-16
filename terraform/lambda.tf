# lambda.tf

resource "aws_lambda_function" "workspace_image_manager" {
    filename = "lambda/image_manager.zip"
    function_name = "workspaces-image-manager"
    role = aws_iam_role.lambda_role.arn.arn
    handler = "index.handler"
    runtime = "python3.11" 
    timeout = 300

    environment {
        variables = {
        BACKUP_TAG_KEY = var.backup_tag_key
        BACKUP_TAG_VALUE = var.backup_tag_value
        RETENTION_DAYS = var.retention_days
        }
    }
}

resource "aws_iam_role" "lambda_role" {
    name = "workspace-backup_lambda-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "lambda.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy" "lambda_policy" {
    name = "workspaces-backup-policy"
    role = aws_iam_role.lambda_role.id 

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "workspaces:DescribeWorkspaces",
                    "workspaces:CreateWorkspaceImage", 
                    "workspaces:DescribeWorkspaceImage",
                    "workspaces:DescribeTags"
                ]
                Resource = "*"
            },
            {
                Effect = "Allow"
                Action = [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ]
                Resource = "arn:aws:logs:*:*:*"
            }
        ]
    })
}
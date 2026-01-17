# ssm.tf

resource "aws_ssm_document" "restore_workspace" {
    name = "RestoreWorkspaceFromImage"
    document_type = "Automation"
    document_format = "YAML"

    content = file("${path.module}/../ssm/restore_runbook.yml")
}

resource "aws_iam_role" "ssm_automation_role" {
    name = "workspaces-restore_automation-role"
    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "ssm.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_role_policy" "ssm_automation_role" {
    name = "workspaces-restore-policy"
    role = aws_iam_role.ssm_automation_role.id

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "workspaces:RebuildWorkspaces",
                    "workspaces:DescribeWorkspaces",
                    "workspaces:DescribeWorkspaceImages"
                ]
                Resource = "*"
            }
        ]
    })
}


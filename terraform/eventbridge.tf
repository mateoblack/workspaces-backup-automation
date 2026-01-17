# eventbridge.tf 

resource "aws_cloudwatch_event_rule" "backup_schedule" {
    name              = "workspaces-backup-schedule"
    description       = "Trigger WorkSpaces image creation"
    schedule_expression = var.backup_schedule
}

resource "aws_cloudwatch_event_target" "lambda" {
    rule    = aws_cloudwatch_event_rule.backup_schedule.name
    target_id = "WorkspacesBackupLambda" 
    arn     = aws_lambda_function.workspace_image_manager.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
    statement_id = "AllowExecutionFromEventBridge"
    action       = "lambda:InvokeFunction"
    function_name = aws_lambda_function.workspace_image_manager.function_name
    principal = "events.amazonaws.com"
    source_arn = aws_cloudwatch_event_rule.backup_schedule.arn
}
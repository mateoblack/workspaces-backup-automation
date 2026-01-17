# outputs.tf

output "lambda_function_name" {
    description = "Name of the Lambda function"
    value       = aws_lambda_function.workspace_image_manager.function_name
}

output "lambda_function_arn" {
    description = "ARN of the Lambda function"
    value       = aws_lambda_function.workspace_image_manager.arn
}

output "eventbridge_rule_name" {
    description = "Name of the EventBridge schedule rule"
    value       = aws_cloudwatch_event_rule.backup_schedule.name
}

output "ssm_document_name" {
    description = "Name of the SSM automation document for restore"
    value       = aws_ssm_document.restore_runbook.name
}

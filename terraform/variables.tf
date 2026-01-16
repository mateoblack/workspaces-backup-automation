variable "backup_tag_key" {
    default = "AutoBack" 
}

variable "backup_tag_value" {
    default = "enabled" 
}

variable "retention_days" {
    default = 30 
}

variable "backup_schedule" {
    default = "cron(0 2 * * ? *)" # 2 AM daily 
}
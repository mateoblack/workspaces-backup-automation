# provider.tf

terraform {
    required_version = ">= 1.0"

    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = ">= 5.0"
        }
        archive = {
            source  = "hashicorp/archive"
            version = ">= 2.0"
        }
    }
}

provider "aws" {
    # Configuration inherited from environment or AWS CLI profile
    # Set AWS_REGION, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    # Or use: aws configure
}

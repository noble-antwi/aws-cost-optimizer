variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for testing"
  type        = string
  default     = "t3.micro"
}

variable "rds_instance_class" {
  description = "RDS instance class for testing"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_password" {
  description = "RDS database password"
  type        = string
  sensitive   = true
  default     = "TestPassword123!"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "test"
}

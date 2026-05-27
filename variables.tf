variable "aws_region" {
  type        = string
  description = "The AWS region to deploy resources"
  default     = "eu-central-1"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size"
  default     = "t3.micro"
}

variable "project_name" {
  type        = string
  description = "Project name tag"
  default     = "ce-observability-project-gz-li"
}

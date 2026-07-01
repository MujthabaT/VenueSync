variable "aws_region" {
  description = "AWS region"
  default     = "ap-south-1"
}

variable "key_pair_name" {
  description = "AWS key pair"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  default     = "t3.micro"
}

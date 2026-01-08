terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================================
# VPC & NETWORKING
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "cost-optimizer-test-vpc"
  }
}

resource "aws_subnet" "main" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "cost-optimizer-test-subnet"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "cost-optimizer-test-igw"
  }
}

resource "aws_route_table" "main" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "cost-optimizer-test-rt"
  }
}

resource "aws_route_table_association" "main" {
  subnet_id      = aws_subnet.main.id
  route_table_id = aws_route_table.main.id
}

resource "aws_security_group" "test" {
  name        = "cost-optimizer-test-sg"
  description = "Security group for cost optimizer testing"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cost-optimizer-test-sg"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# EC2 INSTANCES (Testing Idle Detection)
# ============================================================================

# Active instance (high CPU)
resource "aws_instance" "active" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.test.id]

  tags = {
    Name           = "cost-optimizer-active-instance"
    TestType       = "active"
    CostOptimizer  = "test"
  }

  user_data = base64encode(<<-EOF
              #!/bin/bash
              # Generate CPU load to appear active
              yes > /dev/null &
              EOF
  )
}

# Idle instance (low CPU)
resource "aws_instance" "idle" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.test.id]

  tags = {
    Name           = "cost-optimizer-idle-instance"
    TestType       = "idle"
    CostOptimizer  = "test"
  }
}

# ============================================================================
# EBS VOLUMES (Testing Unattached Detection)
# ============================================================================

# Attached volume (should not be flagged)
resource "aws_ebs_volume" "attached" {
  availability_zone = data.aws_availability_zones.available.names[0]
  size              = 100
  type              = "gp3"

  tags = {
    Name           = "cost-optimizer-attached-volume"
    TestType       = "attached"
    CostOptimizer  = "test"
  }
}

resource "aws_volume_attachment" "attached" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.attached.id
  instance_id = aws_instance.active.id
}

# Unattached volume (should be flagged)
resource "aws_ebs_volume" "unattached" {
  availability_zone = data.aws_availability_zones.available.names[0]
  size              = 50
  type              = "gp3"

  tags = {
    Name           = "cost-optimizer-unattached-volume"
    TestType       = "unattached"
    CostOptimizer  = "test"
  }
}

# ============================================================================
# EBS SNAPSHOTS (Testing Outdated Detection)
# ============================================================================

resource "aws_ebs_snapshot" "test" {
  volume_id = aws_ebs_volume.unattached.id

  tags = {
    Name           = "cost-optimizer-test-snapshot"
    TestType       = "snapshot"
    CostOptimizer  = "test"
  }
}

# ============================================================================
# ELASTIC IPs (Testing Unassociated Detection)
# ============================================================================

# Associated Elastic IP (should not be flagged)
resource "aws_eip" "associated" {
  instance = aws_instance.active.id
  domain   = "vpc"

  tags = {
    Name           = "cost-optimizer-associated-eip"
    TestType       = "associated"
    CostOptimizer  = "test"
  }

  depends_on = [aws_internet_gateway.main]
}

# Unassociated Elastic IP (should be flagged)
resource "aws_eip" "unassociated" {
  domain = "vpc"

  tags = {
    Name           = "cost-optimizer-unassociated-eip"
    TestType       = "unassociated"
    CostOptimizer  = "test"
  }

  depends_on = [aws_internet_gateway.main]
}

# ============================================================================
# RDS INSTANCES (Testing Idle Database Detection)
# ============================================================================

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "cost-optimizer-db-subnet-group"
  subnet_ids = [aws_subnet.main.id]

  tags = {
    Name = "cost-optimizer-db-subnet-group"
  }
}

# Active RDS instance (with connections)
resource "aws_db_instance" "active" {
  identifier            = "cost-optimizer-active-db"
  engine                = "mysql"
  engine_version        = "8.0"
  instance_class        = var.rds_instance_class
  allocated_storage     = 20
  storage_type          = "gp3"
  db_name               = "testdb"
  username              = "admin"
  password              = var.rds_password
  db_subnet_group_name  = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.test.id]
  skip_final_snapshot   = true
  publicly_accessible   = false
  multi_az              = false

  tags = {
    Name           = "cost-optimizer-active-rds"
    TestType       = "active"
    CostOptimizer  = "test"
  }
}

# Idle RDS instance (no connections)
resource "aws_db_instance" "idle" {
  identifier            = "cost-optimizer-idle-db"
  engine                = "mysql"
  engine_version        = "8.0"
  instance_class        = var.rds_instance_class
  allocated_storage     = 20
  storage_type          = "gp3"
  db_name               = "testdb"
  username              = "admin"
  password              = var.rds_password
  db_subnet_group_name  = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.test.id]
  skip_final_snapshot   = true
  publicly_accessible   = false
  multi_az              = false

  tags = {
    Name           = "cost-optimizer-idle-rds"
    TestType       = "idle"
    CostOptimizer  = "test"
  }
}

# ============================================================================
# DATA SOURCES
# ============================================================================

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

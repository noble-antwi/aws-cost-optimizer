output "active_ec2_instance_id" {
  description = "ID of the active EC2 instance"
  value       = aws_instance.active.id
}

output "idle_ec2_instance_id" {
  description = "ID of the idle EC2 instance"
  value       = aws_instance.idle.id
}

output "attached_ebs_volume_id" {
  description = "ID of the attached EBS volume"
  value       = aws_ebs_volume.attached.id
}

output "unattached_ebs_volume_id" {
  description = "ID of the unattached EBS volume"
  value       = aws_ebs_volume.unattached.id
}

output "snapshot_id" {
  description = "ID of the test snapshot"
  value       = aws_ebs_snapshot.test.id
}

output "associated_eip" {
  description = "Associated Elastic IP address"
  value       = aws_eip.associated.public_ip
}

output "unassociated_eip" {
  description = "Unassociated Elastic IP address"
  value       = aws_eip.unassociated.public_ip
}

output "active_rds_endpoint" {
  description = "Endpoint of the active RDS instance"
  value       = aws_db_instance.active.endpoint
}

output "idle_rds_endpoint" {
  description = "Endpoint of the idle RDS instance"
  value       = aws_db_instance.idle.endpoint
}

output "vpc_id" {
  description = "ID of the test VPC"
  value       = aws_vpc.main.id
}

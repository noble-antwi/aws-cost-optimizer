# Terraform Configuration for Cost Optimizer Testing

This directory contains Terraform configuration to provision AWS resources for testing the AWS Cost Optimizer tool.

## Resources Created

The Terraform configuration will create:

### EC2 Instances
- **Active Instance**: High CPU usage (for comparison)
- **Idle Instance**: Low/no CPU usage (should be detected)

### EBS Volumes
- **Attached Volume**: 100GB gp3 attached to active instance
- **Unattached Volume**: 50GB gp3 (should be detected as unused)

### EBS Snapshots
- **Test Snapshot**: Created from the unattached volume

### Elastic IPs
- **Associated EIP**: Assigned to the active instance
- **Unassociated EIP**: Floating EIP (should be detected as unused, costing ~$3.60/month)

### RDS Instances
- **Active RDS**: MySQL instance for comparison
- **Idle RDS**: MySQL instance with low/no connections (should be detected)

### Networking
- VPC with subnet
- Security group
- Internet Gateway
- Route table

## Prerequisites

1. Install Terraform: https://www.terraform.io/downloads.html
2. Configure AWS credentials: `aws configure`
3. Verify AWS CLI access: `aws sts get-caller-identity`

## Usage

### Initialize Terraform
```bash
cd terraform
terraform init
```

### Review the Plan
```bash
terraform plan
```

### Apply Configuration
```bash
terraform apply
```

### Get Resource IDs
```bash
terraform output
```

### Destroy Resources (Clean Up)
```bash
terraform destroy
```

## Variables

You can customize the deployment by editing `terraform.tfvars` or passing variables:

```bash
terraform apply -var="aws_region=us-west-2" -var="ec2_instance_type=t3.small"
```

Available variables:
- `aws_region`: AWS region (default: us-east-1)
- `ec2_instance_type`: EC2 instance type (default: t3.micro)
- `rds_instance_class`: RDS instance class (default: db.t3.micro)
- `rds_password`: RDS database password (default: TestPassword123!)

## Testing the Cost Optimizer

1. Deploy resources with Terraform
2. Wait 5-10 minutes for CloudWatch metrics to populate
3. Run the cost optimizer:
   ```bash
   python src/main.py --region us-east-1
   ```
4. Check the reports in `reports/` directory

## Cost Estimate

This test infrastructure costs approximately **$15-20/month** on us-east-1:
- EC2 instances: ~$3/month
- EBS volumes: ~$3/month
- Elastic IPs: ~$3.60/month (unassociated)
- RDS instances: ~$8-10/month

Remember to destroy resources with `terraform destroy` when done testing to avoid unnecessary charges.

## Notes

- All resources are tagged with `CostOptimizer: test` for easy identification
- The active EC2 instance runs a load generator to show CPU usage
- RDS instances are set to skip final snapshot for easy cleanup
- Modify security groups if you need different access rules

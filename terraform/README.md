# Terraform Configuration for Cost Optimizer Testing

This directory contains Terraform configuration to provision AWS resources for testing and validating the AWS Cost Optimizer tool. It creates a complete testing environment with active and idle resources across multiple AWS service types.

## Resources Created

The Terraform configuration automatically provisions:

### Compute
- **Active EC2 Instance** (t3.micro) - Continuous CPU load for baseline comparison
- **Idle EC2 Instance** (t3.micro) - Minimal CPU usage (< 0.2%) - should be detected as idle
- **Load Generator EC2** (t3.micro) - Runs queries on RDS for load testing

### Storage
- **Attached EBS Volume** (100GB gp3) - Connected to active instance
- **Unattached EBS Volume** (50GB gp3) - Floating volume - should be detected as unused

### Snapshots & Backups
- **EBS Snapshot** (50GB) - Created from test volume for snapshot analysis

### Networking
- **Associated Elastic IP** - Assigned to active instance
- **Unassociated Elastic IP** - Floating EIP (~$3.65/month cost) - should be detected as unused
- VPC with subnet, security groups, and routing

### Databases
- **Active RDS Database** (db.t3.micro MySQL) - Load generator runs continuous queries
- **Idle RDS Database** (db.t3.micro MySQL) - Zero connections, low CPU - should be detected as idle

## Prerequisites

1. **Terraform**: `brew install terraform` (macOS) or [download](https://www.terraform.io/downloads.html)
2. **AWS CLI**: `brew install awscli` with `aws configure`
3. **AWS Credentials**: Ensure `~/.aws/credentials` is configured
4. **IAM Permissions**: EC2, EBS, RDS, CloudWatch full access

Verify setup:
```bash
aws sts get-caller-identity
terraform version
```

## Usage

### Initialize & Plan
```bash
cd terraform
terraform init
terraform plan  # Review what will be created
```

### Deploy Infrastructure
```bash
terraform apply  # Review and type 'yes' to confirm
```

### View Created Resources
```bash
terraform output
aws ec2 describe-instances --region us-east-1
aws rds describe-db-instances --region us-east-1
```

### Cleanup
```bash
terraform destroy  # Type 'yes' to confirm
```

## Configuration

Edit `terraform.tfvars` to customize:

```hcl
aws_region           = "us-east-1"     # AWS region
ec2_instance_type    = "t3.micro"      # Instance type
rds_instance_class   = "db.t3.micro"   # RDS class
rds_password         = "TestPassword123!"  # DB password
```

Override via command line:
```bash
terraform apply -var="aws_region=us-west-2"
```

## Testing Workflow

### Step 1: Deploy Resources
```bash
cd terraform
terraform apply -auto-approve
cd ..
```

### Step 2: Wait for Metrics
CloudWatch needs 5-10 minutes to collect baseline metrics. The RDS load generator automatically starts generating traffic on the "active" database.

### Step 3: Run Cost Optimizer
```bash
python src/main.py --region us-east-1
```

### Step 4: Review Reports
Reports are in `reports/cost-optimization-YYYY-MM-DD_HH-MM-SS/`:
- `cost-optimization-report.html` - Visual dashboard
- `idle-ec2-instances.csv` - Should show 2 instances with CPU metrics
- `idle-rds-instances.csv` - Should show 1 idle database
- `unattached-ebs-volumes.csv` - Should show 1 volume
- `unused-elastic-ips.csv` - Should show 1 unassociated EIP

### Step 5: Cleanup
```bash
cd terraform
terraform destroy -auto-approve
```

## Expected Findings

When you run the cost optimizer on this infrastructure:

| Resource | Expected Count | Reason |
|----------|---|---|
| Idle EC2 | 2 | RDS load generator + idle instance (both have low CPU) |
| Idle RDS | 1 | Idle database with 0 connections |
| Unattached EBS | 1 | Not attached to any instance |
| Unused Elastic IP | 1 | Not associated with any resource |
| Outdated Snapshots | 0-1 | Depends on age threshold |

**Total potential savings: ~$39/month ($468/year)**

## Cost Breakdown

This test infrastructure costs approximately **$15-20/month**:

| Resource | Cost/Month |
|----------|-----------|
| 3x EC2 t3.micro instances | ~$4-5 |
| 2x EBS volumes (150GB gp3) | ~$5-6 |
| Elastic IP (unassociated) | ~$3.65 |
| 2x RDS db.t3.micro MySQL | ~$8-10 |
| **Total** | **~$20-24** |

⚠️ **Remember**: Run `terraform destroy` when done testing to avoid ongoing charges.

## Troubleshooting

### CloudWatch Metrics Not Available
- Wait 10-15 minutes after `terraform apply`
- Metrics start appearing in CloudWatch gradually
- Cost Optimizer shows CPU data once metrics are available

### RDS Load Generator Not Running
- Check EC2 instance status: `aws ec2 describe-instances --region us-east-1`
- SSH into load generator: `aws ssm start-session --target <instance-id> --region us-east-1`
- Verify RDS endpoint in AWS console

### Terraform State Issues
- Delete state: `rm -rf .terraform terraform.tfstate*`
- Reinitialize: `terraform init`

## Next Steps

After validating findings:
1. Adjust thresholds in `config/config.yaml`
2. Re-run analyzer with different settings
3. Generate reports in different formats
4. Integrate into CI/CD pipeline

---

For main project documentation, see [README.md](../README.md)

## Notes

- All resources are tagged with `CostOptimizer: test` for easy identification
- The active EC2 instance runs a load generator to show CPU usage
- RDS instances are set to skip final snapshot for easy cleanup
- Modify security groups if you need different access rules

# Quick Start Guide

## Prerequisites
- Python 3.8 or higher
- AWS Account with IAM permissions
- AWS CLI configured (or AWS credentials)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure AWS Credentials

**Option A: Using AWS CLI**
```bash
aws configure
```

**Option B: Using Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 5. Configure the Application
```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your preferences
```

### 6. Run Your First Analysis
```bash
python src/main.py --region us-east-1
```

## First Run Example

```bash
# Dry-run mode (no changes, just analysis)
python src/main.py --dry-run

# Analyze specific region
python src/main.py --region us-east-1

# Analyze all regions
python src/main.py --all-regions

# Generate only HTML report
python src/main.py --output-format html

# Verbose output for debugging
python src/main.py --verbose
```

## Understanding the Output

The tool will create a `reports/` directory with:
- `cost-optimization-report.json` - Machine-readable JSON report
- `idle-ec2-instances.csv` - CSV file with idle EC2 instances
- `unattached-ebs-volumes.csv` - CSV file with unattached volumes
- `outdated-snapshots.csv` - CSV file with old snapshots
- `cost-optimization-report.html` - Interactive HTML report

## Next Steps

1. **Review the HTML Report**: Open the HTML report in your browser to see detailed findings
2. **Customize Configuration**: Edit `config/config.yaml` to adjust thresholds
3. **Implement Recommendations**: Review and implement cost-saving recommendations
4. **Schedule Regular Runs**: Set up a cron job or scheduled task

## Troubleshooting

### No AWS Credentials Found
```bash
# Make sure AWS CLI is configured
aws sts get-caller-identity

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Permission Errors
Make sure your IAM user/role has these permissions:
- `ec2:DescribeInstances`
- `ec2:DescribeVolumes`
- `ec2:DescribeSnapshots`
- `cloudwatch:GetMetricStatistics`

### Region Not Available
```bash
# List available regions
aws ec2 describe-regions --query 'Regions[].RegionName'
```

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub for bugs or feature requests

## Example Workflow

```bash
# 1. Initial setup
git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp config/config.example.yaml config/config.yaml
# Edit config.yaml if needed

# 3. Run analysis
python src/main.py --all-regions --output-format html

# 4. View results
open reports/cost-optimization-*/cost-optimization-report.html
```

That's it! You're ready to start optimizing your AWS costs! 

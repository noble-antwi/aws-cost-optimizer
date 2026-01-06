# AWS Cost Optimization Analysis Tool

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![AWS](https://img.shields.io/badge/AWS-Boto3-orange)
![License](https://img.shields.io/badge/license-MIT-green)

A Python-based tool that analyzes AWS resource utilization and identifies cost optimization opportunities by detecting idle EC2 instances, unattached EBS volumes, and outdated snapshots.

## Features

- **Idle EC2 Instance Detection**: Identifies EC2 instances with low CPU utilization over a specified period
- **Unattached EBS Volume Analysis**: Finds EBS volumes not attached to any instance
- **Outdated Snapshot Identification**: Locates snapshots older than a specified retention period
- **Cost Estimation**: Calculates potential monthly savings from optimization
- **Multiple Report Formats**: Generates reports in JSON, CSV, and HTML formats
- **Dry-Run Mode**: Preview findings without making any changes

## Architecture

```
┌─────────────────┐
│   AWS Account   │
└────────┬────────┘
         │
         ├─► EC2 Instances
         ├─► EBS Volumes
         ├─► EBS Snapshots
         └─► CloudWatch Metrics
                │
                ▼
     ┌──────────────────────┐
     │  Cost Optimizer Tool │
     │    (Boto3 + Python)  │
     └──────────┬───────────┘
                │
                ├─► Analysis Engine
                ├─► Cost Calculator
                └─► Report Generator
                        │
                        ▼
              ┌─────────────────┐
              │  Output Reports │
              │ JSON | CSV | HTML│
              └─────────────────┘
```

## Prerequisites

- Python 3.8 or higher
- AWS Account with appropriate IAM permissions
- AWS CLI configured or AWS credentials set up

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure AWS credentials:
```bash
aws configure
# Or set environment variables:
# export AWS_ACCESS_KEY_ID=your_key
# export AWS_SECRET_ACCESS_KEY=your_secret
# export AWS_DEFAULT_REGION=us-east-1
```

## Configuration

Copy the example configuration file and customize it:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` to set your preferences:

```yaml
# Analysis thresholds
ec2:
  cpu_threshold: 5.0  # CPU utilization percentage
  analysis_period_days: 7

ebs:
  snapshot_retention_days: 90

# AWS regions to analyze
regions:
  - us-east-1
  - us-west-2

# Report settings
reports:
  output_dir: reports
  formats:
    - json
    - csv
    - html
```

## Usage

### Basic Analysis

Run a complete cost optimization analysis:

```bash
python src/main.py --profile default --region us-east-1
```

### Dry-Run Mode

Preview findings without making changes:

```bash
python src/main.py --dry-run
```

### Analyze Specific Resources

```bash
# Only EC2 instances
python src/main.py --resource-type ec2

# Only EBS volumes
python src/main.py --resource-type ebs

# Only snapshots
python src/main.py --resource-type snapshots
```

### Multi-Region Analysis

```bash
python src/main.py --all-regions
```

### Generate Specific Report Format

```bash
python src/main.py --output-format html
```

## IAM Permissions Required

The tool requires the following AWS IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSnapshots",
        "ec2:DescribeRegions",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage"
      ],
      "Resource": "*"
    }
  ]
}
```

## Sample Output

### Console Output
```
AWS Cost Optimization Analysis Report
=====================================
Analysis Date: 2026-01-06 15:30:45
Region: us-east-1

Findings Summary:
- Idle EC2 Instances: 3 (Potential Savings: $156.00/month)
- Unattached EBS Volumes: 5 (Potential Savings: $50.00/month)
- Outdated Snapshots: 12 (Potential Savings: $18.00/month)

Total Potential Monthly Savings: $224.00
Total Potential Annual Savings: $2,688.00

Detailed reports saved to: reports/cost-optimization-2026-01-06/
```

### HTML Report Preview
The tool generates interactive HTML reports with charts and detailed resource information.

## Project Structure

```
aws-cost-optimizer/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── base_analyzer.py       # Base analyzer class
│   │   ├── ec2_analyzer.py        # EC2 instance analysis
│   │   ├── ebs_analyzer.py        # EBS volume analysis
│   │   └── snapshot_analyzer.py   # Snapshot analysis
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── aws_client.py          # AWS client wrapper
│   │   ├── cost_calculator.py     # Cost estimation logic
│   │   └── config_loader.py       # Configuration handling
│   └── reports/
│       ├── __init__.py
│       ├── json_reporter.py       # JSON report generator
│       ├── csv_reporter.py        # CSV report generator
│       └── html_reporter.py       # HTML report generator
├── config/
│   ├── config.example.yaml        # Example configuration
│   └── pricing.yaml               # AWS pricing data
├── tests/
│   ├── __init__.py
│   ├── test_ec2_analyzer.py
│   ├── test_ebs_analyzer.py
│   └── test_cost_calculator.py
├── reports/                       # Generated reports directory
├── docs/
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
├── .gitignore
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

## Roadmap

- [x] EC2 idle instance detection
- [x] Unattached EBS volume analysis
- [x] Outdated snapshot identification
- [ ] Elastic IP address analysis
- [ ] Unused load balancers detection
- [ ] RDS idle database instances
- [ ] Slack/Email notifications
- [ ] Automated remediation (with approval workflow)
- [ ] CloudWatch dashboard integration
- [ ] Cost trend analysis over time

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Noble Ackerson**  
*Securing the digital world, one byte at a time*

- LinkedIn: [Your LinkedIn]
- GitHub: [Your GitHub]
- Email: [Your Email]

## Acknowledgments

- AWS Boto3 Documentation
- AWS Cost Explorer API
- Python Community

## Disclaimer

This tool is for analysis purposes only. Always review recommendations before making infrastructure changes. The cost estimates are approximate and may not reflect actual AWS billing.

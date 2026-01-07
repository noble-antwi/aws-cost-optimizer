# AWS Cost Optimization Tool

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/) [![AWS](https://img.shields.io/badge/AWS-Boto3-orange)](https://boto3.amazonaws.com/) [![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A Python-based CLI tool that analyzes AWS resources and identifies cost optimization opportunities by detecting **idle EC2 instances**, **unattached EBS volumes**, and **outdated snapshots**.

![HTML Report](assets/images/06_html-report-generated.png)

---

## What This Tool Does

| Resource | Detection Criteria | Potential Savings |
|----------|-------------------|-------------------|
| **EC2 Instances** | CPU utilization < 5% over 7 days | Stop or rightsize |
| **EBS Volumes** | Unattached for configurable days | Delete unused volumes |
| **Snapshots** | Older than retention period (default: 90 days) | Remove outdated backups |

---

## Quick Start

### Prerequisites
- Python 3.8+
- AWS CLI configured with credentials
- IAM permissions for EC2, EBS, CloudWatch (see [IAM Policy](#-iam-permissions))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config/config.example.yaml config/config.yaml
```

### Run Analysis

```bash
# Analyze single region
python src/main.py --profile default --region us-east-1

# Analyze all AWS regions
python src/main.py --all-regions
```

---

## Sample Output

### Terminal Output
When the tool runs, it displays a rich terminal interface showing progress and findings:

![Terminal Output](assets/images/04_output_after_threshold_change.png)

### Detection Example
The tool found **2 unattached EBS volumes** in my AWS account:

![EBS Volumes Detected](assets/images/05_Actual_EBS_volumes_in_the_account.png)

### HTML Report
Interactive HTML reports are generated with detailed findings and cost estimates:

![HTML Report](assets/images/06_html-report-generated.png)

---

## Configuration

Edit `config/config.yaml` to customize detection thresholds:

```yaml
# EC2 Analysis
ec2:
  cpu_threshold: 5.0              # CPU % below this = idle
  analysis_period_days: 7         # Days to analyze
  minimum_uptime_hours: 24        # Ignore recently launched

# EBS Analysis  
ebs:
  unattached_days_threshold: 7    # Days unattached before flagging

# Snapshot Analysis
snapshots:
  retention_days: 90              # Snapshots older than this

# Regions to analyze
regions:
  - us-east-1
  - us-west-2
  # Or use --all-regions flag
```

---

## Report Formats

Reports are generated in three formats:

| Format | Use Case |
|--------|----------|
| **JSON** | Integration with other tools, automation |
| **CSV** | Excel analysis, data processing |
| **HTML** | Human-readable, shareable reports |

Reports are saved to: `reports/cost-optimization-YYYY-MM-DD_HH-MM-SS/`

---

## Architecture

![Architecture Diagram](assets/images/architecture-diagram.png)

---

## IAM Permissions

Create an IAM policy with these permissions:

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
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## CLI Options

```bash
python src/main.py [OPTIONS]

Options:
  --profile TEXT      AWS profile name (default: default)
  --region TEXT       AWS region to analyze
  --all-regions       Analyze all available AWS regions
  --resource-type     Filter: ec2, ebs, or snapshots
  --output-format     Report format: json, csv, or html
  --dry-run           Preview mode (default behavior)
  --help              Show help message
```

---

## Roadmap

- [x] EC2 idle instance detection
- [x] Unattached EBS volume analysis
- [x] Outdated snapshot identification
- [x] Multi-region support
- [x] HTML/JSON/CSV reports
- [ ] Elastic IP analysis
- [ ] RDS idle database detection
- [ ] Slack/Email notifications
- [ ] Lambda function deployment
- [ ] Automated remediation

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Noble Antwi**

---

## Disclaimer

This tool provides cost optimization **recommendations only**. Always review findings before making infrastructure changes. Cost estimates are approximate and may differ from actual AWS billing.

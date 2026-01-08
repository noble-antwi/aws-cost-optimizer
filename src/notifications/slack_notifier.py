"""
Slack Notifier
Sends cost optimization findings to Slack
"""

import json
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class SlackNotifier:
    """Sends notifications to Slack webhook"""
    
    def __init__(self, webhook_url=None):
        """
        Initialize Slack Notifier
        
        Args:
            webhook_url (str): Slack incoming webhook URL (optional)
        """
        self.webhook_url = webhook_url
        self.enabled = bool(webhook_url and webhook_url.strip())
    
    def send_findings(self, combined_results):
        """
        Send cost optimization findings to Slack
        
        Args:
            combined_results (dict): Analysis results from all regions
        """
        if not self.enabled:
            logger.debug("Slack notifications disabled (no webhook URL configured)")
            return
        
        try:
            # Check if there are any findings
            total_findings = sum(
                len(result.get('resources', []))
                for result in combined_results.values()
            )
            
            if total_findings == 0:
                logger.debug("No findings to report to Slack")
                return
            
            message = self._build_message(combined_results)
            self._post_to_slack(message)
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
    
    def _build_message(self, combined_results):
        """
        Build formatted Slack message with rich formatting
        
        Args:
            combined_results (dict): Analysis results
            
        Returns:
            dict: Formatted Slack message payload
        """
        # Calculate totals
        total_findings = 0
        total_monthly_savings = 0.0
        finding_sections = []
        
        resource_config = {
            'idle_ec2_instances': {
                'label': 'Idle EC2 Instances',
                'emoji': '💤',
                'color': '#FF6B6B'
            },
            'unattached_ebs_volumes': {
                'label': 'Unattached EBS Volumes',
                'emoji': '💾',
                'color': '#4ECDC4'
            },
            'outdated_snapshots': {
                'label': 'Outdated Snapshots',
                'emoji': '📸',
                'color': '#95E1D3'
            },
            'unused_elastic_ips': {
                'label': 'Unused Elastic IPs',
                'emoji': '🌐',
                'color': '#FFE66D'
            },
            'idle_rds_instances': {
                'label': 'Idle RDS Databases',
                'emoji': '🗄️',
                'color': '#A8E6CF'
            }
        }
        
        for resource_type, config in resource_config.items():
            if resource_type in combined_results:
                resources = combined_results[resource_type].get('resources', [])
                if resources:
                    count = len(resources)
                    savings = combined_results[resource_type].get('total_monthly_savings', 0)
                    total_findings += count
                    total_monthly_savings += savings
                    
                    # Create section for this resource type
                    finding_sections.append({
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*{config['emoji']} {config['label']}*\n{count} resource{'s' if count > 1 else ''}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Monthly Savings*\n${savings:.2f}"
                            }
                        ]
                    })
        
        # Calculate annual savings
        total_annual_savings = total_monthly_savings * 12
        
        # Build the full message with professional formatting
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 AWS Cost Optimization Report",
                    "emoji": True
                }
            },
            
            # Summary section
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📊 *Analysis completed at:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                }
            },
            
            {
                "type": "divider"
            },
            
            # Key metrics
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Resources Found*\n{total_findings} idle resource{'s' if total_findings != 1 else ''}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Monthly Savings Potential*\n💰 ${total_monthly_savings:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Annual Savings Potential*\n📈 ${total_annual_savings:.2f}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status*\n{'✅ Issues Found' if total_findings > 0 else '✓ All Clear'}"
                    }
                ]
            },
            
            {
                "type": "divider"
            }
        ]
        
        # Add detailed findings
        if finding_sections:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*📋 Detailed Findings:*"
                }
            })
            blocks.extend(finding_sections)
            
            blocks.append({
                "type": "divider"
            })
        
        # Call to action
        if total_findings > 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "🎯 *Recommended Actions:*\n• Review identified idle resources\n• Verify they are not needed\n• Stop or delete to reduce costs\n• Monitor for future optimization opportunities"
                }
            })
            
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "💡 This is an automated cost optimization analysis. Please review findings before taking action."
                    }
                ]
            })
        
        return {"blocks": blocks}
    
    def _post_to_slack(self, message):
        """
        Post message to Slack webhook
        
        Args:
            message (dict): Message payload
        """
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent successfully")
            else:
                logger.error(
                    f"Slack notification failed with status {response.status_code}: "
                    f"{response.text}"
                )
        except requests.exceptions.Timeout:
            logger.error("Slack notification timeout (10 seconds)")
        except requests.exceptions.RequestException as e:
            logger.error(f"Slack notification request failed: {str(e)}")

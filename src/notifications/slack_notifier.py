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
        Build formatted Slack message
        
        Args:
            combined_results (dict): Analysis results
            
        Returns:
            dict: Formatted Slack message payload
        """
        # Calculate totals
        total_findings = 0
        total_monthly_savings = 0
        finding_summary = []
        
        resource_labels = {
            'idle_ec2_instances': ('Idle EC2 Instances', ':sleeping:'),
            'unattached_ebs_volumes': ('Unattached EBS Volumes', ':floppy_disk:'),
            'outdated_snapshots': ('Outdated Snapshots', ':camera:'),
            'unused_elastic_ips': ('Unused Elastic IPs', ':globe_with_meridians:'),
            'idle_rds_instances': ('Idle RDS Databases', ':database:')
        }
        
        for resource_type, (label, emoji) in resource_labels.items():
            if resource_type in combined_results:
                resources = combined_results[resource_type].get('resources', [])
                if resources:
                    count = len(resources)
                    savings = combined_results[resource_type].get('total_monthly_savings', 0)
                    total_findings += count
                    total_monthly_savings += savings
                    
                    finding_summary.append(
                        f"{emoji} {label}: {count} (${savings:.2f}/month)"
                    )
        
        # Build fields
        fields = []
        if finding_summary:
            fields.append({
                "type": "mrkdwn",
                "text": "*📊 Findings Summary:*\n" + "\n".join(finding_summary)
            })
        
        # Calculate annual savings
        total_annual_savings = total_monthly_savings * 12
        
        fields.append({
            "type": "mrkdwn",
            "text": f"*💰 Total Potential Savings:*\n${total_monthly_savings:.2f}/month (${total_annual_savings:.2f}/year)"
        })
        
        # Build message
        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🚀 *AWS Cost Optimization Analysis*\n_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "fields": fields
                }
            ]
        }
        
        if total_findings > 0:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"✅ Found *{total_findings}* resources with optimization opportunities"
                }
            })
        
        return message
    
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

"""
Elastic IP Analyzer
Analyzes Elastic IPs to identify unused/unattached addresses
"""

import logging
from datetime import datetime
from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class EIPAnalyzer(BaseAnalyzer):
    """Analyzes Elastic IPs for unused addresses"""
    
    def __init__(self, ec2_client, config):
        """
        Initialize EIP Analyzer
        
        Args:
            ec2_client: Boto3 EC2 client
            config (dict): Application configuration
        """
        super().__init__(ec2_client, config)
    
    def analyze(self):
        """
        Analyze Elastic IPs for unused addresses
        
        Returns:
            dict: Analysis results with unused Elastic IPs
        """
        logger.info("Starting Elastic IP analysis")
        
        try:
            # Get all Elastic IPs
            addresses = self._get_all_addresses()
            logger.info(f"Found {len(addresses)} Elastic IPs")
            
            # Analyze each address
            for address in addresses:
                if self._is_address_unused(address):
                    self._add_unused_address(address)
            
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error analyzing Elastic IPs: {str(e)}")
            raise
    
    def _get_all_addresses(self):
        """
        Get all Elastic IP addresses
        
        Returns:
            list: List of Elastic IP addresses
        """
        try:
            response = self.client.describe_addresses()
            return response.get('Addresses', [])
            
        except Exception as e:
            logger.error(f"Error fetching Elastic IPs: {str(e)}")
            raise
    
    def _is_address_unused(self, address):
        """
        Check if an Elastic IP is unused (not associated with any resource)
        
        Args:
            address (dict): Elastic IP address details
            
        Returns:
            bool: True if address is unused
        """
        # Check if EIP is associated with an instance or network interface
        instance_id = address.get('InstanceId')
        association_id = address.get('AssociationId')
        network_interface_id = address.get('NetworkInterfaceId')
        
        # If no association exists, the EIP is unused
        if not instance_id and not association_id and not network_interface_id:
            return True
        
        return False
    
    def _add_unused_address(self, address):
        """
        Add unused Elastic IP to findings
        
        Args:
            address (dict): Elastic IP address details
        """
        public_ip = address.get('PublicIp', 'N/A')
        allocation_id = address.get('AllocationId', 'N/A')
        region = self.client.meta.region_name
        domain = address.get('Domain', 'vpc')
        
        # Calculate cost - unused EIPs are charged ~$0.005/hour = ~$3.60/month
        monthly_cost = self.cost_calculator.calculate_eip_cost(region)
        
        # Get tags
        tags = self.get_resource_tags(address.get('Tags', []))
        eip_name = tags.get('Name', 'N/A')
        
        resource_data = {
            'public_ip': public_ip,
            'allocation_id': allocation_id,
            'eip_name': eip_name,
            'domain': domain,
            'region': region,
            'monthly_cost': monthly_cost,
            'tags': tags,
            'recommendation': f'Consider releasing this unused Elastic IP to save ${monthly_cost:.2f}/month'
        }
        
        self.add_finding(resource_data)
        logger.info(f"Found unused Elastic IP: {public_ip} ({eip_name}) - ${monthly_cost:.2f}/month")

"""
EBS Analyzer
Analyzes EBS volumes to identify unattached resources
"""

import logging
from datetime import datetime, timedelta
from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class EBSAnalyzer(BaseAnalyzer):
    """Analyzes EBS volumes for unattached resources"""
    
    def __init__(self, ec2_client, config):
        """
        Initialize EBS Analyzer
        
        Args:
            ec2_client: Boto3 EC2 client
            config (dict): Application configuration
        """
        super().__init__(ec2_client, config)
        
        # Get configuration parameters
        ebs_config = config.get('ebs', {})
        self.unattached_days_threshold = ebs_config.get('unattached_days_threshold', 7)
        self.include_delete_on_termination = ebs_config.get('include_delete_on_termination', False)
    
    def analyze(self):
        """
        Analyze EBS volumes for unattached resources
        
        Returns:
            dict: Analysis results with unattached volumes
        """
        logger.info("Starting EBS volume analysis")
        
        try:
            # Get all volumes
            volumes = self._get_all_volumes()
            logger.info(f"Found {len(volumes)} EBS volumes")
            
            # Analyze each volume
            for volume in volumes:
                if self._is_volume_unattached(volume):
                    self._add_unattached_volume(volume)
            
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error analyzing EBS volumes: {str(e)}")
            raise
    
    def _get_all_volumes(self):
        """
        Get all EBS volumes
        
        Returns:
            list: List of EBS volumes
        """
        try:
            response = self.client.describe_volumes()
            return response['Volumes']
            
        except Exception as e:
            logger.error(f"Error fetching EBS volumes: {str(e)}")
            raise
    
    def _is_volume_unattached(self, volume):
        """
        Check if a volume is unattached
        
        Args:
            volume (dict): EBS volume details
            
        Returns:
            bool: True if volume is unattached and meets criteria
        """
        # Check if volume has any attachments
        if volume['Attachments']:
            return False
        
        # Check how long the volume has been unattached
        create_time = volume['CreateTime']
        days_unattached = (datetime.now(create_time.tzinfo) - create_time).days
        
        if days_unattached < self.unattached_days_threshold:
            logger.debug(f"Volume {volume['VolumeId']} unattached for {days_unattached} days (below threshold)")
            return False
        
        # Check DeleteOnTermination tag if configured
        if not self.include_delete_on_termination:
            tags = self.get_resource_tags(volume.get('Tags', []))
            if tags.get('DeleteOnTermination', '').lower() == 'true':
                logger.debug(f"Volume {volume['VolumeId']} has DeleteOnTermination=true")
                return False
        
        return True
    
    def _add_unattached_volume(self, volume):
        """
        Add unattached volume to findings
        
        Args:
            volume (dict): EBS volume details
        """
        volume_id = volume['VolumeId']
        volume_type = volume['VolumeType']
        volume_size = volume['Size']
        region = self.client.meta.region_name
        
        # Calculate cost
        monthly_cost = self.cost_calculator.calculate_ebs_cost(
            volume_type,
            volume_size,
            region
        )
        
        # Get volume name from tags
        tags = self.get_resource_tags(volume.get('Tags', []))
        volume_name = tags.get('Name', 'N/A')
        
        # Calculate days unattached
        create_time = volume['CreateTime']
        days_unattached = (datetime.now(create_time.tzinfo) - create_time).days
        
        resource_data = {
            'volume_id': volume_id,
            'volume_name': volume_name,
            'volume_type': volume_type,
            'size_gb': volume_size,
            'region': region,
            'state': volume['State'],
            'create_time': create_time.isoformat(),
            'days_unattached': days_unattached,
            'monthly_cost': monthly_cost,
            'tags': tags,
            'recommendation': f'Consider deleting this unattached volume to save ${monthly_cost:.2f}/month'
        }
        
        self.add_finding(resource_data)
        logger.info(f"Found unattached volume: {volume_id} ({volume_name}) - {volume_size}GB - ${monthly_cost:.2f}/month")

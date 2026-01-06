"""
Snapshot Analyzer
Analyzes EBS snapshots to identify outdated resources
"""

import logging
from datetime import datetime, timedelta
from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class SnapshotAnalyzer(BaseAnalyzer):
    """Analyzes EBS snapshots for outdated resources"""
    
    def __init__(self, ec2_client, config):
        """
        Initialize Snapshot Analyzer
        
        Args:
            ec2_client: Boto3 EC2 client
            config (dict): Application configuration
        """
        super().__init__(ec2_client, config)
        
        # Get configuration parameters
        snapshot_config = config.get('snapshots', {})
        self.retention_days = snapshot_config.get('retention_days', 90)
        self.exclude_ami_snapshots = snapshot_config.get('exclude_ami_snapshots', True)
    
    def analyze(self):
        """
        Analyze EBS snapshots for outdated resources
        
        Returns:
            dict: Analysis results with outdated snapshots
        """
        logger.info("Starting EBS snapshot analysis")
        
        try:
            # Get all snapshots owned by account
            snapshots = self._get_account_snapshots()
            logger.info(f"Found {len(snapshots)} EBS snapshots")
            
            # Get AMI snapshots if we need to exclude them
            ami_snapshot_ids = set()
            if self.exclude_ami_snapshots:
                ami_snapshot_ids = self._get_ami_snapshot_ids()
                logger.info(f"Found {len(ami_snapshot_ids)} snapshots associated with AMIs")
            
            # Analyze each snapshot
            for snapshot in snapshots:
                if self._is_snapshot_outdated(snapshot, ami_snapshot_ids):
                    self._add_outdated_snapshot(snapshot)
            
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error analyzing EBS snapshots: {str(e)}")
            raise
    
    def _get_account_snapshots(self):
        """
        Get all EBS snapshots owned by the account
        
        Returns:
            list: List of EBS snapshots
        """
        try:
            response = self.client.describe_snapshots(OwnerIds=['self'])
            return response['Snapshots']
            
        except Exception as e:
            logger.error(f"Error fetching EBS snapshots: {str(e)}")
            raise
    
    def _get_ami_snapshot_ids(self):
        """
        Get snapshot IDs associated with AMIs
        
        Returns:
            set: Set of snapshot IDs used by AMIs
        """
        try:
            response = self.client.describe_images(Owners=['self'])
            snapshot_ids = set()
            
            for image in response['Images']:
                for block_device in image.get('BlockDeviceMappings', []):
                    if 'Ebs' in block_device and 'SnapshotId' in block_device['Ebs']:
                        snapshot_ids.add(block_device['Ebs']['SnapshotId'])
            
            return snapshot_ids
            
        except Exception as e:
            logger.error(f"Error fetching AMI information: {str(e)}")
            return set()
    
    def _is_snapshot_outdated(self, snapshot, ami_snapshot_ids):
        """
        Check if a snapshot is outdated
        
        Args:
            snapshot (dict): EBS snapshot details
            ami_snapshot_ids (set): Set of snapshot IDs used by AMIs
            
        Returns:
            bool: True if snapshot is outdated
        """
        snapshot_id = snapshot['SnapshotId']
        
        # Exclude AMI snapshots if configured
        if self.exclude_ami_snapshots and snapshot_id in ami_snapshot_ids:
            logger.debug(f"Snapshot {snapshot_id} is associated with an AMI")
            return False
        
        # Check snapshot age
        start_time = snapshot['StartTime']
        snapshot_age_days = (datetime.now(start_time.tzinfo) - start_time).days
        
        if snapshot_age_days < self.retention_days:
            logger.debug(f"Snapshot {snapshot_id} is {snapshot_age_days} days old (below threshold)")
            return False
        
        return True
    
    def _add_outdated_snapshot(self, snapshot):
        """
        Add outdated snapshot to findings
        
        Args:
            snapshot (dict): EBS snapshot details
        """
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId', 'N/A')
        volume_size = snapshot['VolumeSize']
        region = self.client.meta.region_name
        
        # Calculate cost
        monthly_cost = self.cost_calculator.calculate_snapshot_cost(
            volume_size,
            region
        )
        
        # Get snapshot description and tags
        description = snapshot.get('Description', 'N/A')
        tags = self.get_resource_tags(snapshot.get('Tags', []))
        snapshot_name = tags.get('Name', description)
        
        # Calculate snapshot age
        start_time = snapshot['StartTime']
        snapshot_age_days = (datetime.now(start_time.tzinfo) - start_time).days
        
        resource_data = {
            'snapshot_id': snapshot_id,
            'snapshot_name': snapshot_name,
            'description': description,
            'volume_id': volume_id,
            'size_gb': volume_size,
            'region': region,
            'state': snapshot['State'],
            'start_time': start_time.isoformat(),
            'age_days': snapshot_age_days,
            'monthly_cost': monthly_cost,
            'tags': tags,
            'recommendation': f'Consider deleting this {snapshot_age_days}-day-old snapshot to save ${monthly_cost:.2f}/month'
        }
        
        self.add_finding(resource_data)
        logger.info(f"Found outdated snapshot: {snapshot_id} ({snapshot_name}) - {volume_size}GB - {snapshot_age_days} days old - ${monthly_cost:.2f}/month")

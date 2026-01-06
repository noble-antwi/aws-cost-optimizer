"""
EC2 Analyzer
Analyzes EC2 instances to identify idle resources
"""

import logging
from datetime import datetime, timedelta
from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class EC2Analyzer(BaseAnalyzer):
    """Analyzes EC2 instances for idle resources"""
    
    def __init__(self, ec2_client, cloudwatch_client, config):
        """
        Initialize EC2 Analyzer
        
        Args:
            ec2_client: Boto3 EC2 client
            cloudwatch_client: Boto3 CloudWatch client
            config (dict): Application configuration
        """
        super().__init__(ec2_client, config)
        self.cloudwatch = cloudwatch_client
        
        # Get configuration parameters
        ec2_config = config.get('ec2', {})
        self.cpu_threshold = ec2_config.get('cpu_threshold', 5.0)
        self.analysis_period_days = ec2_config.get('analysis_period_days', 7)
        self.metric_period_minutes = ec2_config.get('metric_period_minutes', 60)
        self.minimum_uptime_hours = ec2_config.get('minimum_uptime_hours', 24)
    
    def analyze(self):
        """
        Analyze EC2 instances for idle resources
        
        Returns:
            dict: Analysis results with idle instances
        """
        logger.info("Starting EC2 instance analysis")
        
        try:
            # Get all running instances
            instances = self._get_running_instances()
            logger.info(f"Found {len(instances)} running EC2 instances")
            
            # Analyze each instance
            for instance in instances:
                if self._is_instance_idle(instance):
                    self._add_idle_instance(instance)
            
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error analyzing EC2 instances: {str(e)}")
            raise
    
    def _get_running_instances(self):
        """
        Get all running EC2 instances
        
        Returns:
            list: List of running EC2 instances
        """
        try:
            response = self.client.describe_instances(
                Filters=[
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            instances = []
            for reservation in response['Reservations']:
                instances.extend(reservation['Instances'])
            
            return instances
            
        except Exception as e:
            logger.error(f"Error fetching EC2 instances: {str(e)}")
            raise
    
    def _is_instance_idle(self, instance):
        """
        Check if an instance is idle based on CPU utilization
        
        Args:
            instance (dict): EC2 instance details
            
        Returns:
            bool: True if instance is idle
        """
        instance_id = instance['InstanceId']
        
        # Check if instance has been running long enough
        launch_time = instance['LaunchTime']
        uptime_hours = (datetime.now(launch_time.tzinfo) - launch_time).total_seconds() / 3600
        
        if uptime_hours < self.minimum_uptime_hours:
            logger.debug(f"Instance {instance_id} uptime ({uptime_hours:.1f}h) below minimum")
            return False
        
        # Get CPU utilization metrics
        avg_cpu = self._get_average_cpu_utilization(instance_id)
        
        if avg_cpu is None:
            logger.warning(f"Could not get CPU metrics for {instance_id}")
            return False
        
        logger.debug(f"Instance {instance_id} average CPU: {avg_cpu:.2f}%")
        
        return avg_cpu < self.cpu_threshold
    
    def _get_average_cpu_utilization(self, instance_id):
        """
        Get average CPU utilization for an instance
        
        Args:
            instance_id (str): EC2 instance ID
            
        Returns:
            float: Average CPU utilization percentage
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.analysis_period_days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'InstanceId', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=self.metric_period_minutes * 60,
                Statistics=['Average']
            )
            
            if not response['Datapoints']:
                return None
            
            # Calculate average across all datapoints
            datapoints = response['Datapoints']
            avg_cpu = sum(dp['Average'] for dp in datapoints) / len(datapoints)
            
            return avg_cpu
            
        except Exception as e:
            logger.error(f"Error getting CloudWatch metrics for {instance_id}: {str(e)}")
            return None
    
    def _add_idle_instance(self, instance):
        """
        Add idle instance to findings
        
        Args:
            instance (dict): EC2 instance details
        """
        instance_id = instance['InstanceId']
        instance_type = instance['InstanceType']
        region = self.client.meta.region_name
        
        # Calculate cost
        monthly_cost = self.cost_calculator.calculate_ec2_cost(
            instance_type,
            region
        )
        
        # Get instance name from tags
        tags = self.get_resource_tags(instance.get('Tags', []))
        instance_name = tags.get('Name', 'N/A')
        
        resource_data = {
            'instance_id': instance_id,
            'instance_name': instance_name,
            'instance_type': instance_type,
            'region': region,
            'launch_time': instance['LaunchTime'].isoformat(),
            'state': instance['State']['Name'],
            'monthly_cost': monthly_cost,
            'tags': tags,
            'recommendation': f'Consider stopping or terminating this idle instance to save ${monthly_cost:.2f}/month'
        }
        
        self.add_finding(resource_data)
        logger.info(f"Found idle instance: {instance_id} ({instance_name}) - ${monthly_cost:.2f}/month")

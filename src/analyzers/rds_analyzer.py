"""
RDS Analyzer
Analyzes RDS instances to identify idle/underutilized databases
"""

import logging
from datetime import datetime, timedelta
from analyzers.base_analyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class RDSAnalyzer(BaseAnalyzer):
    """Analyzes RDS instances for idle/underutilized databases"""
    
    def __init__(self, rds_client, cloudwatch_client, config):
        """
        Initialize RDS Analyzer
        
        Args:
            rds_client: Boto3 RDS client
            cloudwatch_client: Boto3 CloudWatch client
            config (dict): Application configuration
        """
        super().__init__(rds_client, config)
        self.cloudwatch = cloudwatch_client
        
        # Get configuration parameters
        rds_config = config.get('rds', {})
        self.cpu_threshold = rds_config.get('cpu_threshold', 5.0)
        self.connections_threshold = rds_config.get('connections_threshold', 1)
        self.analysis_period_days = rds_config.get('analysis_period_days', 7)
        self.minimum_uptime_hours = rds_config.get('minimum_uptime_hours', 24)
    
    def analyze(self):
        """
        Analyze RDS instances for idle/underutilized databases
        
        Returns:
            dict: Analysis results with idle RDS instances
        """
        logger.info("Starting RDS instance analysis")
        
        try:
            # Get all RDS instances
            instances = self._get_all_instances()
            logger.info(f"Found {len(instances)} RDS instances")
            
            # Analyze each instance
            for instance in instances:
                if self._is_instance_idle(instance):
                    self._add_idle_instance(instance)
            
            return self.get_results()
            
        except Exception as e:
            logger.error(f"Error analyzing RDS instances: {str(e)}")
            raise
    
    def _get_all_instances(self):
        """
        Get all RDS instances
        
        Returns:
            list: List of RDS instances
        """
        try:
            instances = []
            paginator = self.client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                instances.extend(page.get('DBInstances', []))
            
            return instances
            
        except Exception as e:
            logger.error(f"Error fetching RDS instances: {str(e)}")
            raise
    
    def _is_instance_idle(self, instance):
        """
        Check if an RDS instance is idle based on CPU and connections
        
        Args:
            instance (dict): RDS instance details
            
        Returns:
            bool: True if instance is idle
        """
        db_instance_id = instance['DBInstanceIdentifier']
        instance_status = instance.get('DBInstanceStatus', '')
        
        # Only analyze running instances
        if instance_status != 'available':
            logger.debug(f"RDS {db_instance_id} is not available (status: {instance_status})")
            return False
        
        # Check minimum uptime
        launch_time = instance.get('InstanceCreateTime')
        if launch_time:
            uptime_hours = (datetime.now(launch_time.tzinfo) - launch_time).total_seconds() / 3600
            if uptime_hours < self.minimum_uptime_hours:
                logger.debug(f"RDS {db_instance_id} has been running for only {uptime_hours:.1f} hours")
                return False
        
        # Check CPU utilization
        avg_cpu = self._get_average_cpu(db_instance_id)
        if avg_cpu is None:
            logger.debug(f"No CPU metrics available for RDS {db_instance_id}")
            return False
        
        if avg_cpu >= self.cpu_threshold:
            logger.debug(f"RDS {db_instance_id} CPU is {avg_cpu:.2f}% (above threshold)")
            return False
        
        # Check database connections
        avg_connections = self._get_average_connections(db_instance_id)
        if avg_connections is not None and avg_connections > self.connections_threshold:
            logger.debug(f"RDS {db_instance_id} has {avg_connections:.1f} avg connections")
            return False
        
        logger.info(f"RDS {db_instance_id} appears idle: CPU={avg_cpu:.2f}%, Connections={avg_connections}")
        return True
    
    def _get_average_cpu(self, db_instance_id):
        """
        Get average CPU utilization for an RDS instance
        
        Args:
            db_instance_id (str): RDS instance identifier
            
        Returns:
            float: Average CPU utilization percentage
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.analysis_period_days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='CPUUtilization',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if not datapoints:
                return None
            
            return sum(dp['Average'] for dp in datapoints) / len(datapoints)
            
        except Exception as e:
            logger.error(f"Error getting CPU metrics for RDS {db_instance_id}: {str(e)}")
            return None
    
    def _get_average_connections(self, db_instance_id):
        """
        Get average database connections for an RDS instance
        
        Args:
            db_instance_id (str): RDS instance identifier
            
        Returns:
            float: Average number of database connections
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=self.analysis_period_days)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='DatabaseConnections',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': db_instance_id
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,  # 1 hour
                Statistics=['Average']
            )
            
            datapoints = response.get('Datapoints', [])
            if not datapoints:
                return None
            
            return sum(dp['Average'] for dp in datapoints) / len(datapoints)
            
        except Exception as e:
            logger.error(f"Error getting connection metrics for RDS {db_instance_id}: {str(e)}")
            return None
    
    def _add_idle_instance(self, instance):
        """
        Add idle RDS instance to findings
        
        Args:
            instance (dict): RDS instance details
        """
        db_instance_id = instance['DBInstanceIdentifier']
        instance_class = instance['DBInstanceClass']
        engine = instance.get('Engine', 'N/A')
        engine_version = instance.get('EngineVersion', 'N/A')
        region = self.client.meta.region_name
        multi_az = instance.get('MultiAZ', False)
        storage_type = instance.get('StorageType', 'gp2')
        allocated_storage = instance.get('AllocatedStorage', 0)
        
        # Get CPU and connections for reporting
        avg_cpu = self._get_average_cpu(db_instance_id) or 0.0
        avg_connections = self._get_average_connections(db_instance_id) or 0.0
        
        # Calculate cost
        monthly_cost = self.cost_calculator.calculate_rds_cost(
            instance_class,
            engine,
            region,
            multi_az,
            storage_type,
            allocated_storage
        )
        
        # Get instance name from tags
        tags_list = instance.get('TagList', [])
        tags = self.get_resource_tags(tags_list)
        instance_name = tags.get('Name', db_instance_id)
        
        # Get launch time
        launch_time = instance.get('InstanceCreateTime')
        launch_time_str = launch_time.isoformat() if launch_time else 'N/A'
        
        resource_data = {
            'db_instance_id': db_instance_id,
            'instance_name': instance_name,
            'instance_class': instance_class,
            'engine': f"{engine} {engine_version}",
            'region': region,
            'multi_az': multi_az,
            'storage_type': storage_type,
            'allocated_storage_gb': allocated_storage,
            'status': instance.get('DBInstanceStatus', 'N/A'),
            'launch_time': launch_time_str,
            'avg_cpu_percent': round(avg_cpu, 2),
            'avg_connections': round(avg_connections, 2),
            'monthly_cost': monthly_cost,
            'tags': tags,
            'recommendation': f'Consider stopping or downsizing this idle RDS instance to save ${monthly_cost:.2f}/month'
        }
        
        self.add_finding(resource_data)
        logger.info(f"Found idle RDS instance: {db_instance_id} ({instance_class}) - CPU={avg_cpu:.2f}%, ${monthly_cost:.2f}/month")

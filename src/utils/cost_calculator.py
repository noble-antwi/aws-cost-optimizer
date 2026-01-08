"""
Cost Calculator
Handles AWS cost estimation and calculations
"""

import logging
from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class CostCalculator:
    """Calculates AWS resource costs and potential savings"""
    
    def __init__(self, config, pricing_config=None):
        """
        Initialize Cost Calculator
        
        Args:
            config (dict): Application configuration
            pricing_config (dict): Pricing configuration (optional)
        """
        self.config = config
        
        if pricing_config is None:
            config_loader = ConfigLoader()
            pricing_path = config.get('pricing', {}).get('pricing_file', 'config/pricing.yaml')
            self.pricing = config_loader.load_pricing(pricing_path)
        else:
            self.pricing = pricing_config
        
        self.hours_per_month = self.pricing.get('hours_per_month', 730)
    
    def get_region_pricing(self, region, resource_type):
        """
        Get pricing data for a specific region and resource type
        
        Args:
            region (str): AWS region
            resource_type (str): Resource type (ec2, ebs, snapshots)
            
        Returns:
            dict: Pricing data for the region and resource type
        """
        regions = self.pricing.get('regions', {})
        
        # Try to get region-specific pricing
        if region in regions:
            return regions[region].get(resource_type, {})
        
        # Fall back to default pricing
        default_pricing = regions.get('default', {})
        logger.debug(f"Using default pricing for {region}")
        return default_pricing.get(resource_type, {})
    
    def calculate_ec2_cost(self, instance_type, region, running_hours=None):
        """
        Calculate EC2 instance cost
        
        Args:
            instance_type (str): EC2 instance type
            region (str): AWS region
            running_hours (float): Hours running per month (default: full month)
            
        Returns:
            float: Monthly cost in USD
        """
        pricing = self.get_region_pricing(region, 'ec2')
        
        if running_hours is None:
            running_hours = self.hours_per_month
        
        hourly_rate = pricing.get(instance_type, 0.0)
        
        if hourly_rate == 0.0:
            # Try to estimate based on similar instance types
            hourly_rate = self._estimate_instance_cost(instance_type, pricing)
        
        monthly_cost = hourly_rate * running_hours
        logger.debug(f"EC2 cost for {instance_type} in {region}: ${monthly_cost:.2f}/month")
        
        return monthly_cost
    
    def calculate_ebs_cost(self, volume_type, volume_size_gb, region):
        """
        Calculate EBS volume cost
        
        Args:
            volume_type (str): EBS volume type (gp3, gp2, io1, etc.)
            volume_size_gb (int): Volume size in GB
            region (str): AWS region
            
        Returns:
            float: Monthly cost in USD
        """
        pricing = self.get_region_pricing(region, 'ebs')
        price_per_gb = pricing.get(volume_type, pricing.get('gp3', 0.08))
        monthly_cost = price_per_gb * volume_size_gb
        
        logger.debug(f"EBS cost for {volume_size_gb}GB {volume_type} in {region}: ${monthly_cost:.2f}/month")
        
        return monthly_cost
    
    def calculate_snapshot_cost(self, snapshot_size_gb, region):
        """
        Calculate EBS snapshot cost
        
        Args:
            snapshot_size_gb (int): Snapshot size in GB
            region (str): AWS region
            
        Returns:
            float: Monthly cost in USD
        """
        pricing = self.get_region_pricing(region, 'snapshots')
        price_per_gb = pricing.get('standard', 0.05)
        monthly_cost = price_per_gb * snapshot_size_gb
        
        logger.debug(f"Snapshot cost for {snapshot_size_gb}GB in {region}: ${monthly_cost:.2f}/month")
        
        return monthly_cost
    
    def calculate_eip_cost(self, region):
        """
        Calculate Elastic IP cost (charged when not associated)
        
        Args:
            region (str): AWS region
            
        Returns:
            float: Monthly cost in USD
        """
        pricing = self.get_region_pricing(region, 'elastic_ip')
        hourly_rate = pricing.get('unassociated', 0.005)  # ~$0.005/hour when not associated
        monthly_cost = hourly_rate * self.hours_per_month
        
        logger.debug(f"Elastic IP cost in {region}: ${monthly_cost:.2f}/month")
        
        return monthly_cost
    
    def calculate_rds_cost(self, instance_class, engine, region, multi_az=False, 
                           storage_type='gp2', allocated_storage=0):
        """
        Calculate RDS instance cost
        
        Args:
            instance_class (str): RDS instance class (e.g., db.t3.micro)
            engine (str): Database engine (mysql, postgres, etc.)
            region (str): AWS region
            multi_az (bool): Whether Multi-AZ is enabled
            storage_type (str): Storage type (gp2, gp3, io1)
            allocated_storage (int): Allocated storage in GB
            
        Returns:
            float: Monthly cost in USD
        """
        pricing = self.get_region_pricing(region, 'rds')
        
        # Get instance pricing
        instance_pricing = pricing.get('instances', {})
        hourly_rate = instance_pricing.get(instance_class, 0.0)
        
        if hourly_rate == 0.0:
            # Try to estimate based on similar instance types
            hourly_rate = self._estimate_rds_instance_cost(instance_class, instance_pricing)
        
        # Double the cost for Multi-AZ
        if multi_az:
            hourly_rate *= 2
        
        instance_monthly_cost = hourly_rate * self.hours_per_month
        
        # Calculate storage cost
        storage_pricing = pricing.get('storage', {})
        storage_price_per_gb = storage_pricing.get(storage_type, 0.115)  # Default gp2 price
        storage_monthly_cost = storage_price_per_gb * allocated_storage
        
        # Double storage cost for Multi-AZ
        if multi_az:
            storage_monthly_cost *= 2
        
        total_monthly_cost = instance_monthly_cost + storage_monthly_cost
        
        logger.debug(f"RDS cost for {instance_class} ({engine}) in {region}: ${total_monthly_cost:.2f}/month")
        
        return total_monthly_cost
    
    def _estimate_rds_instance_cost(self, instance_class, pricing):
        """
        Estimate RDS instance cost based on instance family
        
        Args:
            instance_class (str): RDS instance class
            pricing (dict): Pricing data
            
        Returns:
            float: Estimated hourly rate
        """
        # Extract instance family (e.g., 'db.t3' from 'db.t3.large')
        parts = instance_class.split('.')
        if len(parts) >= 2:
            family = f"{parts[0]}.{parts[1]}"
        else:
            family = instance_class
        
        # Look for similar instances in the same family
        for known_type, rate in pricing.items():
            if known_type.startswith(family):
                logger.warning(f"Using approximate pricing for {instance_class} based on {known_type}")
                return rate
        
        # Default fallback
        logger.warning(f"No pricing data found for {instance_class}, using default rate")
        return 0.017  # Default to db.t3.micro rate
    
    def _estimate_instance_cost(self, instance_type, pricing):
        """
        Estimate instance cost based on instance family
        
        Args:
            instance_type (str): EC2 instance type
            pricing (dict): Pricing data
            
        Returns:
            float: Estimated hourly rate
        """
        # Extract instance family (e.g., 't3' from 't3.large')
        family = instance_type.split('.')[0] if '.' in instance_type else instance_type
        
        # Look for similar instances in the same family
        for known_type, rate in pricing.items():
            if known_type.startswith(family):
                logger.warning(f"Using approximate pricing for {instance_type} based on {known_type}")
                return rate
        
        # Default fallback
        logger.warning(f"No pricing data found for {instance_type}, using default rate")
        return 0.05  # Default to $0.05/hour
    
    def calculate_total_savings(self, resources):
        """
        Calculate total potential savings from multiple resources
        
        Args:
            resources (list): List of resource dictionaries with 'savings' key
            
        Returns:
            dict: Summary of savings
        """
        total_monthly = sum(r.get('monthly_cost', 0.0) for r in resources)
        total_annual = total_monthly * 12
        
        return {
            'monthly_savings': total_monthly,
            'annual_savings': total_annual,
            'resource_count': len(resources)
        }
    
    def format_cost(self, cost):
        """
        Format cost for display
        
        Args:
            cost (float): Cost value
            
        Returns:
            str: Formatted cost string
        """
        return f"${cost:.2f}"

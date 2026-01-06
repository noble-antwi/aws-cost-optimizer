"""
Base Analyzer
Abstract base class for resource analyzers
"""

from abc import ABC, abstractmethod
import logging
from datetime import datetime
from utils.cost_calculator import CostCalculator

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """Abstract base class for AWS resource analyzers"""
    
    def __init__(self, client, config):
        """
        Initialize Base Analyzer
        
        Args:
            client: AWS service client
            config (dict): Application configuration
        """
        self.client = client
        self.config = config
        self.cost_calculator = CostCalculator(config)
        self.results = {
            'resources': [],
            'total_savings': 0.0,
            'analysis_date': datetime.now().isoformat()
        }
    
    @abstractmethod
    def analyze(self):
        """
        Perform analysis on AWS resources
        
        Returns:
            dict: Analysis results
        """
        pass
    
    def get_resource_tags(self, tags):
        """
        Convert AWS tags to dictionary format
        
        Args:
            tags (list): List of AWS tag dictionaries
            
        Returns:
            dict: Tags as key-value pairs
        """
        if not tags:
            return {}
        
        return {tag['Key']: tag['Value'] for tag in tags}
    
    def filter_by_tags(self, resource, exclude_tags=None):
        """
        Check if resource should be excluded based on tags
        
        Args:
            resource (dict): Resource with 'tags' key
            exclude_tags (dict): Tags that indicate exclusion
            
        Returns:
            bool: True if resource should be included
        """
        if not exclude_tags:
            return True
        
        resource_tags = resource.get('tags', {})
        
        for key, value in exclude_tags.items():
            if resource_tags.get(key) == value:
                logger.debug(f"Excluding resource with tag {key}={value}")
                return False
        
        return True
    
    def add_finding(self, resource_data):
        """
        Add a finding to results
        
        Args:
            resource_data (dict): Resource information including cost
        """
        self.results['resources'].append(resource_data)
        self.results['total_savings'] += resource_data.get('monthly_cost', 0.0)
    
    def get_results(self):
        """
        Get analysis results
        
        Returns:
            dict: Analysis results
        """
        logger.info(f"Analysis complete: {len(self.results['resources'])} resources found, "
                   f"${self.results['total_savings']:.2f} potential monthly savings")
        return self.results

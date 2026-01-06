"""
Configuration Loader
Handles loading and validating configuration files
"""

import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and validates configuration"""
    
    def __init__(self, config_path='config/config.yaml'):
        """
        Initialize Config Loader
        
        Args:
            config_path (str): Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
    
    def load(self):
        """
        Load configuration from YAML file
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                logger.info("Using default configuration")
                return self._get_default_config()
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from: {self.config_path}")
            return self.config
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def load_pricing(self, pricing_path='config/pricing.yaml'):
        """
        Load pricing configuration
        
        Args:
            pricing_path (str): Path to pricing configuration file
            
        Returns:
            dict: Pricing configuration dictionary
        """
        try:
            pricing_file = Path(pricing_path)
            
            if not pricing_file.exists():
                logger.warning(f"Pricing file not found: {pricing_file}")
                return self._get_default_pricing()
            
            with open(pricing_file, 'r') as f:
                pricing = yaml.safe_load(f)
            
            logger.info(f"Pricing data loaded from: {pricing_file}")
            return pricing
            
        except Exception as e:
            logger.error(f"Error loading pricing data: {str(e)}")
            return self._get_default_pricing()
    
    def _get_default_config(self):
        """
        Get default configuration
        
        Returns:
            dict: Default configuration
        """
        return {
            'aws': {
                'profile': '',
                'regions': ['us-east-1'],
                'analyze_all_regions': False
            },
            'ec2': {
                'cpu_threshold': 5.0,
                'analysis_period_days': 7,
                'metric_period_minutes': 60,
                'minimum_uptime_hours': 24
            },
            'ebs': {
                'unattached_days_threshold': 7,
                'include_delete_on_termination': False
            },
            'snapshots': {
                'retention_days': 90,
                'exclude_ami_snapshots': True
            },
            'reports': {
                'output_dir': 'reports',
                'formats': ['json', 'csv', 'html'],
                'include_details': True,
                'include_charts': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/cost-optimizer.log',
                'console': True
            },
            'dry_run': True
        }
    
    def _get_default_pricing(self):
        """
        Get default pricing data
        
        Returns:
            dict: Default pricing data
        """
        return {
            'regions': {
                'default': {
                    'ec2': {
                        't2.micro': 0.0116,
                        't2.small': 0.023,
                        't2.medium': 0.0464,
                        't3.micro': 0.0104,
                        't3.small': 0.0208,
                        't3.medium': 0.0416,
                        'm5.large': 0.096
                    },
                    'ebs': {
                        'gp3': 0.08,
                        'gp2': 0.10,
                        'io1': 0.125,
                        'st1': 0.045,
                        'sc1': 0.025
                    },
                    'snapshots': {
                        'standard': 0.05
                    }
                }
            },
            'hours_per_month': 730
        }
    
    def validate_config(self):
        """
        Validate configuration values
        
        Returns:
            bool: True if configuration is valid
        """
        if not self.config:
            logger.warning("No configuration loaded")
            return False
        
        # Validate required sections
        required_sections = ['aws', 'ec2', 'ebs', 'snapshots', 'reports']
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate threshold values
        if self.config['ec2']['cpu_threshold'] < 0 or self.config['ec2']['cpu_threshold'] > 100:
            logger.error("Invalid CPU threshold value (must be 0-100)")
            return False
        
        logger.info("Configuration validation passed")
        return True

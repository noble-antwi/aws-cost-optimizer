"""
AWS Client Manager
Handles AWS client initialization and session management
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages AWS client connections and sessions"""
    
    def __init__(self, profile=None, regions=None):
        """
        Initialize AWS Client Manager
        
        Args:
            profile (str): AWS profile name to use
            regions (list): List of AWS regions
        """
        self.profile = profile
        self.regions = regions or ['us-east-1']
        self.session = None
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize boto3 session"""
        try:
            if self.profile:
                self.session = boto3.Session(profile_name=self.profile)
                logger.info(f"Initialized AWS session with profile: {self.profile}")
            else:
                self.session = boto3.Session()
                logger.info("Initialized AWS session with default credentials")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize AWS session: {str(e)}")
            raise
    
    def get_client(self, service_name, region=None):
        """
        Get AWS service client
        
        Args:
            service_name (str): AWS service name (e.g., 'ec2', 'cloudwatch')
            region (str): AWS region (uses default if not specified)
            
        Returns:
            boto3.client: AWS service client
        """
        try:
            region = region or self.regions[0]
            client = self.session.client(service_name, region_name=region)
            logger.debug(f"Created {service_name} client for region {region}")
            return client
        except Exception as e:
            logger.error(f"Failed to create {service_name} client: {str(e)}")
            raise
    
    def get_resource(self, service_name, region=None):
        """
        Get AWS service resource
        
        Args:
            service_name (str): AWS service name (e.g., 'ec2', 's3')
            region (str): AWS region (uses default if not specified)
            
        Returns:
            boto3.resource: AWS service resource
        """
        try:
            region = region or self.regions[0]
            resource = self.session.resource(service_name, region_name=region)
            logger.debug(f"Created {service_name} resource for region {region}")
            return resource
        except Exception as e:
            logger.error(f"Failed to create {service_name} resource: {str(e)}")
            raise
    
    def get_all_regions(self):
        """
        Get all available AWS regions for EC2
        
        Returns:
            list: List of region names
        """
        try:
            ec2_client = self.get_client('ec2')
            response = ec2_client.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            logger.info(f"Found {len(regions)} available regions")
            return regions
        except ClientError as e:
            logger.error(f"Failed to get regions: {str(e)}")
            return self.regions
    
    def validate_credentials(self):
        """
        Validate AWS credentials
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            sts_client = self.get_client('sts')
            response = sts_client.get_caller_identity()
            logger.info(f"Credentials validated for account: {response['Account']}")
            return True
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False
    
    def get_account_id(self):
        """
        Get AWS account ID
        
        Returns:
            str: AWS account ID
        """
        try:
            sts_client = self.get_client('sts')
            response = sts_client.get_caller_identity()
            return response['Account']
        except Exception as e:
            logger.error(f"Failed to get account ID: {str(e)}")
            return None

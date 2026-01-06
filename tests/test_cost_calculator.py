"""
Test Cost Calculator
"""

import pytest
from utils.cost_calculator import CostCalculator


class TestCostCalculator:
    """Test cases for CostCalculator"""
    
    @pytest.fixture
    def config(self):
        """Sample configuration for testing"""
        return {
            'pricing': {
                'pricing_file': 'config/pricing.yaml'
            }
        }
    
    @pytest.fixture
    def pricing_config(self):
        """Sample pricing configuration for testing"""
        return {
            'regions': {
                'us-east-1': {
                    'ec2': {
                        't2.micro': 0.0116,
                        't3.small': 0.0208
                    },
                    'ebs': {
                        'gp3': 0.08,
                        'gp2': 0.10
                    },
                    'snapshots': {
                        'standard': 0.05
                    }
                },
                'default': {
                    'ec2': {
                        't2.micro': 0.0116
                    },
                    'ebs': {
                        'gp3': 0.08
                    },
                    'snapshots': {
                        'standard': 0.05
                    }
                }
            },
            'hours_per_month': 730
        }
    
    @pytest.fixture
    def calculator(self, config, pricing_config):
        """Create CostCalculator instance"""
        return CostCalculator(config, pricing_config)
    
    def test_calculate_ec2_cost_full_month(self, calculator):
        """Test EC2 cost calculation for full month"""
        cost = calculator.calculate_ec2_cost('t2.micro', 'us-east-1')
        expected = 0.0116 * 730  # hourly rate * hours per month
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_ec2_cost_partial_month(self, calculator):
        """Test EC2 cost calculation for partial month"""
        running_hours = 360
        cost = calculator.calculate_ec2_cost('t2.micro', 'us-east-1', running_hours)
        expected = 0.0116 * 360
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_ebs_cost(self, calculator):
        """Test EBS volume cost calculation"""
        volume_size = 100  # GB
        cost = calculator.calculate_ebs_cost('gp3', volume_size, 'us-east-1')
        expected = 0.08 * 100  # price per GB * size
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_snapshot_cost(self, calculator):
        """Test snapshot cost calculation"""
        snapshot_size = 50  # GB
        cost = calculator.calculate_snapshot_cost(snapshot_size, 'us-east-1')
        expected = 0.05 * 50  # price per GB * size
        assert cost == pytest.approx(expected, rel=0.01)
    
    def test_calculate_total_savings(self, calculator):
        """Test total savings calculation"""
        resources = [
            {'monthly_cost': 10.0},
            {'monthly_cost': 20.0},
            {'monthly_cost': 15.0}
        ]
        
        savings = calculator.calculate_total_savings(resources)
        
        assert savings['monthly_savings'] == 45.0
        assert savings['annual_savings'] == 540.0
        assert savings['resource_count'] == 3
    
    def test_format_cost(self, calculator):
        """Test cost formatting"""
        assert calculator.format_cost(123.456) == "$123.46"
        assert calculator.format_cost(0.5) == "$0.50"
        assert calculator.format_cost(1000) == "$1000.00"

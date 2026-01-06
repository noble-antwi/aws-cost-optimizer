#!/usr/bin/env python3
"""
AWS Cost Optimization Analysis Tool
Main entry point for the application
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from analyzers.ec2_analyzer import EC2Analyzer
from analyzers.ebs_analyzer import EBSAnalyzer
from analyzers.snapshot_analyzer import SnapshotAnalyzer
from utils.config_loader import ConfigLoader
from utils.aws_client import AWSClientManager
from reports.json_reporter import JSONReporter
from reports.csv_reporter import CSVReporter
from reports.html_reporter import HTMLReporter

console = Console()


def setup_logging(config):
    """Setup logging configuration"""
    log_level = getattr(logging, config.get('logging', {}).get('level', 'INFO'))
    log_file = config.get('logging', {}).get('file', 'logs/cost-optimizer.log')
    
    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler() if config.get('logging', {}).get('console', True) else logging.NullHandler()
        ]
    )


def print_summary(results):
    """Print summary of findings to console"""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]AWS Cost Optimization Analysis Report[/bold cyan]",
        border_style="cyan"
    ))
    
    console.print(f"\n[bold]Analysis Date:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create summary table
    table = Table(title="Findings Summary", show_header=True, header_style="bold magenta")
    table.add_column("Resource Type", style="cyan", width=30)
    table.add_column("Count", justify="right", style="yellow")
    table.add_column("Potential Monthly Savings", justify="right", style="green")
    
    total_savings = 0.0
    
    for resource_type, data in results.items():
        count = len(data.get('resources', []))
        savings = data.get('total_savings', 0.0)
        total_savings += savings
        
        table.add_row(
            resource_type.replace('_', ' ').title(),
            str(count),
            f"${savings:.2f}"
        )
    
    console.print("\n", table)
    
    # Print total savings
    console.print(f"\n[bold green]Total Potential Monthly Savings: ${total_savings:.2f}[/bold green]")
    console.print(f"[bold green]Total Potential Annual Savings: ${total_savings * 12:.2f}[/bold green]\n")


@click.command()
@click.option('--config', '-c', default='config/config.yaml', help='Path to configuration file')
@click.option('--profile', '-p', default=None, help='AWS profile to use')
@click.option('--region', '-r', default=None, help='AWS region to analyze')
@click.option('--all-regions', is_flag=True, help='Analyze all available regions')
@click.option('--resource-type', '-t', 
              type=click.Choice(['ec2', 'ebs', 'snapshots', 'all']), 
              default='all', 
              help='Type of resources to analyze')
@click.option('--dry-run', is_flag=True, help='Run in dry-run mode (no changes)')
@click.option('--output-format', '-o', 
              type=click.Choice(['json', 'csv', 'html', 'all']), 
              default='all',
              help='Output report format')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(config, profile, region, all_regions, resource_type, dry_run, output_format, verbose):
    """
    AWS Cost Optimization Analysis Tool
    
    Analyzes AWS resources to identify cost optimization opportunities.
    """
    try:
        # Load configuration
        config_loader = ConfigLoader(config)
        app_config = config_loader.load()
        
        # Override config with CLI arguments
        if profile:
            app_config['aws']['profile'] = profile
        if region:
            app_config['aws']['regions'] = [region]
        if all_regions:
            app_config['aws']['analyze_all_regions'] = True
        if dry_run:
            app_config['dry_run'] = True
        
        # Setup logging
        if verbose:
            app_config['logging']['level'] = 'DEBUG'
        setup_logging(app_config)
        
        logger = logging.getLogger(__name__)
        logger.info("Starting AWS Cost Optimization Analysis")
        
        # Initialize AWS client manager
        aws_manager = AWSClientManager(
            profile=app_config['aws'].get('profile'),
            regions=app_config['aws'].get('regions', [])
        )
        
        # Get regions to analyze
        if app_config['aws'].get('analyze_all_regions'):
            regions = aws_manager.get_all_regions()
        else:
            regions = app_config['aws'].get('regions', ['us-east-1'])
        
        console.print(f"\n[bold]Analyzing regions:[/bold] {', '.join(regions)}")
        console.print(f"[bold]Resource types:[/bold] {resource_type}\n")
        
        # Initialize analyzers
        all_results = {}
        
        for aws_region in regions:
            console.print(f"\n[bold cyan]Analyzing region: {aws_region}[/bold cyan]")
            
            ec2_client = aws_manager.get_client('ec2', aws_region)
            cloudwatch_client = aws_manager.get_client('cloudwatch', aws_region)
            
            region_results = {}
            
            # Run EC2 analysis
            if resource_type in ['ec2', 'all']:
                with console.status("[bold green]Analyzing EC2 instances..."):
                    ec2_analyzer = EC2Analyzer(ec2_client, cloudwatch_client, app_config)
                    region_results['idle_ec2_instances'] = ec2_analyzer.analyze()
                    console.print(f"✓ Found {len(region_results['idle_ec2_instances']['resources'])} idle EC2 instances")
            
            # Run EBS analysis
            if resource_type in ['ebs', 'all']:
                with console.status("[bold green]Analyzing EBS volumes..."):
                    ebs_analyzer = EBSAnalyzer(ec2_client, app_config)
                    region_results['unattached_ebs_volumes'] = ebs_analyzer.analyze()
                    console.print(f"✓ Found {len(region_results['unattached_ebs_volumes']['resources'])} unattached EBS volumes")
            
            # Run Snapshot analysis
            if resource_type in ['snapshots', 'all']:
                with console.status("[bold green]Analyzing EBS snapshots..."):
                    snapshot_analyzer = SnapshotAnalyzer(ec2_client, app_config)
                    region_results['outdated_snapshots'] = snapshot_analyzer.analyze()
                    console.print(f"✓ Found {len(region_results['outdated_snapshots']['resources'])} outdated snapshots")
            
            all_results[aws_region] = region_results
        
        # Print summary
        combined_results = {}
        for aws_region, region_results in all_results.items():
            for resource_type_key, data in region_results.items():
                if resource_type_key not in combined_results:
                    combined_results[resource_type_key] = {
                        'resources': [],
                        'total_savings': 0.0
                    }
                combined_results[resource_type_key]['resources'].extend(data['resources'])
                combined_results[resource_type_key]['total_savings'] += data['total_savings']
        
        print_summary(combined_results)
        
        # Generate reports
        output_dir = Path(app_config['reports']['output_dir'])
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        report_dir = output_dir / f"cost-optimization-{timestamp}"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"\n[bold]Generating reports in:[/bold] {report_dir}\n")
        
        formats = [output_format] if output_format != 'all' else app_config['reports'].get('formats', ['json', 'csv', 'html'])
        
        for fmt in formats:
            if fmt == 'json':
                reporter = JSONReporter(report_dir)
                reporter.generate(all_results)
                console.print(f"✓ JSON report generated")
            elif fmt == 'csv':
                reporter = CSVReporter(report_dir)
                reporter.generate(all_results)
                console.print(f"✓ CSV reports generated")
            elif fmt == 'html':
                reporter = HTMLReporter(report_dir)
                reporter.generate(all_results, combined_results)
                console.print(f"✓ HTML report generated")
        
        console.print(f"\n[bold green]Analysis complete![/bold green] 🎉\n")
        
        return 0
        
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")
        logger.error(f"Application error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

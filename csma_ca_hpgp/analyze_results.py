#!/usr/bin/env python3
"""
HPGP SLAC Simulation Results Analysis
Analyzes OMNET++ simulation results for SLAC delay measurements
Based on simulator_simpleAndQuick analysis methods
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import glob
import os
from pathlib import Path


class SlacResultsAnalyzer:
    def __init__(self, results_dir="results"):
        self.results_dir = Path(results_dir)
        self.scalar_data = None
        self.vector_data = None
        
    def load_results(self, config_pattern="*"):
        """Load scalar and vector results from OMNET++ output files"""
        scalar_files = list(self.results_dir.glob(f"slac-{config_pattern}*.sca"))
        vector_files = list(self.results_dir.glob(f"slac-{config_pattern}*.vec"))
        
        print(f"Found {len(scalar_files)} scalar files and {len(vector_files)} vector files")
        
        # Load scalar data
        self.scalar_data = self._load_scalar_files(scalar_files)
        
        # Load vector data  
        self.vector_data = self._load_vector_files(vector_files)
        
        return self.scalar_data, self.vector_data
    
    def _load_scalar_files(self, files):
        """Parse OMNET++ scalar (.sca) files"""
        all_data = []
        
        for file_path in files:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            run_data = {}
            current_run = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('run '):
                    # New run
                    parts = line.split()
                    current_run = parts[1]
                    run_data[current_run] = {}
                    
                elif line.startswith('param '):
                    # Parameter
                    parts = line.split(' ', 2)
                    param_name = parts[1]
                    param_value = parts[2]
                    if current_run:
                        run_data[current_run][param_name] = param_value
                        
                elif line.startswith('scalar '):
                    # Scalar result
                    parts = line.split(' ', 3)
                    module = parts[1]
                    scalar_name = parts[2]
                    scalar_value = float(parts[3])
                    if current_run:
                        key = f"{module}.{scalar_name}"
                        run_data[current_run][key] = scalar_value
            
            # Convert to DataFrame format
            for run_id, data in run_data.items():
                data['file'] = file_path.name
                data['run'] = run_id
                all_data.append(data)
        
        return pd.DataFrame(all_data)
    
    def _load_vector_files(self, files):
        """Parse OMNET++ vector (.vec) files"""
        # Simplified vector loading - would need more sophisticated parsing
        # for full vector data analysis
        return None
    
    def analyze_slac_delays(self):
        """Analyze SLAC completion delays by node count and configuration"""
        if self.scalar_data is None:
            raise ValueError("No scalar data loaded")
        
        # Extract SLAC completion times
        completion_cols = [col for col in self.scalar_data.columns 
                          if 'slacCompletionTime' in col]
        
        results = []
        for _, row in self.scalar_data.iterrows():
            config = self._extract_config_name(row.get('file', ''))
            num_nodes = self._extract_num_nodes(row)
            
            for col in completion_cols:
                if pd.notna(row[col]):
                    node_id = self._extract_node_id(col)
                    results.append({
                        'config': config,
                        'num_nodes': num_nodes,
                        'node_id': node_id,
                        'completion_time': row[col],
                        'success': 1 if row[col] > 0 else 0
                    })
        
        return pd.DataFrame(results)
    
    def analyze_retry_counts(self):
        """Analyze SLAC retry patterns"""
        if self.scalar_data is None:
            raise ValueError("No scalar data loaded")
        
        retry_cols = [col for col in self.scalar_data.columns 
                     if 'slacRetryCount' in col]
        
        results = []
        for _, row in self.scalar_data.iterrows():
            config = self._extract_config_name(row.get('file', ''))
            num_nodes = self._extract_num_nodes(row)
            
            for col in retry_cols:
                if pd.notna(row[col]):
                    node_id = self._extract_node_id(col)
                    results.append({
                        'config': config,
                        'num_nodes': num_nodes,
                        'node_id': node_id,
                        'retry_count': row[col]
                    })
        
        return pd.DataFrame(results)
    
    def _extract_config_name(self, filename):
        """Extract configuration name from filename"""
        parts = filename.split('-')
        if len(parts) >= 2:
            return parts[1]
        return 'unknown'
    
    def _extract_num_nodes(self, row):
        """Extract number of nodes from parameters"""
        for col in row.index:
            if 'numNodes' in col:
                return int(row[col])
        return 0
    
    def _extract_node_id(self, column_name):
        """Extract node ID from column name"""
        import re
        match = re.search(r'node\[(\d+)\]', column_name)
        if match:
            return int(match.group(1))
        return 0
    
    def plot_delay_vs_nodes(self, delay_data, save_path=None):
        """Plot SLAC delay vs number of nodes"""
        plt.figure(figsize=(12, 8))
        
        # Group by configuration and number of nodes
        summary = delay_data.groupby(['config', 'num_nodes']).agg({
            'completion_time': ['mean', 'std', 'count'],
            'success': 'mean'
        }).reset_index()
        
        summary.columns = ['config', 'num_nodes', 'mean_delay', 'std_delay', 
                          'count', 'success_rate']
        
        # Plot for each configuration
        configs = summary['config'].unique()
        colors = plt.cm.Set1(np.linspace(0, 1, len(configs)))
        
        for i, config in enumerate(configs):
            config_data = summary[summary['config'] == config]
            plt.errorbar(config_data['num_nodes'], config_data['mean_delay'],
                        yerr=config_data['std_delay'], 
                        label=f'{config} (success: {config_data["success_rate"].mean():.2f})',
                        color=colors[i], marker='o', linewidth=2, markersize=6)
        
        plt.xlabel('Number of Nodes')
        plt.ylabel('Mean SLAC Completion Time (s)')
        plt.title('SLAC Delay vs Network Size')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_retry_distribution(self, retry_data, save_path=None):
        """Plot distribution of retry counts"""
        plt.figure(figsize=(10, 6))
        
        # Create box plot by configuration
        sns.boxplot(data=retry_data, x='config', y='retry_count')
        plt.xticks(rotation=45)
        plt.ylabel('Retry Count')
        plt.title('SLAC Retry Count Distribution by Configuration')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_concurrent_impact(self, delay_data, save_path=None):
        """Plot impact of concurrent SLAC procedures"""
        plt.figure(figsize=(12, 6))
        
        # Compare single EVSE vs concurrent EVSE scenarios
        single_data = delay_data[delay_data['config'] == 'SingleEVSE']
        concurrent_data = delay_data[delay_data['config'] == 'ConcurrentEVSE']
        
        if len(single_data) > 0 and len(concurrent_data) > 0:
            single_summary = single_data.groupby('num_nodes')['completion_time'].mean()
            concurrent_summary = concurrent_data.groupby('num_nodes')['completion_time'].mean()
            
            plt.plot(single_summary.index, single_summary.values, 
                    'o-', label='Single EVSE', linewidth=2, markersize=6)
            plt.plot(concurrent_summary.index, concurrent_summary.values, 
                    's-', label='Concurrent EVSEs', linewidth=2, markersize=6)
            
            plt.xlabel('Number of Nodes')
            plt.ylabel('Mean SLAC Completion Time (s)')
            plt.title('Impact of Concurrent SLAC Procedures')
            plt.legend()
            plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, output_dir="analysis"):
        """Generate comprehensive analysis report"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Load and analyze data
        delay_data = self.analyze_slac_delays()
        retry_data = self.analyze_retry_counts()
        
        # Generate plots
        self.plot_delay_vs_nodes(delay_data, 
                               output_path / "slac_delay_vs_nodes.png")
        self.plot_retry_distribution(retry_data, 
                                   output_path / "retry_distribution.png")
        self.plot_concurrent_impact(delay_data, 
                                  output_path / "concurrent_impact.png")
        
        # Generate summary statistics
        summary_stats = self._generate_summary_stats(delay_data, retry_data)
        
        # Save summary to CSV
        summary_stats.to_csv(output_path / "summary_statistics.csv", index=False)
        
        print(f"Analysis complete. Results saved to {output_path}")
        return summary_stats
    
    def _generate_summary_stats(self, delay_data, retry_data):
        """Generate summary statistics"""
        summary = delay_data.groupby(['config', 'num_nodes']).agg({
            'completion_time': ['mean', 'std', 'min', 'max'],
            'success': ['mean', 'count']
        }).reset_index()
        
        summary.columns = ['config', 'num_nodes', 'mean_delay', 'std_delay',
                          'min_delay', 'max_delay', 'success_rate', 'total_nodes']
        
        # Add retry statistics
        retry_summary = retry_data.groupby(['config', 'num_nodes'])['retry_count'].mean().reset_index()
        retry_summary.columns = ['config', 'num_nodes', 'mean_retries']
        
        summary = summary.merge(retry_summary, on=['config', 'num_nodes'], how='left')
        
        return summary


def main():
    parser = argparse.ArgumentParser(description='Analyze HPGP SLAC simulation results')
    parser.add_argument('--results-dir', default='results', 
                       help='Directory containing simulation results')
    parser.add_argument('--config', default='*', 
                       help='Configuration pattern to analyze')
    parser.add_argument('--output-dir', default='analysis', 
                       help='Output directory for analysis results')
    
    args = parser.parse_args()
    
    # Create analyzer and load results
    analyzer = SlacResultsAnalyzer(args.results_dir)
    analyzer.load_results(args.config)
    
    # Generate comprehensive report
    summary = analyzer.generate_report(args.output_dir)
    
    print("\nSummary Statistics:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

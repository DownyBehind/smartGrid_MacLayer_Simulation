#!/usr/bin/env python3
"""
Real HPGP MAC Data Analysis Script
Analyzes actual 30-run, 120-second experiment data
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from scipy import stats
import glob

def parse_sca_file(sca_file_path):
    """Parse OMNeT++ scalar (.sca) file"""
    data = {}
    
    with open(sca_file_path, 'r') as f:
        lines = f.readlines()
    
    current_run = None
    current_node = None
    
    for line in lines:
        line = line.strip()
        
        # Parse run information
        if line.startswith('run '):
            current_run = line.split()[1]
            data[current_run] = {}
        
        # Parse iteration variables
        elif line.startswith('itervar nodeId '):
            current_node = int(line.split()[2])
            if 'nodes' not in data[current_run]:
                data[current_run]['nodes'] = {}
            data[current_run]['nodes'][current_node] = {}
        
        # Parse scalar values
        elif line.startswith('scalar '):
            parts = line.split()
            if len(parts) >= 3:
                metric = parts[1]
                value = float(parts[2])
                
                if current_run and current_node is not None:
                    if 'metrics' not in data[current_run]:
                        data[current_run]['metrics'] = {}
                    data[current_run]['metrics'][metric] = value
                    data[current_run]['nodes'][current_node][metric] = value
    
    return data

def parse_vector_file(vec_file_path):
    """Parse OMNeT++ vector (.vec) file"""
    data = {}
    
    with open(vec_file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        
        # Parse vector data
        if line.startswith('vector '):
            parts = line.split()
            if len(parts) >= 4:
                run_id = parts[1]
                metric = parts[2]
                values = [float(x) for x in parts[3:]]
                
                if run_id not in data:
                    data[run_id] = {}
                data[run_id][metric] = values
    
    return data

def load_real_experiment_data():
    """Load actual experiment data from .sca and .vec files"""
    
    # Find all .sca files
    sca_files = glob.glob("test/*/results/*.sca")
    vec_files = glob.glob("test/*/results/*.vec")
    
    print(f"Found {len(sca_files)} scalar files and {len(vec_files)} vector files")
    
    all_data = {}
    
    for sca_file in sca_files:
        print(f"Parsing {sca_file}")
        sca_data = parse_sca_file(sca_file)
        all_data.update(sca_data)
    
    return all_data

def calculate_real_statistics(data):
    """Calculate statistics from real experiment data"""
    
    # Extract metrics from all runs
    metrics_data = {}
    
    for run_id, run_data in data.items():
        if 'metrics' in run_data:
            for metric, value in run_data['metrics'].items():
                if metric not in metrics_data:
                    metrics_data[metric] = []
                metrics_data[metric].append(value)
    
    # Calculate statistics
    stats_results = {}
    
    for metric, values in metrics_data.items():
        if len(values) > 0:
            stats_results[metric] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'min': np.min(values),
                'max': np.max(values),
                'p25': np.percentile(values, 25),
                'p50': np.percentile(values, 50),
                'p75': np.percentile(values, 75),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99),
                'count': len(values),
                'ci_95_low': np.mean(values) - 1.96 * np.std(values) / np.sqrt(len(values)),
                'ci_95_high': np.mean(values) + 1.96 * np.std(values) / np.sqrt(len(values))
            }
    
    return stats_results, metrics_data

def create_real_data_analysis(data, stats_results, metrics_data, output_dir):
    """Create analysis from real experiment data"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 1. Real Data Summary
    create_real_data_summary(stats_results, output_dir)
    
    # 2. Performance Distribution Analysis
    create_performance_distribution(metrics_data, output_dir)
    
    # 3. Run-by-Run Analysis
    create_run_by_run_analysis(data, output_dir)
    
    # 4. Statistical Significance Analysis
    create_statistical_analysis(metrics_data, output_dir)
    
    # 5. Comprehensive Dashboard
    create_comprehensive_dashboard(data, stats_results, metrics_data, output_dir)

def create_real_data_summary(stats_results, output_dir):
    """Create summary of real experiment data"""
    
    # Create summary DataFrame
    summary_data = []
    
    for metric, stats in stats_results.items():
        summary_data.append({
            'Metric': metric,
            'Mean': f"{stats['mean']:.4f}",
            'Std': f"{stats['std']:.4f}",
            'Min': f"{stats['min']:.4f}",
            'Max': f"{stats['max']:.4f}",
            'P95': f"{stats['p95']:.4f}",
            'P99': f"{stats['p99']:.4f}",
            'Count': stats['count'],
            'CI_95_Low': f"{stats['ci_95_low']:.4f}",
            'CI_95_High': f"{stats['ci_95_high']:.4f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_dir / 'real_data_summary.csv', index=False)
    
    print("✅ Real data summary created")
    print(f"Total metrics analyzed: {len(stats_results)}")
    print(f"Total runs: {stats_results[list(stats_results.keys())[0]]['count']}")

def create_performance_distribution(metrics_data, output_dir):
    """Create performance distribution analysis"""
    
    plt.figure(figsize=(15, 10))
    
    # Get key metrics
    key_metrics = ['dcCycle', 'slacAttempt', 'txAttempt', 'collision']
    available_metrics = [m for m in key_metrics if m in metrics_data]
    
    if not available_metrics:
        print("No key metrics found in data")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    axes = axes.flatten()
    
    for i, metric in enumerate(available_metrics[:4]):
        if i < len(axes):
            ax = axes[i]
            values = metrics_data[metric]
            
            # Create histogram
            ax.hist(values, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
            ax.axvline(np.mean(values), color='red', linestyle='--', 
                      label=f'Mean: {np.mean(values):.4f}')
            ax.axvline(np.percentile(values, 95), color='orange', linestyle='--', 
                      label=f'P95: {np.percentile(values, 95):.4f}')
            
            ax.set_title(f'{metric} Distribution (n={len(values)})')
            ax.set_xlabel(metric)
            ax.set_ylabel('Frequency')
            ax.legend()
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'real_performance_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Performance distribution analysis created")

def create_run_by_run_analysis(data, output_dir):
    """Create run-by-run analysis"""
    
    plt.figure(figsize=(15, 10))
    
    # Extract run numbers and key metrics
    runs = []
    dc_cycles = []
    slac_attempts = []
    tx_attempts = []
    collisions = []
    
    for run_id, run_data in data.items():
        if 'metrics' in run_data:
            run_num = int(run_id.split('-')[-1]) if '-' in run_id else 0
            runs.append(run_num)
            
            dc_cycles.append(run_data['metrics'].get('dcCycle', 0))
            slac_attempts.append(run_data['metrics'].get('slacAttempt', 0))
            tx_attempts.append(run_data['metrics'].get('txAttempt', 0))
            collisions.append(run_data['metrics'].get('collision', 0))
    
    # Sort by run number
    sorted_data = sorted(zip(runs, dc_cycles, slac_attempts, tx_attempts, collisions))
    runs, dc_cycles, slac_attempts, tx_attempts, collisions = zip(*sorted_data)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # DC Cycle over runs
    ax1.plot(runs, dc_cycles, 'o-', color='blue', linewidth=2, markersize=4)
    ax1.set_title('DC Cycle Over 30 Runs')
    ax1.set_xlabel('Run Number')
    ax1.set_ylabel('DC Cycle')
    ax1.grid(True, alpha=0.3)
    
    # SLAC Attempts over runs
    ax2.plot(runs, slac_attempts, 'o-', color='green', linewidth=2, markersize=4)
    ax2.set_title('SLAC Attempts Over 30 Runs')
    ax2.set_xlabel('Run Number')
    ax2.set_ylabel('SLAC Attempts')
    ax2.grid(True, alpha=0.3)
    
    # TX Attempts over runs
    ax3.plot(runs, tx_attempts, 'o-', color='red', linewidth=2, markersize=4)
    ax3.set_title('TX Attempts Over 30 Runs')
    ax3.set_xlabel('Run Number')
    ax3.set_ylabel('TX Attempts')
    ax3.grid(True, alpha=0.3)
    
    # Collisions over runs
    ax4.plot(runs, collisions, 'o-', color='orange', linewidth=2, markersize=4)
    ax4.set_title('Collisions Over 30 Runs')
    ax4.set_xlabel('Run Number')
    ax4.set_ylabel('Collisions')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'real_run_by_run_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Run-by-run analysis created")

def create_statistical_analysis(metrics_data, output_dir):
    """Create statistical analysis"""
    
    # Calculate correlation matrix
    metrics_df = pd.DataFrame(metrics_data)
    correlation_matrix = metrics_df.corr()
    
    # Create correlation heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                square=True, fmt='.3f')
    plt.title('Metrics Correlation Matrix (30 Runs)')
    plt.tight_layout()
    plt.savefig(output_dir / 'real_correlation_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Calculate coefficient of variation
    cv_data = []
    for metric, values in metrics_data.items():
        if len(values) > 1:
            cv = (np.std(values) / np.mean(values)) * 100
            cv_data.append({'Metric': metric, 'CV_%': cv})
    
    cv_df = pd.DataFrame(cv_data)
    cv_df.to_csv(output_dir / 'real_coefficient_of_variation.csv', index=False)
    
    print("✅ Statistical analysis created")

def create_comprehensive_dashboard(data, stats_results, metrics_data, output_dir):
    """Create comprehensive analysis dashboard"""
    
    plt.figure(figsize=(20, 12))
    
    # Create a 3x3 subplot layout
    fig, axes = plt.subplots(3, 3, figsize=(20, 12))
    
    # 1. DC Cycle Distribution (Top Left)
    ax1 = axes[0, 0]
    if 'dcCycle' in metrics_data:
        values = metrics_data['dcCycle']
        ax1.hist(values, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(values):.4f}')
        ax1.set_title('DC Cycle Distribution (30 Runs)')
        ax1.set_xlabel('DC Cycle')
        ax1.set_ylabel('Frequency')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
    
    # 2. SLAC Attempts Distribution (Top Center)
    ax2 = axes[0, 1]
    if 'slacAttempt' in metrics_data:
        values = metrics_data['slacAttempt']
        ax2.hist(values, bins=15, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.axvline(np.mean(values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(values):.4f}')
        ax2.set_title('SLAC Attempts Distribution (30 Runs)')
        ax2.set_xlabel('SLAC Attempts')
        ax2.set_ylabel('Frequency')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # 3. TX Attempts Distribution (Top Right)
    ax3 = axes[0, 2]
    if 'txAttempt' in metrics_data:
        values = metrics_data['txAttempt']
        ax3.hist(values, bins=15, alpha=0.7, color='lightcoral', edgecolor='black')
        ax3.axvline(np.mean(values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(values):.4f}')
        ax3.set_title('TX Attempts Distribution (30 Runs)')
        ax3.set_xlabel('TX Attempts')
        ax3.set_ylabel('Frequency')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
    
    # 4. Collision Distribution (Middle Left)
    ax4 = axes[1, 0]
    if 'collision' in metrics_data:
        values = metrics_data['collision']
        ax4.hist(values, bins=15, alpha=0.7, color='orange', edgecolor='black')
        ax4.axvline(np.mean(values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(values):.4f}')
        ax4.set_title('Collision Distribution (30 Runs)')
        ax4.set_xlabel('Collisions')
        ax4.set_ylabel('Frequency')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
    
    # 5. Run-by-Run DC Cycle (Middle Center)
    ax5 = axes[1, 1]
    if 'dcCycle' in metrics_data:
        runs = list(range(1, len(metrics_data['dcCycle']) + 1))
        ax5.plot(runs, metrics_data['dcCycle'], 'o-', color='blue', linewidth=2, markersize=4)
        ax5.set_title('DC Cycle Over 30 Runs')
        ax5.set_xlabel('Run Number')
        ax5.set_ylabel('DC Cycle')
        ax5.grid(True, alpha=0.3)
    
    # 6. Run-by-Run SLAC Attempts (Middle Right)
    ax6 = axes[1, 2]
    if 'slacAttempt' in metrics_data:
        runs = list(range(1, len(metrics_data['slacAttempt']) + 1))
        ax6.plot(runs, metrics_data['slacAttempt'], 'o-', color='green', linewidth=2, markersize=4)
        ax6.set_title('SLAC Attempts Over 30 Runs')
        ax6.set_xlabel('Run Number')
        ax6.set_ylabel('SLAC Attempts')
        ax6.grid(True, alpha=0.3)
    
    # 7. Statistics Summary Table (Bottom Left)
    ax7 = axes[2, 0]
    ax7.axis('off')
    
    summary_data = []
    for metric, stats in list(stats_results.items())[:5]:  # Show first 5 metrics
        summary_data.append([
            metric,
            f"{stats['mean']:.4f}",
            f"{stats['std']:.4f}",
            f"{stats['p95']:.4f}",
            f"{stats['count']}"
        ])
    
    table = ax7.table(cellText=summary_data,
                     colLabels=['Metric', 'Mean', 'Std', 'P95', 'Count'],
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    ax7.set_title('Key Statistics Summary', fontsize=14, pad=20)
    
    # 8. Coefficient of Variation (Bottom Center)
    ax8 = axes[2, 1]
    cv_data = []
    for metric, values in metrics_data.items():
        if len(values) > 1:
            cv = (np.std(values) / np.mean(values)) * 100
            cv_data.append(cv)
    
    if cv_data:
        ax8.bar(range(len(cv_data)), cv_data, color='purple', alpha=0.7)
        ax8.set_title('Coefficient of Variation (%)')
        ax8.set_xlabel('Metrics')
        ax8.set_ylabel('CV (%)')
        ax8.grid(True, alpha=0.3)
    
    # 9. Performance Trend (Bottom Right)
    ax9 = axes[2, 2]
    if 'dcCycle' in metrics_data and 'slacAttempt' in metrics_data:
        ax9.scatter(metrics_data['slacAttempt'], metrics_data['dcCycle'], 
                   alpha=0.7, color='red', s=50)
        ax9.set_title('DC Cycle vs SLAC Attempts')
        ax9.set_xlabel('SLAC Attempts')
        ax9.set_ylabel('DC Cycle')
        ax9.grid(True, alpha=0.3)
    
    plt.suptitle('Real HPGP MAC Analysis Dashboard (30 Runs, 120s each)', fontsize=16, y=0.98)
    plt.tight_layout()
    plt.savefig(output_dir / 'real_comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✅ Comprehensive dashboard created")

def main():
    """Main analysis function"""
    print("Starting Real HPGP MAC Data Analysis...")
    print("Analyzing actual 30-run, 120-second experiment data")
    
    # Load real experiment data
    data = load_real_experiment_data()
    
    if not data:
        print("No data found! Please check if .sca files exist.")
        return
    
    # Calculate statistics
    stats_results, metrics_data = calculate_real_statistics(data)
    
    # Create analysis
    create_real_data_analysis(data, stats_results, metrics_data, "real_analysis_results")
    
    print("\nReal data analysis complete!")
    print("Results saved to real_analysis_results/")
    print(f"Analyzed {len(data)} runs with {len(stats_results)} metrics")

if __name__ == "__main__":
    main()

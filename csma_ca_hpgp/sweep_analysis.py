#!/usr/bin/env python3
"""
HPGP SLAC Node Sweep Analysis
Replicates simulator_simpleAndQuick/scripts/sweep_nodes.py functionality for OMNET++
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless plotting
import matplotlib.pyplot as plt
import subprocess
import glob
from pathlib import Path
import argparse
import time

class HpgpSlacSweep:
    def __init__(self, exe_path="./csma_ca_hpgp", results_dir="results"):
        self.exe_path = exe_path
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def run_single_experiment(self, num_nodes, seed=0):
        """Run single OMNET++ simulation for given node count"""
        print(f"Running N={num_nodes}, seed={seed}...", end=" ")
        
        cmd = [
            self.exe_path,
            "-u", "Cmdenv",
            "-c", "NodeSweepSingle", 
            "-f", "node_sweep.ini",
            f"--seed-set={seed}",
            f"--*.numNodes={num_nodes}",
            f"--result-dir={self.results_dir}"
        ]
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                print(f"OK ({duration:.1f}s)")
                return True
            else:
                print(f"FAILED: {result.stderr[:100]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    def parse_omnetpp_results(self, num_nodes):
        """Parse OMNET++ scalar results for given node count"""
        # Find result files for this node count
        pattern = f"{self.results_dir}/NodeSweepSingle-N{num_nodes}-*.sca"
        sca_files = glob.glob(pattern)
        
        if not sca_files:
            return None
            
        metrics = {
            'nodes': num_nodes,
            'slac_completion_time_avg': 0,
            'slac_completion_time_max': 0,
            'slac_success_rate': 0,
            'slac_retry_avg': 0,
            'slac_timeout_rate': 0,
            'session_success': 0,
            'session_total': 0,
            'efficiency_eta': 0,
            'throughput_mbps': 0,
            'collision_ratio': 0,
            'utilization': 0
        }
        
        completion_times = []
        retry_counts = []
        timeouts = 0
        successes = 0
        total_sessions = 0
        
        for sca_file in sca_files:
            try:
                with open(sca_file, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('scalar ') and 'slacCompletionTime' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            completion_time = float(parts[3])
                            if completion_time > 0:  # Successful completion
                                completion_times.append(completion_time)
                                successes += 1
                            total_sessions += 1
                    
                    elif line.startswith('scalar ') and 'slacRetryCount' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            retry_counts.append(float(parts[3]))
                    
                    elif line.startswith('scalar ') and 'slacTimeout' in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            timeouts += float(parts[3])
                            
            except Exception as e:
                print(f"Error parsing {sca_file}: {e}")
        
        if completion_times:
            metrics['slac_completion_time_avg'] = np.mean(completion_times)
            metrics['slac_completion_time_max'] = np.max(completion_times)
        
        if retry_counts:
            metrics['slac_retry_avg'] = np.mean(retry_counts)
        
        if total_sessions > 0:
            metrics['slac_success_rate'] = successes / total_sessions
            metrics['slac_timeout_rate'] = timeouts / total_sessions
        
        metrics['session_success'] = successes
        metrics['session_total'] = total_sessions
        
        # Calculate efficiency (successful SLAC procedures / total time)
        if completion_times:
            total_time = 10.0  # 10s simulation time
            metrics['efficiency_eta'] = successes / (num_nodes - 1)  # EV success rate
            metrics['throughput_mbps'] = successes * 0.1  # Approximate throughput
        
        return metrics
    
    def run_node_sweep(self, node_range=None, seeds=None):
        """Run complete node sweep experiment"""
        if node_range is None:
            node_range = list(range(5, 101, 5))  # 5 to 100 in steps of 5
        
        if seeds is None:
            seeds = [0]  # Single seed for quick testing
        
        print(f"Starting node sweep: {len(node_range)} node counts × {len(seeds)} seeds")
        print("=" * 60)
        
        all_results = []
        
        for i, num_nodes in enumerate(node_range, 1):
            print(f"[{i}/{len(node_range)}] Testing N={num_nodes}")
            
            node_results = []
            for seed in seeds:
                if self.run_single_experiment(num_nodes, seed):
                    time.sleep(0.5)  # Brief pause between runs
            
            # Parse results for this node count
            metrics = self.parse_omnetpp_results(num_nodes)
            if metrics:
                all_results.append(metrics)
                print(f"    → SLAC success: {metrics['session_success']}/{metrics['session_total']} "
                      f"({metrics['slac_success_rate']:.2%}), "
                      f"avg_time: {metrics['slac_completion_time_avg']:.3f}s, "
                      f"retries: {metrics['slac_retry_avg']:.1f}")
            else:
                print(f"    → No results found for N={num_nodes}")
            
            print()
        
        return all_results
    
    def generate_analysis_plots(self, results, output_dir="analysis"):
        """Generate analysis plots like simulator_simpleAndQuick"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        if not results:
            print("No results to plot")
            return
        
        df = pd.DataFrame(results)
        
        # Plot 1: SLAC Success Rate vs Nodes
        plt.figure(figsize=(10, 6))
        plt.subplot(2, 2, 1)
        plt.plot(df['nodes'], df['slac_success_rate'], 'bo-', linewidth=2, markersize=6)
        plt.xlabel('Number of Nodes')
        plt.ylabel('SLAC Success Rate')
        plt.title('SLAC Success Rate vs Number of Nodes')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1.0)
        
        # Plot 2: Average Completion Time vs Nodes
        plt.subplot(2, 2, 2)
        plt.plot(df['nodes'], df['slac_completion_time_avg'], 'ro-', linewidth=2, markersize=6)
        plt.xlabel('Number of Nodes')
        plt.ylabel('Avg SLAC Completion Time (s)')
        plt.title('SLAC Completion Time vs Number of Nodes')
        plt.grid(True, alpha=0.3)
        
        # Plot 3: Retry Count vs Nodes
        plt.subplot(2, 2, 3)
        plt.plot(df['nodes'], df['slac_retry_avg'], 'go-', linewidth=2, markersize=6)
        plt.xlabel('Number of Nodes')
        plt.ylabel('Average Retry Count')
        plt.title('SLAC Retries vs Number of Nodes')
        plt.grid(True, alpha=0.3)
        
        # Plot 4: Efficiency vs Nodes (like simulator_simpleAndQuick)
        plt.subplot(2, 2, 4)
        plt.plot(df['nodes'], df['efficiency_eta'], 'mo-', linewidth=2, markersize=6)
        plt.xlabel('Number of Nodes')
        plt.ylabel('Efficiency (η)')
        plt.title('HPGP SLAC Efficiency vs Number of Nodes')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1.0)
        
        plt.tight_layout()
        plot_path = output_path / "slac_node_sweep_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Additional detailed plot for efficiency (matching simulator_simpleAndQuick style)
        plt.figure(figsize=(8, 5))
        plt.plot(df['nodes'], df['efficiency_eta'], 'o-', linewidth=2, markersize=8, 
                color='#1f77b4', markerfacecolor='white', markeredgewidth=2)
        plt.xlabel('Number of Nodes', fontsize=12)
        plt.ylabel('Efficiency (η)', fontsize=12)
        plt.title('HPGP SLAC Efficiency vs Number of Nodes\n(OMNET++ Simulation)', fontsize=14)
        plt.grid(True, alpha=0.3, linewidth=0.5)
        plt.ylim(0, 1.0)
        
        # Add annotations for key points
        max_efficiency_idx = df['efficiency_eta'].idxmax()
        max_eff_node = df.loc[max_efficiency_idx, 'nodes']
        max_eff_val = df.loc[max_efficiency_idx, 'efficiency_eta']
        
        plt.annotate(f'Peak: N={max_eff_node}, η={max_eff_val:.3f}',
                    xy=(max_eff_node, max_eff_val),
                    xytext=(max_eff_node + 15, max_eff_val + 0.1),
                    arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
                    fontsize=10, color='red')
        
        efficiency_plot_path = output_path / "efficiency_vs_nodes.png"
        plt.savefig(efficiency_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Plots saved:")
        print(f"  - {plot_path}")
        print(f"  - {efficiency_plot_path}")
        
        return plot_path, efficiency_plot_path
    
    def save_results_csv(self, results, output_path="analysis/sweep_summary.csv"):
        """Save results to CSV like simulator_simpleAndQuick"""
        if not results:
            return None
            
        df = pd.DataFrame(results)
        
        # Reorder columns to match simulator_simpleAndQuick output
        columns = [
            'nodes', 'slac_success_rate', 'slac_completion_time_avg', 'slac_completion_time_max',
            'slac_retry_avg', 'slac_timeout_rate', 'session_success', 'session_total',
            'efficiency_eta', 'throughput_mbps'
        ]
        
        df = df[columns]
        
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        
        df.to_csv(output_file, index=False, float_format='%.6f')
        print(f"Results saved to: {output_file}")
        
        return output_file
    
    def generate_report(self, results, output_path="analysis/sweep_report.md"):
        """Generate markdown report like simulator_simpleAndQuick"""
        if not results:
            return None
            
        df = pd.DataFrame(results)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write("# HPGP SLAC Node Sweep Report\n\n")
            f.write("OMNET++ simulation replicating simulator_simpleAndQuick functionality\n\n")
            f.write("## Summary Statistics\n\n")
            
            f.write("| Nodes | Success Rate | Avg Time (s) | Max Time (s) | Avg Retries | Efficiency |\n")
            f.write("|-------|--------------|--------------|--------------|-------------|------------|\n")
            
            for _, row in df.iterrows():
                f.write(f"| {row['nodes']} | {row['slac_success_rate']:.3f} | "
                       f"{row['slac_completion_time_avg']:.3f} | {row['slac_completion_time_max']:.3f} | "
                       f"{row['slac_retry_avg']:.1f} | {row['efficiency_eta']:.3f} |\n")
            
            f.write(f"\n## Key Findings\n\n")
            
            max_eff_idx = df['efficiency_eta'].idxmax()
            max_eff_nodes = df.loc[max_eff_idx, 'nodes']
            max_eff_val = df.loc[max_eff_idx, 'efficiency_eta']
            
            f.write(f"- **Peak Efficiency**: η = {max_eff_val:.3f} at N = {max_eff_nodes} nodes\n")
            f.write(f"- **Success Rate Range**: {df['slac_success_rate'].min():.3f} - {df['slac_success_rate'].max():.3f}\n")
            f.write(f"- **Completion Time Range**: {df['slac_completion_time_avg'].min():.3f}s - {df['slac_completion_time_avg'].max():.3f}s\n")
            f.write(f"- **Total Experiments**: {len(df)} node configurations tested\n")
            
        print(f"Report saved to: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description='HPGP SLAC Node Sweep Analysis')
    parser.add_argument('--nodes', nargs='+', type=int, 
                       default=list(range(5, 101, 5)),
                       help='Node counts to test')
    parser.add_argument('--seeds', nargs='+', type=int, default=[0],
                       help='Random seeds')
    parser.add_argument('--exe', default='./csma_ca_hpgp',
                       help='OMNET++ executable path')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with fewer nodes')
    
    args = parser.parse_args()
    
    if args.quick:
        args.nodes = [5, 10, 15, 20, 25]
        print("Quick test mode: limited node range")
    
    # Check if executable exists
    if not Path(args.exe).exists():
        print(f"Error: Executable '{args.exe}' not found. Run 'make' first.")
        return 1
    
    print("HPGP SLAC Node Sweep Analysis")
    print("=" * 50)
    print(f"Node range: {args.nodes}")
    print(f"Seeds: {args.seeds}")
    print(f"Executable: {args.exe}")
    print()
    
    # Run sweep
    sweep = HpgpSlacSweep(args.exe)
    results = sweep.run_node_sweep(args.nodes, args.seeds)
    
    if not results:
        print("No results obtained!")
        return 1
    
    print(f"\nAnalysis complete! {len(results)} data points collected.")
    
    # Generate outputs
    csv_path = sweep.save_results_csv(results)
    report_path = sweep.generate_report(results)
    plot_paths = sweep.generate_analysis_plots(results)
    
    print("\nGenerated files:")
    print(f"  - CSV: {csv_path}")
    print(f"  - Report: {report_path}")
    print(f"  - Plots: {plot_paths}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

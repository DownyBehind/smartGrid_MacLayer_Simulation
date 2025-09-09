#!/usr/bin/env python3
"""
Simple test runner for HPGP SLAC simulation
Replicates basic functionality of simulator_simpleAndQuick
"""

import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import glob
import re
from pathlib import Path

class SimpleHpgpTest:
    def __init__(self, omnetpp_path):
        self.omnetpp_path = omnetpp_path
        self.results_dir = "results"
        
    def run_simulation(self, node_count, config="SimpleNodeSweep"):
        """Run a single simulation with specified parameters"""
        # Map node_count to iteration index in simple_sweep.ini (5..100 step 5)
        run_index = max(0, (node_count - 5) // 5)
        cmd = [
            self.omnetpp_path,
            "-u", "Cmdenv",
            "-c", config,
            "-r", str(run_index),
            "-n", ".",
            f"--sim-time-limit=10s",
            f"--**.numNodes={node_count}",
            "simple_sweep.ini"
        ]
        
        print(f"Running simulation with {node_count} nodes...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running simulation: {result.stderr}")
            return False
            
        return True
    
    def parse_scalar_results(self, sca_file):
        """Parse OMNET++ scalar results file"""
        import math, re
        data = {
            'completion_time': [],
            'retry_count': [],
            'timeout_count': 0
        }
        scalar_re = re.compile(r'^scalar\s+(?P<module>\S+)\s+(?P<name>\S+)\s+(?P<value>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)')
        node_index_re = re.compile(r"node\[(\d+)\]")
        try:
            with open(sca_file, 'r') as f:
                for raw in f:
                    line = raw.strip()
                    if not line.startswith('scalar '):
                        continue
                    m = scalar_re.match(line)
                    if not m:
                        continue
                    module = m.group('module')
                    name = m.group('name')
                    val_str = m.group('value')
                    # Convert
                    try:
                        val = float(val_str)
                    except ValueError:
                        continue
                    # EV-only filter: ignore node[0] (EVSE)
                    idx = None
                    mi = node_index_re.search(module)
                    if mi:
                        try:
                            idx = int(mi.group(1))
                        except Exception:
                            idx = None
                    if name == 'slacCompletionTime:mean':
                        if idx is None or idx >= 1:
                            data['completion_time'].append(val)
                    elif name == 'slacRetryCount:mean':
                        if (idx is None or idx >= 1) and not math.isnan(val):
                            data['retry_count'].append(val)
                    elif name == 'slacTimeout:count':
                        if idx is None or idx >= 1:
                            data['timeout_count'] += int(val)
        except Exception as e:
            print(f"Error parsing {sca_file}: {e}")
        return data
    
    def calculate_efficiency(self, results, total_nodes):
        """Calculate SLAC efficiency metrics"""
        if not results['completion_time']:
            return {
                'success_rate': 0.0,
                'avg_completion_time': 0.0,
                'avg_retries': 0.0
            }
        
        successful_connections = len(results['completion_time'])
        expected_connections = total_nodes - 1  # Exclude EVSE
        
        success_rate = successful_connections / expected_connections if expected_connections > 0 else 0
        avg_completion_time = sum(results['completion_time']) / len(results['completion_time'])
        avg_retries = sum(results['retry_count']) / len(results['retry_count']) if results['retry_count'] else 0
        
        return {
            'success_rate': success_rate,
            'avg_completion_time': avg_completion_time,
            'avg_retries': avg_retries
        }
    
    def run_node_sweep(self, min_nodes=5, max_nodes=100, step=5):
        """Run simulation sweep across different node counts"""
        print(f"Running node sweep from {min_nodes} to {max_nodes} nodes...")
        
        # Create results directory
        os.makedirs(self.results_dir, exist_ok=True)
        
        sweep_results = []
        
        for node_count in range(min_nodes, max_nodes + 1, step):
            if self.run_simulation(node_count):
                # Find and parse result file
                sca_pattern = f"{self.results_dir}/SimpleNodeSweep-N{node_count}.sca"
                sca_files = glob.glob(sca_pattern)
                
                if sca_files:
                    results = self.parse_scalar_results(sca_files[0])
                    efficiency = self.calculate_efficiency(results, node_count)
                    
                    sweep_results.append({
                        'nodes': node_count,
                        'success_rate': efficiency['success_rate'],
                        'avg_completion_time': efficiency['avg_completion_time'],
                        'avg_retries': efficiency['avg_retries']
                    })
                    
                    print(f"  {node_count} nodes: {efficiency['success_rate']:.2%} success rate")
                else:
                    print(f"  No results found for {node_count} nodes")
        
        return sweep_results
    
    def plot_results(self, sweep_results, output_file="efficiency_vs_nodes.png"):
        """Generate plots similar to simulator_simpleAndQuick"""
        if not sweep_results:
            print("No results to plot")
            return
        
        df = pd.DataFrame(sweep_results)
        
        # Create subplot figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Success rate plot
        ax1.plot(df['nodes'], df['success_rate'] * 100, 'b-o', linewidth=2, markersize=6)
        ax1.set_xlabel('Number of Nodes')
        ax1.set_ylabel('Success Rate (%)')
        ax1.set_title('SLAC Success Rate vs Number of Nodes')
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 105)
        
        # Completion time plot
        ax2.plot(df['nodes'], df['avg_completion_time'], 'r-s', linewidth=2, markersize=6)
        ax2.set_xlabel('Number of Nodes')
        ax2.set_ylabel('Average Completion Time (s)')
        ax2.set_title('SLAC Completion Time vs Number of Nodes')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {output_file}")
        
        # Save CSV results
        csv_file = "sweep_results.csv"
        df.to_csv(csv_file, index=False)
        print(f"Results saved as {csv_file}")
        
        return df

def main():
    # Prefer the local built executable (contains linked modules); opp_run won't work without a library
    if os.path.exists("./csma_ca_hpgp"):
        omnetpp_exe = "./csma_ca_hpgp"
    else:
        print("Project executable './csma_ca_hpgp' not found. Build the project and try again.")
        return
    
    # Run the test
    tester = SimpleHpgpTest(omnetpp_exe)
    
    print("Starting simple HPGP SLAC simulation test...")
    results = tester.run_node_sweep(min_nodes=5, max_nodes=100, step=5)
    
    if results:
        print(f"\nCompleted {len(results)} simulations")
        tester.plot_results(results)
        print("\nTest completed successfully!")
    else:
        print("No successful simulations completed")

if __name__ == "__main__":
    main()

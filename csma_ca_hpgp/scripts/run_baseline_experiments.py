#!/usr/bin/env python3
"""
HPGP MAC Baseline Experiments Runner
Runs WC-A and WC-B experiments with different node counts
"""

import subprocess
import os
import time
import glob
from datetime import datetime

class BaselineExperimentRunner:
    def __init__(self, project_dir="."):
        self.project_dir = project_dir
        self.results_dir = os.path.join(project_dir, "results")
        self.test_dir = os.path.join(project_dir, "test")
        
    def run_single_experiment(self, config_name, num_nodes, run_id):
        """Run a single experiment"""
        print(f"  Run {run_id}/30...")
        
        # Run simulation
        cmd = [
            "./csma_ca_hpgp",
            "-u", "Cmdenv",
            "-c", config_name,
            f"test/baseline_wc_a/omnetpp.ini" if "WC_A" in config_name else f"test/baseline_wc_b/omnetpp.ini",
            "-r", str(run_id - 1)  # OMNeT++ uses 0-based run indices
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_dir, 
                                  capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                print(f"    ✓ Completed successfully")
                return True
            else:
                print(f"    ✗ Failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"    ✗ Timeout")
            return False
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return False
    
    def run_wc_a_experiments(self):
        """Run WC-A (Sequential SLAC) experiments"""
        print("1. Running WC-A (Sequential SLAC) Experiments...")
        print("=" * 50)
        
        node_counts = [2, 5, 10]
        total_runs = 30
        
        for num_nodes in node_counts:
            print(f"Testing with {num_nodes} nodes...")
            print(f"Running WC-A_{num_nodes}nodes experiment...")
            print(f"Config: Baseline_WC_A_Sequential_SLAC, Runs: {total_runs}")
            
            successful_runs = 0
            
            for run_id in range(1, total_runs + 1):
                success = self.run_single_experiment("Baseline_WC_A_Sequential_SLAC", 
                                                   num_nodes, run_id)
                if success:
                    successful_runs += 1
                
                # Small delay between runs
                time.sleep(0.1)
            
            print(f"WC-A with {num_nodes} nodes: {successful_runs}/{total_runs} successful")
            print()
    
    def run_wc_b_experiments(self):
        """Run WC-B (Simultaneous SLAC) experiments"""
        print("2. Running WC-B (Simultaneous SLAC) Experiments...")
        print("=" * 50)
        
        node_counts = [2, 5, 10]
        total_runs = 30
        
        for num_nodes in node_counts:
            print(f"Testing with {num_nodes} nodes...")
            print(f"Running WC-B_{num_nodes}nodes experiment...")
            print(f"Config: Baseline_WC_B_Simultaneous_SLAC, Runs: {total_runs}")
            
            successful_runs = 0
            
            for run_id in range(1, total_runs + 1):
                success = self.run_single_experiment("Baseline_WC_B_Simultaneous_SLAC", 
                                                   num_nodes, run_id)
                if success:
                    successful_runs += 1
                
                # Small delay between runs
                time.sleep(0.1)
            
            print(f"WC-B with {num_nodes} nodes: {successful_runs}/{total_runs} successful")
            print()
    
    def run_all_experiments(self):
        """Run all baseline experiments"""
        print("Starting HPGP MAC Baseline Experiments...")
        print("=" * 40)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run WC-A experiments
        self.run_wc_a_experiments()
        
        # Run WC-B experiments  
        self.run_wc_b_experiments()
        
        print("=" * 40)
        print(f"All experiments completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Analyze results
        print("Analyzing results...")
        self.analyze_results()
    
    def analyze_results(self):
        """Analyze experiment results"""
        print("Running data analysis...")
        
        # Run the analysis script
        analysis_script = os.path.join(self.project_dir, "analyze_baseline_data.py")
        if os.path.exists(analysis_script):
            try:
                result = subprocess.run(["python3", analysis_script], 
                                      cwd=self.project_dir, 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✓ Analysis completed successfully")
                else:
                    print(f"✗ Analysis failed: {result.stderr}")
            except Exception as e:
                print(f"✗ Analysis error: {e}")
        else:
            print("✗ Analysis script not found")

def main():
    """Main function"""
    runner = BaselineExperimentRunner()
    runner.run_all_experiments()

if __name__ == "__main__":
    main()

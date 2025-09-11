#!/usr/bin/env python3
"""
Extended HPGP MAC Experiment Runner
Runs 30 iterations of 120-second experiments for comprehensive analysis
"""

import subprocess
import time
import os
from pathlib import Path
import json

def run_experiment(config_name, ini_path, output_dir, num_runs=30):
    """Run a single experiment configuration multiple times"""
    print(f"Running {config_name} - {num_runs} iterations...")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Run the experiment
    cmd = [
        "./csma_ca_hpgp",
        "-u", "Cmdenv",
        "-c", config_name,
        "-n", ".",
        ini_path,
        "-r", "0-" + str(num_runs-1)
    ]
    
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        if result.returncode == 0:
            print(f"✅ {config_name} completed successfully")
            return True
        else:
            print(f"❌ {config_name} failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {config_name} timed out")
        return False
    except Exception as e:
        print(f"💥 {config_name} failed with exception: {e}")
        return False

def run_all_experiments():
    """Run all experiment configurations"""
    
    experiments = [
        # WC-A Sequential experiments
        {
            "config": "Baseline_WC_A_Sequential_SLAC",
            "ini": "test/baseline_wc_a/omnetpp.ini",
            "output": "results_extended/wc_a_sequential/nodes3",
            "description": "WC-A Sequential, 3 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_A_Sequential_SLAC_5Nodes",
            "ini": "test/baseline_wc_a_nodes5/omnetpp.ini",
            "output": "results_extended/wc_a_sequential/nodes5",
            "description": "WC-A Sequential, 5 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_A_Sequential_SLAC_10Nodes",
            "ini": "test/baseline_wc_a_nodes10/omnetpp.ini",
            "output": "results_extended/wc_a_sequential/nodes10",
            "description": "WC-A Sequential, 10 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_A_Sequential_SLAC_20Nodes",
            "ini": "test/baseline_wc_a_nodes20/omnetpp.ini",
            "output": "results_extended/wc_a_sequential/nodes20",
            "description": "WC-A Sequential, 20 nodes, 120s, 30 runs"
        },
        
        # WC-B Simultaneous experiments
        {
            "config": "Baseline_WC_B_Simultaneous_SLAC",
            "ini": "test/baseline_wc_b/omnetpp.ini",
            "output": "results_extended/wc_b_simultaneous/nodes3",
            "description": "WC-B Simultaneous, 3 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_B_Simultaneous_SLAC_5Nodes",
            "ini": "test/baseline_wc_b_nodes5/omnetpp.ini",
            "output": "results_extended/wc_b_simultaneous/nodes5",
            "description": "WC-B Simultaneous, 5 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_B_Simultaneous_SLAC_10Nodes",
            "ini": "test/baseline_wc_b_nodes10/omnetpp.ini",
            "output": "results_extended/wc_b_simultaneous/nodes10",
            "description": "WC-B Simultaneous, 10 nodes, 120s, 30 runs"
        },
        {
            "config": "Baseline_WC_B_Simultaneous_SLAC_20Nodes",
            "ini": "test/baseline_wc_b_nodes20/omnetpp.ini",
            "output": "results_extended/wc_b_simultaneous/nodes20",
            "description": "WC-B Simultaneous, 20 nodes, 120s, 30 runs"
        }
    ]
    
    # Create results directory
    Path("results_extended").mkdir(exist_ok=True)
    
    # Track results
    results = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "experiments": []
    }
    
    successful_experiments = 0
    total_experiments = len(experiments)
    
    for i, exp in enumerate(experiments, 1):
        print(f"\n{'='*60}")
        print(f"Experiment {i}/{total_experiments}: {exp['description']}")
        print(f"{'='*60}")
        
        start_time = time.time()
        success = run_experiment(exp["config"], exp["ini"], exp["output"])
        end_time = time.time()
        
        duration = end_time - start_time
        
        exp_result = {
            "config": exp["config"],
            "description": exp["description"],
            "success": success,
            "duration_seconds": duration,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
            "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        }
        
        results["experiments"].append(exp_result)
        
        if success:
            successful_experiments += 1
            print(f"✅ Completed in {duration:.1f} seconds")
        else:
            print(f"❌ Failed after {duration:.1f} seconds")
        
        # Save intermediate results
        with open("results_extended/experiment_log.json", "w") as f:
            json.dump(results, f, indent=2)
    
    results["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    results["successful_experiments"] = successful_experiments
    results["total_experiments"] = total_experiments
    results["success_rate"] = successful_experiments / total_experiments
    
    # Save final results
    with open("results_extended/experiment_log.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"EXPERIMENT SUMMARY")
    print(f"{'='*60}")
    print(f"Total experiments: {total_experiments}")
    print(f"Successful: {successful_experiments}")
    print(f"Failed: {total_experiments - successful_experiments}")
    print(f"Success rate: {results['success_rate']:.1%}")
    print(f"Total time: {time.strftime('%H:%M:%S', time.gmtime(sum(exp['duration_seconds'] for exp in results['experiments'])))}")
    
    return results

if __name__ == "__main__":
    print("Starting Extended HPGP MAC Experiments")
    print("Duration: 120 seconds per experiment")
    print("Iterations: 30 runs per configuration")
    print("Total configurations: 8")
    print("Estimated total time: 4-6 hours")
    
    start_time = time.time()
    results = run_all_experiments()
    total_time = time.time() - start_time
    
    print(f"\nAll experiments completed in {total_time/3600:.1f} hours")
    print("Results saved to results_extended/")

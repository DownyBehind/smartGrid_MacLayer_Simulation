#!/usr/bin/env python3
"""
HPGP SLAC Simulation Batch Runner
Automated batch execution of OMNET++ simulations with different parameters
"""

import subprocess
import os
import sys
import time
import json
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SlacSimulationRunner:
    def __init__(self, omnetpp_exe="./csma_ca_hpgp", results_dir="results"):
        self.omnetpp_exe = omnetpp_exe
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
    def run_single_simulation(self, config, seed=None, additional_params=None):
        """Run a single simulation configuration"""
        cmd = [self.omnetpp_exe, "-u", "Cmdenv", "-c", config]
        
        if seed is not None:
            cmd.extend(["--seed-set", str(seed)])
            
        if additional_params:
            for param, value in additional_params.items():
                cmd.extend(["--", f"*.{param}={value}"])
        
        # Create unique result file names
        timestamp = int(time.time())
        result_prefix = f"{config}_{seed}_{timestamp}" if seed else f"{config}_{timestamp}"
        
        cmd.extend([
            f"--result-dir={self.results_dir}",
            f"--output-scalar-file={result_prefix}.sca",
            f"--output-vector-file={result_prefix}.vec"
        ])
        
        logger.info(f"Running simulation: {config} (seed: {seed})")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"Simulation completed: {config} (seed: {seed}) in {duration:.1f}s")
                return {"config": config, "seed": seed, "status": "success", "duration": duration}
            else:
                logger.error(f"Simulation failed: {config} (seed: {seed})")
                logger.error(f"Error output: {result.stderr}")
                return {"config": config, "seed": seed, "status": "failed", "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            logger.error(f"Simulation timeout: {config} (seed: {seed})")
            return {"config": config, "seed": seed, "status": "timeout"}
        except Exception as e:
            logger.error(f"Simulation error: {config} (seed: {seed}) - {str(e)}")
            return {"config": config, "seed": seed, "status": "error", "error": str(e)}
    
    def run_parameter_sweep(self, base_config, parameter_ranges, seeds=None):
        """Run parameter sweep across multiple parameter values"""
        if seeds is None:
            seeds = [0]
            
        simulation_tasks = []
        
        for param_name, param_values in parameter_ranges.items():
            for param_value in param_values:
                for seed in seeds:
                    additional_params = {param_name: param_value}
                    simulation_tasks.append((base_config, seed, additional_params))
        
        return self.run_batch_simulations(simulation_tasks)
    
    def run_batch_simulations(self, simulation_tasks, max_workers=4):
        """Run multiple simulations in parallel"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all simulations
            future_to_task = {}
            for task in simulation_tasks:
                config, seed, additional_params = task
                future = executor.submit(self.run_single_simulation, config, seed, additional_params)
                future_to_task[future] = task
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Task failed: {task} - {str(e)}")
                    results.append({
                        "config": task[0], 
                        "seed": task[1], 
                        "status": "exception", 
                        "error": str(e)
                    })
        
        return results
    
    def run_predefined_scenarios(self):
        """Run predefined simulation scenarios"""
        scenarios = [
            ("SingleEVSE", list(range(10))),      # 10 seeds
            ("ConcurrentEVSE", list(range(10))),  # 10 seeds  
            ("HighDensity", list(range(5))),      # 5 seeds (longer sims)
            ("LowLatency", list(range(10))),      # 10 seeds
            ("HighNoise", list(range(10))),       # 10 seeds
        ]
        
        all_tasks = []
        for config, seeds in scenarios:
            for seed in seeds:
                all_tasks.append((config, seed, None))
        
        logger.info(f"Running {len(all_tasks)} predefined scenarios")
        return self.run_batch_simulations(all_tasks)
    
    def generate_summary_report(self, results):
        """Generate summary report of simulation results"""
        summary = {
            "total_simulations": len(results),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "timeout": len([r for r in results if r["status"] == "timeout"]),
            "error": len([r for r in results if r["status"] == "error"]),
            "total_duration": sum(r.get("duration", 0) for r in results),
            "average_duration": sum(r.get("duration", 0) for r in results) / len(results) if results else 0
        }
        
        # Save detailed results
        results_file = self.results_dir / "batch_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save summary
        summary_file = self.results_dir / "batch_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Batch simulation summary:")
        logger.info(f"  Total simulations: {summary['total_simulations']}")
        logger.info(f"  Successful: {summary['successful']}")
        logger.info(f"  Failed: {summary['failed']}")
        logger.info(f"  Timeout: {summary['timeout']}")
        logger.info(f"  Errors: {summary['error']}")
        logger.info(f"  Total duration: {summary['total_duration']:.1f}s")
        logger.info(f"  Average duration: {summary['average_duration']:.1f}s")
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='HPGP SLAC Simulation Batch Runner')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Single simulation command
    single_parser = subparsers.add_parser('single', help='Run single simulation')
    single_parser.add_argument('config', help='Configuration name')
    single_parser.add_argument('--seed', type=int, default=0, help='Random seed')
    
    # Batch simulation command
    batch_parser = subparsers.add_parser('batch', help='Run batch simulations')
    batch_parser.add_argument('--configs', nargs='+', required=True, help='Configuration names')
    batch_parser.add_argument('--seeds', nargs='+', type=int, default=[0], help='Random seeds')
    batch_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    
    # Parameter sweep command
    sweep_parser = subparsers.add_parser('sweep', help='Run parameter sweep')
    sweep_parser.add_argument('config', help='Base configuration name')
    sweep_parser.add_argument('--param', required=True, help='Parameter name')
    sweep_parser.add_argument('--values', nargs='+', required=True, help='Parameter values')
    sweep_parser.add_argument('--seeds', nargs='+', type=int, default=[0], help='Random seeds')
    
    # Predefined scenarios command
    scenarios_parser = subparsers.add_parser('scenarios', help='Run predefined scenarios')
    scenarios_parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check if simulation executable exists
    if not Path("./csma_ca_hpgp").exists():
        logger.error("Simulation executable './csma_ca_hpgp' not found. Run 'make' first.")
        return
    
    runner = SlacSimulationRunner()
    
    if args.command == 'single':
        result = runner.run_single_simulation(args.config, args.seed)
        print(json.dumps(result, indent=2))
        
    elif args.command == 'batch':
        tasks = []
        for config in args.configs:
            for seed in args.seeds:
                tasks.append((config, seed, None))
        
        results = runner.run_batch_simulations(tasks, args.workers)
        summary = runner.generate_summary_report(results)
        
    elif args.command == 'sweep':
        parameter_ranges = {args.param: args.values}
        results = runner.run_parameter_sweep(args.config, parameter_ranges, args.seeds)
        summary = runner.generate_summary_report(results)
        
    elif args.command == 'scenarios':
        results = runner.run_predefined_scenarios()
        summary = runner.generate_summary_report(results)

if __name__ == "__main__":
    main()

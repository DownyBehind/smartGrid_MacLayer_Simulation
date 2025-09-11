#!/usr/bin/env python3
"""
Enhanced DC Command Analysis Script
- DC 명령 데드라인 미스율 분석
- SLAC 실패율 집계
- WC-A vs WC-B 비교 분석
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import re
import glob
from scipy import stats as scipy_stats
import json

class DCAnalyzer:
    def __init__(self):
        self.results = {}
        self.slac_failures = {}
        
    def parse_sca_file(self, sca_file):
        """Parse OMNeT++ scalar file for DC command data"""
        data = {
            'dc_cycles': [],
            'slac_attempts': [],
            'mac_tx': [],
            'collisions': []
        }
        
        try:
            with open(sca_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('scalar'):
                        parts = line.split()
                        if len(parts) >= 4:
                            module = parts[1]
                            name = parts[2]
                            value = parts[3]
                            
                            # DC cycle data
                            if 'dcCycle' in name:
                                data['dc_cycles'].append({
                                    'module': module,
                                    'value': float(value)
                                })
                            
                            # SLAC attempt data
                            elif 'slacAttempt' in name:
                                data['slac_attempts'].append({
                                    'module': module,
                                    'value': float(value)
                                })
                            
                            # MAC transmission data
                            elif 'macTx' in name:
                                data['mac_tx'].append({
                                    'module': module,
                                    'value': float(value)
                                })
                            
                            # Collision data
                            elif 'collision' in name:
                                data['collisions'].append({
                                    'module': module,
                                    'value': float(value)
                                })
        except Exception as e:
            print(f"Error parsing {sca_file}: {e}")
            
        return data
    
    def calculate_dc_metrics(self, data):
        """Calculate DC command metrics"""
        metrics = {
            'total_dc_requests': 0,
            'dc_deadline_misses': 0,
            'dc_success_rate': 0.0,
            'dc_avg_rtt': 0.0,
            'dc_p95_rtt': 0.0,
            'dc_p99_rtt': 0.0,
            'slac_failures': 0,
            'slac_success_rate': 0.0
        }
        
        # DC cycle analysis
        if data['dc_cycles']:
            dc_values = [d['value'] for d in data['dc_cycles']]
            metrics['total_dc_requests'] = len(dc_values)
            
            # Assume negative values indicate deadline misses
            deadline_misses = sum(1 for v in dc_values if v < 0)
            metrics['dc_deadline_misses'] = deadline_misses
            metrics['dc_success_rate'] = (len(dc_values) - deadline_misses) / len(dc_values) if dc_values else 0
            
            # RTT analysis (positive values only)
            positive_rtts = [v for v in dc_values if v > 0]
            if positive_rtts:
                metrics['dc_avg_rtt'] = np.mean(positive_rtts)
                metrics['dc_p95_rtt'] = np.percentile(positive_rtts, 95)
                metrics['dc_p99_rtt'] = np.percentile(positive_rtts, 99)
        
        # SLAC analysis
        if data['slac_attempts']:
            slac_values = [d['value'] for d in data['slac_attempts']]
            # Assume 0 means failure, 1 means success
            failures = sum(1 for v in slac_values if v == 0)
            metrics['slac_failures'] = failures
            metrics['slac_success_rate'] = (len(slac_values) - failures) / len(slac_values) if slac_values else 0
        
        return metrics
    
    def analyze_experiment(self, experiment_dir, scenario_name):
        """Analyze single experiment directory"""
        print(f"Analyzing {scenario_name}...")
        
        # Find all .sca files
        sca_files = glob.glob(f"{experiment_dir}/results/*.sca")
        
        if not sca_files:
            print(f"No .sca files found in {experiment_dir}/results/")
            return None
        
        all_metrics = []
        
        for sca_file in sca_files:
            print(f"  Processing {sca_file}")
            data = self.parse_sca_file(sca_file)
            metrics = self.calculate_dc_metrics(data)
            all_metrics.append(metrics)
        
        # Calculate average metrics
        if all_metrics:
            avg_metrics = {}
            for key in all_metrics[0].keys():
                values = [m[key] for m in all_metrics if key in m]
                if values:
                    avg_metrics[key] = np.mean(values)
                else:
                    avg_metrics[key] = 0.0
            
            avg_metrics['scenario'] = scenario_name
            avg_metrics['num_runs'] = len(all_metrics)
            
            return avg_metrics
        
        return None
    
    def run_analysis(self):
        """Run complete analysis"""
        print("=== Enhanced DC Command Analysis ===")
        
        # Analyze WC-A
        wc_a_metrics = self.analyze_experiment("test/baseline_wc_a", "WC_A_Sequential")
        
        # Analyze WC-B
        wc_b_metrics = self.analyze_experiment("test/baseline_wc_b", "WC_B_Simultaneous")
        
        # Combine results
        results = []
        if wc_a_metrics:
            results.append(wc_a_metrics)
        if wc_b_metrics:
            results.append(wc_b_metrics)
        
        if results:
            self.results = results
            self.create_analysis_report()
            self.create_visualizations()
        else:
            print("No valid results found!")
    
    def create_analysis_report(self):
        """Create analysis report"""
        print("\n=== DC Command Analysis Report ===")
        
        for result in self.results:
            print(f"\n{result['scenario']} Results:")
            print(f"  Runs: {result['num_runs']}")
            print(f"  Total DC Requests: {result['total_dc_requests']:.0f}")
            print(f"  DC Deadline Misses: {result['dc_deadline_misses']:.0f}")
            print(f"  DC Success Rate: {result['dc_success_rate']:.2%}")
            print(f"  DC Avg RTT: {result['dc_avg_rtt']:.3f} ms")
            print(f"  DC P95 RTT: {result['dc_p95_rtt']:.3f} ms")
            print(f"  DC P99 RTT: {result['dc_p99_rtt']:.3f} ms")
            print(f"  SLAC Failures: {result['slac_failures']:.0f}")
            print(f"  SLAC Success Rate: {result['slac_success_rate']:.2%}")
        
        # Statistical comparison
        if len(self.results) == 2:
            print(f"\n=== Statistical Comparison ===")
            wc_a = self.results[0]
            wc_b = self.results[1]
            
            print(f"DC Success Rate:")
            print(f"  WC-A: {wc_a['dc_success_rate']:.2%}")
            print(f"  WC-B: {wc_b['dc_success_rate']:.2%}")
            print(f"  Difference: {wc_b['dc_success_rate'] - wc_a['dc_success_rate']:.2%}")
            
            print(f"\nSLAC Success Rate:")
            print(f"  WC-A: {wc_a['slac_success_rate']:.2%}")
            print(f"  WC-B: {wc_b['slac_success_rate']:.2%}")
            print(f"  Difference: {wc_b['slac_success_rate'] - wc_a['slac_success_rate']:.2%}")
    
    def create_visualizations(self):
        """Create analysis visualizations"""
        if not self.results:
            return
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('DC Command Analysis Results', fontsize=16, fontweight='bold')
        
        # Extract data
        scenarios = [r['scenario'] for r in self.results]
        dc_success_rates = [r['dc_success_rate'] for r in self.results]
        slac_success_rates = [r['slac_success_rate'] for r in self.results]
        dc_avg_rtts = [r['dc_avg_rtt'] for r in self.results]
        dc_p99_rtts = [r['dc_p99_rtt'] for r in self.results]
        
        # 1. DC Success Rate Comparison
        axes[0, 0].bar(scenarios, dc_success_rates, color=['skyblue', 'lightcoral'])
        axes[0, 0].set_title('DC Command Success Rate')
        axes[0, 0].set_ylabel('Success Rate')
        axes[0, 0].set_ylim(0, 1)
        for i, v in enumerate(dc_success_rates):
            axes[0, 0].text(i, v + 0.01, f'{v:.2%}', ha='center', va='bottom')
        
        # 2. SLAC Success Rate Comparison
        axes[0, 1].bar(scenarios, slac_success_rates, color=['lightgreen', 'orange'])
        axes[0, 1].set_title('SLAC Success Rate')
        axes[0, 1].set_ylabel('Success Rate')
        axes[0, 1].set_ylim(0, 1)
        for i, v in enumerate(slac_success_rates):
            axes[0, 1].text(i, v + 0.01, f'{v:.2%}', ha='center', va='bottom')
        
        # 3. DC RTT Comparison
        x = np.arange(len(scenarios))
        width = 0.35
        axes[1, 0].bar(x - width/2, dc_avg_rtts, width, label='Avg RTT', color='lightblue')
        axes[1, 0].bar(x + width/2, dc_p99_rtts, width, label='P99 RTT', color='darkblue')
        axes[1, 0].set_title('DC Command RTT Comparison')
        axes[1, 0].set_ylabel('RTT (ms)')
        axes[1, 0].set_xticks(x)
        axes[1, 0].set_xticklabels(scenarios)
        axes[1, 0].legend()
        
        # 4. Combined Performance
        metrics = ['DC Success', 'SLAC Success', 'DC Avg RTT', 'DC P99 RTT']
        wc_a_values = [dc_success_rates[0], slac_success_rates[0], dc_avg_rtts[0], dc_p99_rtts[0]]
        wc_b_values = [dc_success_rates[1], slac_success_rates[1], dc_avg_rtts[1], dc_p99_rtts[1]]
        
        x = np.arange(len(metrics))
        width = 0.35
        axes[1, 1].bar(x - width/2, wc_a_values, width, label='WC-A', color='skyblue')
        axes[1, 1].bar(x + width/2, wc_b_values, width, label='WC-B', color='lightcoral')
        axes[1, 1].set_title('Combined Performance Metrics')
        axes[1, 1].set_ylabel('Value')
        axes[1, 1].set_xticks(x)
        axes[1, 1].set_xticklabels(metrics, rotation=45)
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig('dc_analysis_enhanced_results.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Save results to CSV
        df = pd.DataFrame(self.results)
        df.to_csv('dc_analysis_enhanced_results.csv', index=False)
        print(f"\nResults saved to dc_analysis_enhanced_results.csv")

if __name__ == "__main__":
    analyzer = DCAnalyzer()
    analyzer.run_analysis()

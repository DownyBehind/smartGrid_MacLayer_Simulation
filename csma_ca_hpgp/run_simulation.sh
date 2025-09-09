#!/bin/bash
#
# HPGP SLAC Simulation Runner
# Automated script to run OMNET++ simulations and analyze results
#

# Configuration
INET_PLC_DIR="../../inet_plc/inet"
OMNETPP_ROOT="../../omnetpp-6.1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check environment
check_environment() {
    log "Checking simulation environment..."
    
    # Check OMNET++ installation
    if [ ! -d "$OMNETPP_ROOT" ]; then
        error "OMNET++ not found at $OMNETPP_ROOT"
        exit 1
    fi
    
    # Check INET PLC framework
    if [ ! -d "$INET_PLC_DIR" ]; then
        error "INET PLC framework not found at $INET_PLC_DIR"
        exit 1
    fi
    
    # Check if INET PLC is built
    if [ ! -f "$INET_PLC_DIR/src/libINET.so" ] && [ ! -f "$INET_PLC_DIR/src/libINET.a" ]; then
        warning "INET PLC library not found. Building INET PLC..."
        build_inet_plc
    fi
    
    success "Environment check passed"
}

# Build INET PLC framework
build_inet_plc() {
    log "Building INET PLC framework..."
    
    cd "$INET_PLC_DIR"
    
    # Set environment
    source "$OMNETPP_ROOT/setenv"
    
    # Generate makefiles and build
    if make makefiles && make; then
        success "INET PLC built successfully"
    else
        error "Failed to build INET PLC"
        exit 1
    fi
    
    cd - > /dev/null
}

# Build simulation
build_simulation() {
    log "Building HPGP SLAC simulation..."
    
    # Set environment
    source "$OMNETPP_ROOT/setenv"
    
    # Clean and build
    if make clean && make; then
        success "Simulation built successfully"
    else
        error "Failed to build simulation"
        exit 1
    fi
}

# Run single configuration
run_config() {
    local config=$1
    local description=$2
    
    log "Running configuration: $config - $description"
    
    # Create results directory
    mkdir -p results
    
    # Run simulation from simulations directory
    cd simulations
    if ../csma_ca_hpgp -u Cmdenv -c "$config" > "../results/run_${config}.log" 2>&1; then
        success "Configuration $config completed"
        cd ..
    else
        error "Configuration $config failed"
        cd ..
        return 1
    fi
}

# Run all configurations
run_simulations() {
    log "Starting HPGP SLAC simulations..."
    
    # Define configurations
    declare -A configs=(
        ["SingleEVSE"]="Single EVSE with multiple EVs - baseline scenario"
        ["ConcurrentEVSE"]="Multiple EVSEs with multiple EVs - concurrent SLAC scenario"
        ["HighDensity"]="High density scenario with many nodes"
        ["LowLatency"]="Low latency scenario with optimized parameters"
        ["HighNoise"]="High noise environment scenario"
        ["FastCharging"]="Fast charging scenario with higher data rates"
    )
    
    local failed_configs=()
    
    for config in "${!configs[@]}"; do
        if ! run_config "$config" "${configs[$config]}"; then
            failed_configs+=("$config")
        fi
    done
    
    if [ ${#failed_configs[@]} -eq 0 ]; then
        success "All simulations completed successfully"
    else
        warning "Some simulations failed: ${failed_configs[*]}"
        return 1
    fi
}

# Analyze results
analyze_results() {
    log "Analyzing simulation results..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        warning "Python3 not found. Skipping analysis."
        return 1
    fi
    
    # Install required packages if needed
    pip3 install -q pandas matplotlib seaborn numpy 2>/dev/null || true
    
    # Run analysis
    if python3 analyze_results.py --results-dir results --output-dir analysis; then
        success "Results analysis completed"
        log "Analysis results saved in 'analysis/' directory"
    else
        error "Results analysis failed"
        return 1
    fi
}

# Generate summary report
generate_report() {
    log "Generating simulation summary report..."
    
    local report_file="SIMULATION_REPORT.md"
    
    cat > "$report_file" << EOF
# HPGP SLAC Simulation Report

Generated on: $(date)

## Simulation Overview

This report summarizes the results of HPGP SLAC (Signal Level Attenuation Characterization) 
simulations using OMNET++ with IEEE1901 Power Line Communication.

### Objectives
- Measure SLAC completion delays with multiple concurrent nodes
- Analyze the impact of network density on SLAC performance
- Study retry patterns and failure rates
- Compare different EVSE deployment scenarios

### Configurations Tested
EOF

    # Add configuration details
    declare -A configs=(
        ["SingleEVSE"]="Single EVSE with multiple EVs - baseline scenario"
        ["ConcurrentEVSE"]="Multiple EVSEs with multiple EVs - concurrent SLAC scenario"
        ["HighDensity"]="High density scenario with many nodes"
        ["LowLatency"]="Low latency scenario with optimized parameters"
        ["HighNoise"]="High noise environment scenario"
        ["FastCharging"]="Fast charging scenario with higher data rates"
    )
    
    for config in "${!configs[@]}"; do
        echo "- **$config**: ${configs[$config]}" >> "$report_file"
    done
    
    cat >> "$report_file" << EOF

### Results

Results are available in the following files:
- \`analysis/summary_statistics.csv\` - Numerical summary of all results
- \`analysis/slac_delay_vs_nodes.png\` - SLAC delay vs network size
- \`analysis/retry_distribution.png\` - Distribution of retry counts
- \`analysis/concurrent_impact.png\` - Impact of concurrent SLAC procedures

### Key Findings

$(if [ -f "analysis/summary_statistics.csv" ]; then
    echo "Statistical summary has been generated. Please review the analysis plots for detailed insights."
else
    echo "Analysis data not available. Please run the analysis step."
fi)

### Simulation Environment

- **OMNET++**: $(if [ -f "$OMNETPP_ROOT/Version" ]; then cat "$OMNETPP_ROOT/Version"; else echo "6.1"; fi)
- **INET Framework**: PLC-enabled version with IEEE1901 support
- **Platform**: $(uname -s) $(uname -m)
- **Simulation Time**: 30 seconds per configuration
- **Random Seeds**: 10 repetitions per scenario

EOF

    success "Report generated: $report_file"
}

# Clean all generated files
clean_all() {
    log "Cleaning all generated files..."
    
    make clean
    rm -rf results analysis
    rm -f SIMULATION_REPORT.md
    
    success "Cleanup completed"
}

# Main execution
main() {
    echo "============================================"
    echo "  HPGP SLAC Simulation Runner"
    echo "============================================"
    echo
    
    case "${1:-full}" in
        "env")
            check_environment
            ;;
        "build-inet")
            check_environment
            build_inet_plc
            ;;
        "build")
            check_environment
            build_simulation
            ;;
        "run")
            check_environment
            build_simulation
            run_simulations
            ;;
        "analyze")
            analyze_results
            ;;
        "report")
            generate_report
            ;;
        "clean")
            clean_all
            ;;
        "full")
            check_environment
            build_simulation
            run_simulations
            analyze_results
            generate_report
            ;;
        "help")
            echo "Usage: $0 [command]"
            echo
            echo "Commands:"
            echo "  env        - Check environment only"
            echo "  build-inet - Build INET PLC framework"
            echo "  build      - Build simulation only"
            echo "  run        - Build and run simulations"
            echo "  analyze    - Analyze existing results"
            echo "  report     - Generate summary report"
            echo "  clean      - Clean all generated files"
            echo "  full       - Complete workflow (default)"
            echo "  help       - Show this help"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"

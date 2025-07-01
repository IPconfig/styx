#!/bin/bash

# Script to run original experiments with coordinated checkpointing
# Usage: ./scripts/run_original_experiments.sh [experiment_type] [parameters...]

set -e

EXPERIMENT_TYPE=${1:-"ycsbt"}
echo "Running original experiment: $EXPERIMENT_TYPE"

# Set environment to use coordinated checkpointing (original behavior)
export CHECKPOINTING_STRATEGY=COORDINATED

case $EXPERIMENT_TYPE in
    "ycsbt")
        # YCSB-T experiment
        # Parameters: client_threads n_keys n_part zipf_const input_rate total_time saving_dir warmup_seconds epoch_size
        CLIENT_THREADS=${2:-4}
        N_KEYS=${3:-1000}
        N_PART=${4:-4}
        ZIPF_CONST=${5:-0.8}
        INPUT_RATE=${6:-1000}
        TOTAL_TIME=${7:-60}
        SAVING_DIR=${8:-"results/ycsbt_coordinated"}
        WARMUP_SECONDS=${9:-10}
        EPOCH_SIZE=${10:-10}
        
        echo "Running YCSB-T experiment with coordinated checkpointing..."
        echo "Parameters: threads=$CLIENT_THREADS, keys=$N_KEYS, partitions=$N_PART, zipf=$ZIPF_CONST"
        echo "           rate=$INPUT_RATE, time=$TOTAL_TIME, warmup=$WARMUP_SECONDS, epoch=$EPOCH_SIZE"
        
        bash scripts/run_experiment.sh "ycsbt" "$INPUT_RATE" "$N_KEYS" "$N_PART" "$ZIPF_CONST" "$CLIENT_THREADS" "$TOTAL_TIME" "$SAVING_DIR" "$WARMUP_SECONDS" "$EPOCH_SIZE"
        ;;
    
    "tpcc")
        # TPC-C experiment
        # Parameters: client_threads n_part input_rate total_time saving_dir warmup_seconds n_keys
        CLIENT_THREADS=${2:-4}
        N_PART=${3:-4}
        INPUT_RATE=${4:-1000}
        TOTAL_TIME=${5:-60}
        SAVING_DIR=${6:-"results/tpcc_coordinated"}
        WARMUP_SECONDS=${7:-10}
        N_KEYS=${8:-1000}
        
        echo "Running TPC-C experiment with coordinated checkpointing..."
        echo "Parameters: threads=$CLIENT_THREADS, partitions=$N_PART, rate=$INPUT_RATE"
        echo "           time=$TOTAL_TIME, warmup=$WARMUP_SECONDS, keys=$N_KEYS"
        
        bash scripts/run_experiment.sh "tpcc" "$INPUT_RATE" "$N_KEYS" "$N_PART" "0" "$CLIENT_THREADS" "$TOTAL_TIME" "$SAVING_DIR" "$WARMUP_SECONDS" "10"
        ;;
    
    "dhr")
        # Deathstar Hotel Reservation experiment
        # Parameters: client_threads n_part input_rate total_time saving_dir warmup_seconds
        CLIENT_THREADS=${2:-4}
        N_PART=${3:-4}
        INPUT_RATE=${4:-1000}
        TOTAL_TIME=${5:-60}
        SAVING_DIR=${6:-"results/dhr_coordinated"}
        WARMUP_SECONDS=${7:-10}
        
        echo "Running Deathstar Hotel Reservation experiment with coordinated checkpointing..."
        echo "Parameters: threads=$CLIENT_THREADS, partitions=$N_PART, rate=$INPUT_RATE"
        echo "           time=$TOTAL_TIME, warmup=$WARMUP_SECONDS"
        
        bash scripts/run_experiment.sh "dhr" "$INPUT_RATE" "0" "$N_PART" "0" "$CLIENT_THREADS" "$TOTAL_TIME" "$SAVING_DIR" "$WARMUP_SECONDS" "10"
        ;;
    
    "dmr")
        # Deathstar Movie Review experiment
        # Parameters: client_threads n_part input_rate total_time saving_dir warmup_seconds
        CLIENT_THREADS=${2:-4}
        N_PART=${3:-4}
        INPUT_RATE=${4:-1000}
        TOTAL_TIME=${5:-60}
        SAVING_DIR=${6:-"results/dmr_coordinated"}
        WARMUP_SECONDS=${7:-10}
        
        echo "Running Deathstar Movie Review experiment with coordinated checkpointing..."
        echo "Parameters: threads=$CLIENT_THREADS, partitions=$N_PART, rate=$INPUT_RATE"
        echo "           time=$TOTAL_TIME, warmup=$WARMUP_SECONDS"
        
        bash scripts/run_experiment.sh "dmr" "$INPUT_RATE" "0" "$N_PART" "0" "$CLIENT_THREADS" "$TOTAL_TIME" "$SAVING_DIR" "$WARMUP_SECONDS" "10"
        ;;
    
    "scalability")
        # Scalability experiment
        echo "Running scalability experiment with coordinated checkpointing..."
        bash scripts/run_scalability_experiments.sh
        ;;
    
    "batch")
        # Batch experiments
        echo "Running batch experiments with coordinated checkpointing..."
        bash scripts/run_batch_experiments.sh
        ;;
    
    *)
        echo "Unknown experiment type: $EXPERIMENT_TYPE"
        echo "Available experiments: ycsbt, tpcc, dhr, dmr, scalability, batch"
        echo ""
        echo "Examples:"
        echo "  ./scripts/run_original_experiments.sh ycsbt"
        echo "  ./scripts/run_original_experiments.sh tpcc 4 4 1000 60 results/tpcc_test 10 1000"
        echo "  ./scripts/run_original_experiments.sh scalability"
        exit 1
        ;;
esac

echo "✅ Original experiment completed with coordinated checkpointing!" 
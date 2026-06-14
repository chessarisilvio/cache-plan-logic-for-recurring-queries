# Manual Benchmark Test for Cache Plan Logic

This document provides step-by-step instructions to manually test the caching mechanism for recurring queries
using the 35B model on a free GPU (Tesla P40). The test will compare latency with and without the cache.

## Prerequisites

- The 35B model (Qwen3.6-35B-A3B-IQ4_XS) must be running and accessible via a local API endpoint.
  For example, using `llama-server` from the llama.cpp project or a similar backend.
- The cache module (`src/cache.py`) and worker module (`src/worker.py`) are present and functional.
- Python 3.12 or higher is installed.
- Environment variables for configuration (if any) are set.

## Setup

1. Clone the repository (if not already done) and navigate to the project directory.
   Note: Use relative paths from the repository root.

2. Ensure the cache database is initialized. The worker module will do this automatically on first run.

3. (Optional) Set environment variables for configuration:
   - `CACHE_DB_PATH`: Path to the SQLite cache database (default: `./cache.db`)
   - `CACHE_TTL`: Time-to-live for cache entries in seconds (default: `86400`)
   - `MODEL_ENDPOINT`: The URL of the 35B model API (if not using the stub)

## Test Procedure

We will run two sets of queries:
   A. A set of unique queries (to measure baseline latency without cache hits).
   B. A set of recurring queries (to measure latency with cache hits).

We will use a simple script to time the execution of each query and record the results.

### Example Script: `run_benchmark.sh`

We provide an example script below. This script is for illustration and must be adapted to your specific
model API and environment. The script does not execute automatically; you must run it manually.

Note: Replace the placeholder for the model API call with the actual method to invoke your 35B model.

```bash
#!/bin/bash
# run_benchmark.sh - Example script to benchmark cache performance

# Set environment variables (adjust as needed)
export CACHE_DB_PATH="./cache.db"
export CACHE_TTL="86400"
# If using a real model endpoint, set it here. Otherwise, the worker stub will be used.
# export MODEL_ENDPOINT="http://localhost:8090/completion"

# Number of unique queries to run in the first set
UNIQUE_QUERIES_COUNT=5
# Number of recurring queries to run in the second set (should be less than or equal to unique ones for cache hits)
RECURRING_QUERIES_COUNT=3

# Define test queries (feel free to modify)
declare -a UNIQUE_QUERIES=(
  "Controlla la posta elettronica per spam"
  "Qual è il meteo oggi?"
  "Trova i file modificati la scorsa settimana"
  "Calcola il totale delle spese del mese"
  "Invia un promemoria per la riunione di domani"
)

# For the recurring set, we'll use the first few queries from the unique set to ensure cache hits
declare -a RECURRING_QUERIES=(
  "Controlla la posta elettronica per spam"
  "Qual è il meteo oggi?"
  "Trova i file modificati la scorsa settimana"
)

# Function to run a single query and measure time
run_query() {
  local query="$1"
  local context="$2"  # Optional context as JSON string
  local start_time
  start_time=$(date +%s%N)  # Nanoseconds since epoch

  # Call the worker module to process the query.
  # In a real scenario, this would be a function call to your worker that uses the cache.
  # For this example, we assume there is a Python script that can process a query and return the plan.
  # We'll use the worker.py module directly.

  # Note: Adjust the way you call the worker according to your integration.
  # Here, we are using the worker's process_query function via a Python one-liner.
  # This is just an example; you may have a different interface.

  # Example using the worker module (if it's set up to be called as a module):
  # python3 -c "
  # import sys
  # sys.path.append('src')
  # from worker import process_query
  # import json
  # result = process_query('$query', ${context:-{}})
  # print(json.dumps(result))
  # "

  # For the purpose of this example, we'll simulate a delay to represent model inference.
  # In a real test, you would replace the sleep with the actual model call.
  sleep 2  # Simulate 2 seconds of model inference (adjust as needed)

  local end_time
  end_time=$(date +%s%N)
  local duration_ms=$(( (end_time - start_time) / 1000000 ))
  echo "$duration_ms"
}

# Clear the cache database to start fresh (optional, but recommended for a clean test)
# Uncomment the following line if you want to reset the cache before each test.
# rm -f "$CACHE_DB_PATH"

echo "=== Running Unique Queries (No Cache Hits Expected) ==="
for query in "${UNIQUE_QUERIES[@]:0:$UNIQUE_QUERIES_COUNT}"; do
  echo -n "Query: $query -> "
  latency=$(run_query "$query" '{}')
  echo "Latency: ${latency}ms"
done

echo ""
echo "=== Running Recurring Queries (Cache Hits Expected) ==="
for query in "${RECURRING_QUERIES[@]:0:$RECURRING_QUERIES_COUNT}"; do
  echo -n "Query: $query -> "
  latency=$(run_query "$query" '{}')
  echo "Latency: ${latency}ms"
done

echo ""
echo "Note: This script uses a simulated delay. Replace the sleep command in run_query with"
echo "the actual model inference call to get real measurements."
```

### Instructions for Using the Script

1. Save the above script as `run_benchmark.sh` in the project root.
2. Make it executable: `chmod +x run_benchmark.sh`
3. Run the script: `./run_benchmark.sh`
4. Observe the latency measurements for each set of queries.

### Expected Results

- The first set (unique queries) should show higher latency (simulated or real model inference time).
- The second set (recurring queries) should show significantly lower latency if the cache is working
  (because the plan is retrieved from cache instead of regenerating it).

### Recording Results

Create a table to record the latency for each query in both sets. Example:

| Query Set | Query | Latency (ms) | Notes (Cache Hit/Miss) |
|-----------|-------|--------------|------------------------|
| Unique    | ...   | ...          | Miss (expected)        |
| Recurring | ...   | ...          | Hit (expected)         |

### Cleanup

After the test, you may want to remove the cache database to start fresh for future tests:
   rm -f ./cache.db

### Troubleshooting

- If you encounter errors, ensure that the worker and cache modules are correctly imported and
  that the Python environment has the necessary dependencies (sqlite3 is standard, but check for any others).
- Verify that the 35B model is running and accessible if you are not using the stub.

### Notes

- This test is manual and intended for validation purposes. For automated benchmarking, consider
  integrating with a proper testing framework.
- The script provided is a starting point and should be adapted to your specific setup and requirements.
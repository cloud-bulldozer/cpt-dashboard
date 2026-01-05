#!/bin/bash
#
# Run the backend and frontend locally in a mode where saving changes will
# immediately update the running instances. This is useful for active
# development.
#
# Usage:
#   ./run-local.sh
#
# Need:
# - Users will need to update the backend/ocpperf.toml file to meet their needs.
#
# TBD:
# - Add a way to automatically configure the functional test OpenSearch database
#   snapshots with the appropriate ocpperf.toml file, which may be useful for
#   testing.
#
# Assisted-by: Cursor AI
TOP=$(git rev-parse --show-toplevel)
BACKEND=${TOP}/backend
FRONTEND=${TOP}/frontend
CPT_CONFIG=${CPT_CONFIG:-"${BACKEND}/ocpperf.toml"}
if [ ! -f "${CPT_CONFIG}" ]; then
    echo "Error: ${CPT_CONFIG} not found" >&2
    echo "Please update the ${CPT_CONFIG} file to meet your needs." >&2
    exit 1
fi

# Make sure all dependencies are installed.
temp_file=$(mktemp)
echo "Installing dependencies... (${temp_file})"
(
    cd "${BACKEND}"
    poetry install
    cd "${FRONTEND}"
    npm install
) > "${temp_file}" 2>&1

if [ $? -ne 0 ]; then
    echo "Error: failed to install dependencies" >&2
    cat "${temp_file}" >&2
    rm "${temp_file}"
    exit 1
fi

# start the backend
echo "Starting backend..."
(
    cd ${BACKEND}
    poetry run scripts/start-reload.sh
) &
backend_pid=$!

# start the frontend
echo "Starting frontend..."
(
    cd ${FRONTEND}
    npm run dev
) &
frontend_pid=$!

# Killing the subshells won't kill all child processes, so grab their process
# group IDs and use those instead. They're likely in the same PGID; but check
# both to be sure.
b_pgid=$(ps -o pgid= -p ${backend_pid})
f_pgid=$(ps -o pgid= -p ${frontend_pid})

# Remove spaces from "ps -o" output
backend_pgid=${b_pgid//[[:space:]]/}
frontend_pgid=${f_pgid//[[:space:]]/}

to_kill="-${backend_pgid}"
if [[ ${frontend_pgid} -ne ${backend_pgid} ]]; then
    to_kill="${to_kill} -${frontend_pgid}"
fi

# Let frontend and backend start up and write their output before we finish,
# or our helpful note will be lost.
waiting=0
while ! curl -s http://localhost:8000/ > /dev/null 2>&1; do
    if [ ${waiting} -eq 0 ]; then
        echo "Waiting for backend to start..."
    fi
    sleep 1
    waiting=$((waiting + 1))
    if [ ${waiting} -gt 10 ]; then
        echo "Error: backend didn't start in time" >&2
        exit 1
    fi
done
waiting=0
while ! curl -s http://localhost:3000/ > /dev/null 2>&1; do
    if [ ${waiting} -eq 0 ]; then
        echo "Waiting for frontend to start..."
    fi
    sleep 1
    waiting=$((waiting + 1))
    if [ ${waiting} -gt 10 ]; then
        echo "Error: frontend didn't start in time" >&2
        exit 1
    fi
done

echo ""
echo "--------------------------------"
echo "CPT Backend is running in the background at http://localhost:8000"
echo "CPT Frontend is running in the background at http://localhost:3000"
echo ""
echo "To terminate, run:"
echo "  kill -- ${to_kill}"
echo ""
echo "HINT: capture this in an alias for later:"
echo "  alias kill-cpt=\"kill -- ${to_kill}\""
echo "and then you can terminate with 'kill-cpt'"
echo ""

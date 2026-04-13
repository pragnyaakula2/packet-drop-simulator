#!/bin/bash
# ──────────────────────────────────────────────────────────────
# Packet Drop Simulator — Quick Start
# Usage: bash run_sim.sh
# ──────────────────────────────────────────────────────────────

POX_DIR="$HOME/pox"   # ← Change this to your POX directory
TOPO_SCRIPT="$(dirname "$0")/topology.py"
CONTROLLER="drop_controller"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║      PACKET DROP SIMULATOR (POX)         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── Step 1: Start POX controller in background ────────────────
echo "[1/3] Starting POX controller..."
cd "$POX_DIR" || { echo "ERROR: POX dir not found at $POX_DIR"; exit 1; }

# Kill any existing POX
pkill -f "pox.py" 2>/dev/null
sleep 1

./pox.py log.level --DEBUG $CONTROLLER &
POX_PID=$!
echo "    POX started (PID $POX_PID)"
sleep 2   # Give POX time to bind to port 6633

# ── Step 2: Start Mininet ──────────────────────────────────────
echo "[2/3] Starting Mininet topology..."
echo "    (You'll get a Mininet CLI — run tests there)"
echo ""
echo "    In the Mininet CLI, try:"
echo "      h1 ping h3 -c 10   # Should show ~100% loss (drop rule)"
echo "      h1 ping h2 -c 10   # Should pass normally"
echo "      py exec(open('/path/to/measure_and_test.py').read())"
echo "      py run_all_measurements(net)"
echo ""

sudo python3 "$TOPO_SCRIPT"

# ── Step 3: After Mininet exits, run regression tests ─────────
echo ""
echo "[3/3] Running regression tests on flow table..."
python3 "$(dirname "$0")/measure_and_test.py" s1

# Cleanup
echo ""
echo "Killing POX (PID $POX_PID)..."
kill $POX_PID 2>/dev/null
echo "Done."

"""
Packet Drop Simulator - Measurement & Regression Tests
Run INSIDE Mininet CLI:  py exec(open('/path/to/measure_and_test.py').read())
Or run externally after importing net.

Also works standalone to query OVS flow tables via subprocess.
"""

import subprocess
import re
import sys
import json
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# 1. PACKET LOSS MEASUREMENT  (run from Mininet CLI or script)
# ──────────────────────────────────────────────────────────────

def measure_packet_loss(net, src_name, dst_name, count=20):
    """
    Send `count` pings from src to dst and measure packet loss.
    Returns dict with loss%, sent, received.
    """
    src = net.get(src_name)
    dst = net.get(dst_name)
    dst_ip = dst.IP()

    result = src.cmd(f"ping -c {count} -W 1 {dst_ip}")
    print(f"\n[PING] {src_name} → {dst_name} ({dst_ip})")
    print(result)

    # Parse loss percentage
    match = re.search(r"(\d+)% packet loss", result)
    loss = int(match.group(1)) if match else -1

    # Parse sent/received
    match2 = re.search(r"(\d+) packets transmitted, (\d+) received", result)
    sent = int(match2.group(1)) if match2 else count
    received = int(match2.group(2)) if match2 else 0

    return {
        "src": src_name, "dst": dst_name,
        "sent": sent, "received": received,
        "loss_pct": loss,
        "expected_drop": loss > 50,   # True if mostly dropped
    }


def run_all_measurements(net):
    """
    Run measurements for all relevant flows.
    Adjust the pairs below to match your drop rules.
    """
    test_pairs = [
        # (src, dst, should_be_dropped)
        ("h1", "h3", True),    # Drop rule installed
        ("h2", "h4", True),    # Drop rule installed (ICMP)
        ("h1", "h2", False),   # No drop rule — should pass
        ("h3", "h4", False),   # No drop rule — should pass
    ]

    results = []
    for src, dst, expect_drop in test_pairs:
        r = measure_packet_loss(net, src, dst, count=20)
        r["expect_drop"] = expect_drop
        r["pass"] = (r["expected_drop"] == expect_drop)
        results.append(r)

    _print_results_table(results)
    return results


def _print_results_table(results):
    print("\n" + "═" * 65)
    print(f"{'FLOW':<15} {'SENT':>5} {'RCVD':>5} {'LOSS%':>7} "
          f"{'EXPECTED':>10} {'STATUS':>8}")
    print("─" * 65)
    for r in results:
        flow = f"{r['src']}→{r['dst']}"
        expected = "DROP" if r["expect_drop"] else "PASS"
        status = "✓ PASS" if r["pass"] else "✗ FAIL"
        print(f"{flow:<15} {r['sent']:>5} {r['received']:>5} "
              f"{r['loss_pct']:>6}%  {expected:>10} {status:>8}")
    print("═" * 65)


# ──────────────────────────────────────────────────────────────
# 2. FLOW TABLE INSPECTION  (uses ovs-ofctl, run as root)
# ──────────────────────────────────────────────────────────────

def get_flow_table(switch="s1"):
    """Dump flow table from OVS switch using ovs-ofctl."""
    cmd = ["sudo", "ovs-ofctl", "dump-flows", switch]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] Could not dump flows: {result.stderr}")
        return []
    return result.stdout.strip().split("\n")


def parse_drop_rules(flow_lines):
    """Extract rules with no actions (= drop rules)."""
    drop_rules = []
    for line in flow_lines:
        # Drop rules have no actions= field, or actions=drop
        if "actions=drop" in line or (
            "actions=" not in line and "REPLY" not in line
        ):
            drop_rules.append(line.strip())
    return drop_rules


def print_flow_table(switch="s1"):
    """Pretty-print the flow table."""
    flows = get_flow_table(switch)
    drop_rules = parse_drop_rules(flows)

    print(f"\n{'═'*65}")
    print(f" FLOW TABLE: {switch}")
    print(f"{'─'*65}")
    for i, line in enumerate(flows):
        tag = " [DROP]" if line in drop_rules else ""
        print(f"  {i+1:02d}. {line}{tag}")
    print(f"{'═'*65}")
    print(f"  Total flows: {len(flows)}  |  Drop rules: {len(drop_rules)}")


# ──────────────────────────────────────────────────────────────
# 3. REGRESSION TESTS — Verify drop rules persist correctly
# ──────────────────────────────────────────────────────────────

EXPECTED_DROP_SIGNATURES = [
    # These substrings must appear in at least one flow entry
    {"match": "nw_src=10.0.0.1,nw_dst=10.0.0.3", "desc": "h1→h3 drop rule"},
    {"match": "nw_src=10.0.0.2,nw_dst=10.0.0.4", "desc": "h2→h4 ICMP drop rule"},
]


def regression_test_flow_persistence(switch="s1"):
    """
    Regression test: verify that expected drop rules are still in
    the flow table after some time has passed (rules haven't expired).
    """
    print("\n" + "═" * 65)
    print(" REGRESSION TEST: Drop Rule Persistence")
    print("─" * 65)

    flows = get_flow_table(switch)
    flow_text = "\n".join(flows)

    passed = 0
    failed = 0
    results = []

    for sig in EXPECTED_DROP_SIGNATURES:
        found = sig["match"] in flow_text
        status = "✓ FOUND" if found else "✗ MISSING"
        if found:
            passed += 1
        else:
            failed += 1
        results.append({"desc": sig["desc"], "found": found})
        print(f"  {status}  — {sig['desc']}")
        print(f"           Looking for: {sig['match']}")

    print("─" * 65)
    print(f"  Result: {passed} passed, {failed} failed")
    print("═" * 65)

    return failed == 0


def regression_test_default_forward_exists(switch="s1"):
    """Verify the default flood/forward rule is still present."""
    flows = get_flow_table(switch)
    for line in flows:
        if "priority=1" in line and ("FLOOD" in line or "flood" in line or "ALL" in line):
            print("\n[REGRESSION] ✓ Default forward rule present")
            return True
    print("\n[REGRESSION] ✗ Default forward rule MISSING!")
    return False


def run_all_regression_tests(switch="s1"):
    """Run all regression tests and return overall pass/fail."""
    print(f"\n{'='*65}")
    print(f" RUNNING ALL REGRESSION TESTS  [{datetime.now().strftime('%H:%M:%S')}]")
    print(f"{'='*65}")

    r1 = regression_test_flow_persistence(switch)
    r2 = regression_test_default_forward_exists(switch)

    overall = r1 and r2
    status = "ALL TESTS PASSED ✓" if overall else "SOME TESTS FAILED ✗"
    print(f"\n{'='*65}")
    print(f"  OVERALL: {status}")
    print(f"{'='*65}\n")
    return overall


# ──────────────────────────────────────────────────────────────
# 4. SAVE RESULTS TO JSON
# ──────────────────────────────────────────────────────────────

def save_results(results, filename="drop_sim_results.json"):
    data = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n[SAVED] Results written to {filename}")


# ──────────────────────────────────────────────────────────────
# STANDALONE: just inspect flow table + run regression tests
# (no Mininet net object needed)
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    switch = sys.argv[1] if len(sys.argv) > 1 else "s1"
    print_flow_table(switch)
    run_all_regression_tests(switch)

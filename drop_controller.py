"""
Packet Drop Simulator - POX Controller
Place this file in: pox/ext/drop_controller.py
Run with: ./pox.py drop_controller
"""

from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import IPAddr, EthAddr

log = core.getLogger()

# ──────────────────────────────────────────────
# DROP RULES CONFIGURATION
# Edit this dict to define which flows to drop.
# Keys are (src_ip, dst_ip) tuples; None = wildcard
# ──────────────────────────────────────────────
DROP_RULES = [
    {
        "description": "Drop all traffic from h1 to h3",
        "src_ip": "10.0.0.1",
        "dst_ip": "10.0.0.3",
        "priority": 100,
    },
    {
        "description": "Drop ICMP from h2 to h4",
        "src_ip": "10.0.0.2",
        "dst_ip": "10.0.0.4",
        "nw_proto": 1,          # 1 = ICMP, 6 = TCP, 17 = UDP
        "priority": 110,
    },
]

# Track installed rules per switch for regression testing
installed_rules = {}   # dpid -> list of rule dicts


class DropController(object):
    def __init__(self):
        core.openflow.addListeners(self)
        log.info("Drop Controller initialized. Waiting for switches...")

    # ── Switch connects ──────────────────────────────────────────────────
    def _handle_ConnectionUp(self, event):
        dpid = dpidToStr(event.dpid)
        log.info("Switch %s connected. Installing drop rules...", dpid)
        installed_rules[dpid] = []
        self._install_drop_rules(event.connection, dpid)

    # ── Install flow rules on the switch ────────────────────────────────
    def _install_drop_rules(self, connection, dpid):
        for rule in DROP_RULES:
            msg = of.ofp_flow_mod()
            msg.priority = rule.get("priority", 100)

            # Match on IP fields (ethertype = IPv4)
            msg.match.dl_type = 0x0800

            if rule.get("src_ip"):
                msg.match.nw_src = IPAddr(rule["src_ip"])
            if rule.get("dst_ip"):
                msg.match.nw_dst = IPAddr(rule["dst_ip"])
            if rule.get("nw_proto"):
                msg.match.nw_proto = rule["nw_proto"]

            # No actions = DROP
            # msg.actions is empty by default

            connection.send(msg)

            record = {
                "description": rule.get("description", "unnamed"),
                "src_ip": rule.get("src_ip"),
                "dst_ip": rule.get("dst_ip"),
                "nw_proto": rule.get("nw_proto"),
                "priority": msg.priority,
            }
            installed_rules[dpid].append(record)
            log.info("  [INSTALLED] %s", record["description"])

        # Default rule: forward everything else normally via flooding
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
        connection.send(msg)
        log.info("  [INSTALLED] Default flood rule (priority 1)")

    # ── PacketIn: log unexpected packets (should be rare) ───────────────
    def _handle_PacketIn(self, event):
        log.debug("PacketIn from switch %s (packet not matched by flow rules)",
                  dpidToStr(event.dpid))


def launch():
    core.registerNew(DropController)
    log.info("Drop Controller loaded. Drop rules: %d", len(DROP_RULES))

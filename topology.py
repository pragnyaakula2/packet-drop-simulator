"""
Mininet Topology for Packet Drop Simulator
Run with: sudo python3 topology.py

Topology:
  h1 ─┐
  h2 ─┤── s1 ──── s2 ─┬── h3
  h4 ─┘               └── (more hosts)

4 hosts, 1 switch (expandable)
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class DropSimTopo(Topo):
    """Simple 4-host, 1-switch topology."""

    def build(self):
        # Add switch
        s1 = self.addSwitch("s1")

        # Add hosts
        h1 = self.addHost("h1", ip="10.0.0.1/24")
        h2 = self.addHost("h2", ip="10.0.0.2/24")
        h3 = self.addHost("h3", ip="10.0.0.3/24")
        h4 = self.addHost("h4", ip="10.0.0.4/24")

        # Links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(h4, s1)


def run():
    setLogLevel("info")
    topo = DropSimTopo()

    # Connect to POX running on localhost:6633
    net = Mininet(
        topo=topo,
        switch=OVSSwitch,
        controller=RemoteController("c0", ip="127.0.0.1", port=6633),
        autoSetMacs=True,
    )

    net.start()
    info("\n*** Topology started. Hosts: h1=10.0.0.1, h2=10.0.0.2, "
         "h3=10.0.0.3, h4=10.0.0.4\n")
    info("*** Type 'exit' to stop the network\n")
    CLI(net)
    net.stop()


if __name__ == "__main__":
    run()

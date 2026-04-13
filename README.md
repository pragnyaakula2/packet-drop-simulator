# Packet Drop Simulator using SDN (POX + Mininet)

## 📌 Overview

This project demonstrates a **Software Defined Networking (SDN)**-based packet filtering system using a **POX controller** and **Mininet**.
It allows selective dropping of network traffic based on predefined rules and validates behavior using automated testing.

---

## 🚀 Features

* Custom packet drop rules based on:

  * Source IP
  * Destination IP
  * Protocol (ICMP/TCP/UDP)
* Real-time rule installation using POX controller
* Simulated network using Mininet
* Packet loss measurement using ping
* Flow table inspection using OpenFlow
* Automated regression testing for rule validation

---

## 🧠 Project Structure

```
packet-drop-simulator/
│
├── run_sim.sh              # Script to automate full simulation
├── topology.py             # Mininet topology definition
├── measure_and_test.py     # Packet loss + regression testing
├── drop_controller.py      # POX controller logic
└── README.md
```

---

## ⚙️ Requirements

* Python 3.x
* Mininet
* POX Controller
* Open vSwitch (OVS)

> Note: POX officially supports Python 3.6–3.9, but may work on newer versions.

---

## 🛠️ Setup Instructions

### 1. Install Mininet

```bash
sudo apt update
sudo apt install mininet
```

### 2. Clone POX

```bash
git clone https://github.com/noxrepo/pox.git
cd pox
```

### 3. Place Controller File

Copy `drop_controller.py` into:

```
pox/ext/
```

---

## ▶️ Running the Simulation

From your project directory:

```bash
bash run_sim.sh
```

This will:

1. Start the POX controller
2. Launch the Mininet topology
3. Allow testing via CLI
4. Run regression tests after exit

---

## 🧪 Manual Testing (Mininet CLI)

Inside Mininet, run:

```bash
h1 ping h3 -c 10   # Expected: 100% packet loss (dropped)
h1 ping h2 -c 10   # Expected: Successful
h2 ping h4 -c 10   # Expected: ICMP dropped
```

---

## 📊 Automated Testing

Run inside Mininet:

```bash
py exec(open('measure_and_test.py').read())
py run_all_measurements(net)
```

After exiting Mininet, regression tests run automatically:

* Verifies drop rules exist
* Confirms default forwarding rule
* Checks flow persistence

---

## 🔥 Drop Rules Configuration

Defined in `drop_controller.py`:

```python
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
        "nw_proto": 1,
        "priority": 110,
    },
]
```

---

## 🧠 Key Concepts Demonstrated

* Software Defined Networking (SDN)
* Separation of Control Plane and Data Plane
* OpenFlow Protocol
* Flow Table Management
* Network Traffic Filtering

---

## ✅ Expected Output

* Selected flows experience **100% packet loss**
* Other flows are forwarded normally
* Flow table shows installed drop rules
* Regression tests pass successfully

---

## 📌 Conclusion

This project demonstrates how SDN controllers can dynamically manage network behavior by installing flow rules, enabling flexible and programmable network control.

---

## 👩‍💻 Author

Pragnya Akula

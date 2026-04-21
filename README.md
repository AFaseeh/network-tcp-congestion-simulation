# TCP Congestion Control Simulation
### Reno vs CUBIC

A live network simulation using **Mininet** that demonstrates and compares TCP Reno and TCP CUBIC congestion control algorithms. Real kernel TCP behavior is captured via `ss` and plotted using matplotlib.

---

## Topology

```
h2 (Sender) ──── s1 (Switch) ──── h1 (Server/Receiver)
  no loss                        loss applied here only

RTT = 4 × single link delay
BDP = bandwidth × RTT / 8  (bytes)
```

---

## Requirements

```bash
# System dependencies
sudo apt install mininet iperf3 ethtool python3-pip

# Python dependencies (inside your venv)
pip install matplotlib mininet

# Run with sudo using your venv's python
sudo $(which python3) network_simulation.py
```

> **Note:** Must be run with `sudo` — Mininet requires root to create virtual interfaces.
> If using a virtual environment: `sudo $(which python3) network_simulation.py`

---

## Usage

```bash
sudo $(which python3) network_simulation.py
```

You will be prompted for:
```
Algorithm (reno, cubic): reno
Enter wanted RTT (ms): 100
Enter bandwidth (Mbps): 100
Packet loss %: 0.01
```

Output: a `cwnd_reno.png` or `cwnd_cubic.png` graph saved in the current directory.

---

## Project Structure

```
.
├── network_simulation.py          # Mininet simulation script
├── README.md
├── cwnd_reno.png    # Generated after running Reno
├── cwnd_cubic.png   # Generated after running Cubic
├── d1.py
└── d2.py
```
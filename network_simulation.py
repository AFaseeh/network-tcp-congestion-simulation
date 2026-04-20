import threading
import time
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.topo import Topo
from mininet.node import OVSBridge
import matplotlib.pyplot as plt

class networkTopo(Topo):
    def build(self, bw, delay, loss):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1', cls=OVSBridge)
        delay_str = f"{delay}ms"
        self.addLink(h1, s1, bw=bw, delay=delay_str, loss=loss)
        self.addLink(h2, s1, bw=bw, delay=delay_str, loss=0)

def configure_host(host, algo, max_buf):
    iface = f"{host.name}-eth0"
    # Disable NIC offloading features to show TCP
    host.cmd(f'ethtool -K {iface} tso off gso off gro off lro off')

    host.cmd(f'sysctl -w net.ipv4.tcp_rmem="4096 87380 {max_buf}"')
    host.cmd(f'sysctl -w net.ipv4.tcp_wmem="4096 87380 {max_buf}"')
    host.cmd(f'sysctl -w net.core.rmem_max={max_buf}')
    host.cmd(f'sysctl -w net.core.wmem_max={max_buf}')
    host.cmd(f'sysctl -w net.ipv4.tcp_congestion_control={algo}')

def capture_cwnd(host, server_ip, duration, results, stop_event):
    """
    Poll ss (Socket Statistics) every 50ms on the sender (h2).
    ss -tin dst <server_ip> gives per-socket TCP info including cwnd.
    """
    start = time.time()
    while not stop_event.is_set() and (time.time() - start) < duration:
        out = host.cmd(f'ss -tin dst {server_ip}')
        timestamp = time.time() - start

        current_cwnds = []
        for line in out.splitlines():
            if 'cwnd' in line:
                try:
                    # parse cwnd value (in segments/MSS)
                    cwnd_mss = int(line.split('cwnd:')[1].split()[0])
                    cwnd_bytes = cwnd_mss * 1460  # MSS = 1460 bytes
                    current_cwnds.append(cwnd_bytes)
                    if 'mss:' in line:
                        try:
                            print("MSS: " + int(line.split('mss:')[1].split()[0]))
                        except:
                            pass
                except (IndexError, ValueError):
                    pass
        
        if current_cwnds:
            results.append((timestamp, max(current_cwnds)))

        time.sleep(0.02)

def plot_cwnd(results, algo, bw, rtt_ms, loss):
    if not results:
        print("No cwnd data captured!")
        return

    times = [r[0] for r in results]
    cwnds = [r[1] / 1024 for r in results]  # convert to KB

    plt.figure(figsize=(14, 6))
    plt.plot(times, cwnds, 'b-', linewidth=1, label='cwnd')

    # Mark drops (where cwnd decreases)
    for i in range(1, len(cwnds)):
        if cwnds[i] < cwnds[i-1] * 0.9:  # >10% drop
            plt.axvline(x=times[i], color='red', alpha=0.3, linewidth=0.8)

    plt.xlabel('Time (s)')
    plt.ylabel('cwnd (KB)')
    plt.title(f'TCP {algo.upper()} — cwnd over time\n'
              f'{bw}Mbps | {rtt_ms}ms RTT | {loss}% Loss')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    filename = f'cwnd_{algo}.png'
    plt.savefig(filename, dpi=150)
    print(f"Plot saved: {filename}")
    plt.show()

def demo(algo, delay, loss, bw):
    setLogLevel('info')

    rtt_ms    = delay * 4
    bdp_bytes = int((bw * 1e6) * (rtt_ms / 1000) / 8)
    max_buf   = bdp_bytes * 4
    duration  = 20

    print(f"\nAlgorithm : {algo}")
    print(f"Network   : {bw}Mbps | {rtt_ms}ms RTT | {loss}% Loss")
    print(f"BDP       : {bdp_bytes//1024} KB")
    print(f"Buffer cap: {max_buf//1024} KB")

    topo = networkTopo(bw=bw, delay=delay, loss=loss)
    net  = Mininet(topo=topo, controller=None, link=TCLink)
    net.start()

    h1, h2 = net.get('h1', 'h2')

    configure_host(h1, algo, max_buf)
    configure_host(h2, algo, max_buf)

    actual = h2.cmd('sysctl -n net.ipv4.tcp_congestion_control').strip()
    print(f"Confirmed algo on h2: {actual}")

    net.pingAll()

    # Start iperf server on h1
    server = h1.popen('iperf3 -s')
    time.sleep(0.5)  # let server start

    # Start iperf client on h2
    client = h2.popen(f'iperf3 -c {h1.IP()} -t {duration} -C {algo} -M 1460 --forceflush')
    time.sleep(0.5)

    # Start ss capture in background thread
    cwnd_data  = []
    stop_event = threading.Event()
    poller     = threading.Thread(
        target=capture_cwnd,
        args=(h2, h1.IP(), duration, cwnd_data, stop_event)
    )
    poller.start()

    print("\n--- iperf3 output ---")
    for line in client.stdout:
        print(line.decode('utf-8'), end='', flush=True)

    stop_event.set()
    poller.join()

    server.terminate()
    net.stop()

    print(f"\nCaptured {len(cwnd_data)} cwnd samples")
    plot_cwnd(cwnd_data, algo, bw, rtt_ms, loss)

if __name__ == '__main__':
    algo      = input("Algorithm (reno, cubic): ").strip()
    rtt       = float(input("Enter wanted RTT (ms): "))
    bandwidth = int(input("Enter bandwidth (Mbps): "))
    loss      = float(input("Packet loss %: ").strip())
    demo(algo, rtt/4, loss, bandwidth)
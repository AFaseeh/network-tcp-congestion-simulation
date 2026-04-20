import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def simulate_tcp_friendly(total_rounds=2000, loss_interval=200, c_cubic=0.4, rtt_sec=0.1):
    reno_cwnd = []
    cubic_pure = []
    cubic_friendly = []
    
    beta_reno = 0.5
    beta_cubic = 0.7
    
    # Starting state
    w_max = 200.0 
    r_cwnd = w_max * beta_reno
    c_cwnd = w_max * beta_cubic
    
    k = np.cbrt((w_max * (1.0 - beta_cubic)) / c_cubic)
    t_since_loss_sec = 0.0
    
    for i in range(total_rounds):
        if i > 0 and i % int(loss_interval) == 0:
            w_max = c_cwnd
            r_cwnd = max(r_cwnd * beta_reno, 10.0)
            c_cwnd = max(c_cwnd * beta_cubic, 10.0)
            k = np.cbrt((w_max * (1.0 - beta_cubic)) / c_cubic)
            t_since_loss_sec = 0.0
        else:
            t_since_loss_sec += rtt_sec
            
            # 1. Standard Reno (+1 per round)
            r_cwnd += 1.0 
            
            # 2. Pure Cubic Math
            target_cubic = c_cubic * ((t_since_loss_sec - k)**3) + w_max
            
            # 3. Reno-Friendly Calculation (RFC 9438)
            # This approximates how Reno would grow from the same starting point
            reno_estimate = w_max * beta_cubic + (3 * (1-beta_cubic)/(1+beta_cubic)) * (t_since_loss_sec / rtt_sec)
            
            # Use the max of the two
            friendly_cwnd = max(target_cubic, reno_estimate)
            c_cwnd = friendly_cwnd # This updates the "real" window for next iteration
                
        reno_cwnd.append(r_cwnd)
        cubic_pure.append(target_cubic)
        cubic_friendly.append(c_cwnd)
        
    return reno_cwnd, cubic_pure, cubic_friendly

# --- Plot Setup ---
fig, ax = plt.subplots(figsize=(12, 8))
plt.subplots_adjust(bottom=0.25)

time_axis = np.arange(2000)
reno, pure, friendly = simulate_tcp_friendly()

line_reno, = ax.plot(time_axis, reno, 'b--', label="Actual Reno", alpha=0.3)
line_pure, = ax.plot(time_axis, pure, 'g:', label="Pure Cubic (No Friendly Mode)")
line_friend, = ax.plot(time_axis, friendly, 'r', label="CUBIC with Friendly Mode", linewidth=2)

ax.set_title("Simulating the TCP-Friendly Region")
ax.legend()
ax.set_ylim(0, 2000)

ax_rtt = plt.axes([0.15, 0.1, 0.65, 0.03])
s_rtt = Slider(ax_rtt, 'RTT (s)', 0.01, 1.0, valinit=0.1)

def update(val):
    r, p, f = simulate_tcp_friendly(rtt_sec=s_rtt.val)
    line_reno.set_ydata(r)
    line_pure.set_ydata(p)
    line_friend.set_ydata(f)
    ax.set_ylim(0, max(max(f), max(r)) * 1.1)
    fig.canvas.draw_idle()

s_rtt.on_changed(update)
plt.show()
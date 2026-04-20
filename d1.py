import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# --- Simulation Function ---
def simulate_tcp(total_rounds=2000, loss_interval=200, c_cubic=0.4, rtt_sec=0.1):
    reno_cwnd = []
    cubic_cwnd = []
    
    beta_reno = 0.5
    beta_cubic = 0.7
    
    w_max = 200.0 
    r_cwnd = w_max * beta_reno
    c_cwnd = w_max * beta_cubic
    
    # K is the time to reach W_max plateau
    k = np.cbrt((w_max * (1.0 - beta_cubic)) / c_cubic)
    t_since_loss_sec = 0.0
    
    for i in range(total_rounds):
        if i > 0 and i % int(loss_interval) == 0:
            # RESET ON LOSS
            w_max = c_cwnd
            r_cwnd = max(r_cwnd * beta_reno, 10.0)
            c_cwnd = max(c_cwnd * beta_cubic, 10.0)
            
            k = np.cbrt((w_max * (1.0 - beta_cubic)) / c_cubic)
            t_since_loss_sec = 0.0
        else:
            # GROWTH PHASE
            t_since_loss_sec += rtt_sec
            
            # 1. Standard Reno (Pure linear growth for comparison)
            r_cwnd += 1.0 
            
            # 2. Pure Cubic Math
            target_cubic = c_cubic * ((t_since_loss_sec - k)**3) + w_max
            
            # 3. Reno-Friendly Region Calculation
            # This approximates the window size of a standard TCP Reno 
            # starting from the same post-loss window.
            reno_friendly_estimate = w_max * beta_cubic + (3 * (1 - beta_cubic) / (1 + beta_cubic)) * (t_since_loss_sec / rtt_sec)
            
            # THE MERGE: CUBIC chooses the larger of the two to remain "friendly"
            c_cwnd = max(target_cubic, reno_friendly_estimate)
                
        reno_cwnd.append(r_cwnd)
        cubic_cwnd.append(c_cwnd)
        
    return reno_cwnd, cubic_cwnd

# --- Plot Setup ---
max_sim_rounds = 2000
initial_loss = 200
initial_c = 0.4
initial_rtt = 0.1

fig, ax = plt.subplots(figsize=(12, 8))
plt.subplots_adjust(bottom=0.35)

time_axis = np.arange(max_sim_rounds)
reno_data, cubic_data = simulate_tcp(max_sim_rounds, initial_loss, initial_c, initial_rtt)

line_reno, = ax.plot(time_axis, reno_data, label="TCP Reno (RTT-Independent in rounds)", color="blue", alpha=0.5)
line_cubic, = ax.plot(time_axis, cubic_data, label="TCP CUBIC (Time-Dependent)", color="red", linewidth=2.5)

ax.set_title("Reno vs Cubic")
ax.set_xlabel("Rounds (Number of RTTs)")
ax.set_ylabel("Window Size")
ax.legend(loc='upper left')

ax.set_xlim(0, 1000)
ax.set_ylim(0, 5000)

# --- Sliders ---
ax_rtt = plt.axes([0.15, 0.15, 0.65, 0.03], facecolor='lightgrey')
ax_y   = plt.axes([0.15, 0.10, 0.65, 0.03], facecolor='lightgrey')
ax_loss = plt.axes([0.15, 0.20, 0.65, 0.03], facecolor='lightgrey')

s_rtt = Slider(ax_rtt, 'Round Time (s)', 0.01, 10.0, valinit=initial_rtt)
s_y   = Slider(ax_y, 'Vert Zoom', 500, 100000, valinit=5000)
s_loss = Slider(ax_loss, 'Loss Interval', 50, 1000, valinit=initial_loss)

def update(val):
    new_reno, new_cubic = simulate_tcp(max_sim_rounds, s_loss.val, 0.4, s_rtt.val)
    line_reno.set_ydata(new_reno)
    line_cubic.set_ydata(new_cubic)
    ax.set_ylim(0, s_y.val)
    fig.canvas.draw_idle()

s_rtt.on_changed(update)
s_y.on_changed(update)
s_loss.on_changed(update)

plt.show()
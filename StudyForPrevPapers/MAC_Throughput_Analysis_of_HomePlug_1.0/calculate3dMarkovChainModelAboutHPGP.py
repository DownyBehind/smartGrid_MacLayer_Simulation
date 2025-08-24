import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import eigs

# ------------------------------------------------------------
# Parameters (Table I, CA3/CA2 Priority)
# ------------------------------------------------------------
CW_values = {0: 7, 1: 15, 2: 15, 3: 31}     # Contention Window sizes
DC_values = {0: 0, 1: 1, 2: 3, 3: 15}       # Deferral Counter values
BPC_max = 3                                 # Max retransmission stage
N_nodes = 100                                 # Number of nodes

# ------------------------------------------------------------
# State space (BPC, DC, BC)
# ------------------------------------------------------------
states = []
state_index = {}
idx = 0
for i in range(BPC_max + 1):
    for j in range(DC_values[i] + 1):
        for k in range(CW_values[i] + 1):
            states.append((i, j, k))
            state_index[(i, j, k)] = idx
            idx += 1
N = len(states)

# ------------------------------------------------------------
# Transition matrix builder (depends on tau, p, pb)
# ------------------------------------------------------------
def build_transition_matrix(tau, p, pb):
    P = lil_matrix((N, N))

    for (i, j, k) in states:
        cur_idx = state_index[(i, j, k)]

        if k > 0:
            # Idle slot: BC-1 (prob 1-pb)
            nxt_idx = state_index[(i, j, k - 1)]
            P[cur_idx, nxt_idx] += (1 - pb)

            # Busy slot: BC-1, DC-1 (prob pb)
            if j > 0:
                nxt_idx = state_index[(i, j - 1, k - 1)]
                P[cur_idx, nxt_idx] += pb
            else:
                # DC=0 and busy → increase BPC
                nxt_i = min(BPC_max, i + 1)
                for new_k in range(CW_values[nxt_i] + 1):
                    nxt_idx = state_index[(nxt_i, DC_values[nxt_i], new_k)]
                    P[cur_idx, nxt_idx] += pb / (CW_values[nxt_i] + 1)

        else:
            # Transmission attempt (BC=0)
            # Success (1-p): reset to stage 0
            for new_k in range(CW_values[0] + 1):
                nxt_idx = state_index[(0, DC_values[0], new_k)]
                P[cur_idx, nxt_idx] += (1 - p) / (CW_values[0] + 1)

            # Collision (p): increase BPC
            nxt_i = min(BPC_max, i + 1)
            for new_k in range(CW_values[nxt_i] + 1):
                nxt_idx = state_index[(nxt_i, DC_values[nxt_i], new_k)]
                P[cur_idx, nxt_idx] += p / (CW_values[nxt_i] + 1)

    return P.tocsr()

# ------------------------------------------------------------
# Fixed-point iteration to solve for tau and p
# ------------------------------------------------------------
def solve_markov_chain(max_iter=50, tol=1e-6):
    tau = 0.1  # initial guess
    tau_history, p_history = [], []

    for _ in range(max_iter):
        p = 1 - (1 - tau) ** (N_nodes - 1)  # collision probability
        pb = 1 - (1 - tau) ** N_nodes       # busy probability

        # Build transition matrix
        P = build_transition_matrix(tau, p, pb)

        # Solve steady-state distribution: π = πP
        # Using power method to find dominant eigenvector of P^T
        vals, vecs = eigs(P.T, k=1, which='LM')
        pi = np.real(vecs[:, 0])
        pi = pi / np.sum(pi)

        # Compute new tau
        new_tau = sum(pi[state_index[(i, j, 0)]] for (i, j, k) in states if k == 0)

        tau_history.append(new_tau)
        p_history.append(p)

        if abs(new_tau - tau) < tol:
            tau = new_tau
            break

        tau = new_tau

    return pi, tau_history, p_history

# ------------------------------------------------------------
# Run solver
# ------------------------------------------------------------
pi, tau_history, p_history = solve_markov_chain()

# Save steady-state probabilities
df = pd.DataFrame(states, columns=["BPC", "DC", "BC"])
df["Probability"] = pi
df.to_csv("./homeplug_markov_exact.csv", index=False)

# Plot Tau and Collision probability convergence
plt.figure(figsize=(8, 5))
plt.plot(tau_history, marker="o", label="Tau (transmission probability)")
plt.plot(p_history, marker="s", label="p (collision probability)")
plt.title(f"Tau and Collision Probability Convergence (n={N_nodes}) - Exact")
plt.xlabel("Iteration")
plt.ylabel("Probability")
plt.legend()
plt.grid(True)
plt.show()

# HomePlug 1.0 Markov Chain Solver (Exact Numerical Method)

This project implements a **numerical solver** for the tri-dimensional discrete-time 
Markov chain model of HomePlug 1.0 MAC, based on Jung et al. (2005).

## 📊 Markov Chain States
The system state is represented as:
- `BPC` (Backoff Procedure Counter): retransmission stage
- `DC` (Deferral Counter): estimates number of competing stations
- `BC` (Backoff Counter): random backoff timer

State: (i, j, k) = (BPC=i, DC=j, BC=k)

## 📜 Transition Rules
1. Idle slot:  
   - `BC=BC-1` with probability (1-pb)
2. Busy slot:  
   - `BC=BC-1, DC=DC-1` with probability pb  
   - If DC=0 → `BPC=BPC+1, DC=M_BPC, BC∈U[0,W_BPC]`
3. Transmission (BC=0):  
   - Success with probability (1-p): reset to stage 0  
   - Failure with probability p: increase BPC
4. BPC maximum stage:  
   - If max stage reached, stay at max.

## 📐 Probabilities
- Busy probability:  
  `pb = 1 - (1 - τ)^n`
- Collision probability:  
  `p = 1 - (1 - τ)^(n-1)`
- Transmission probability:  
  `τ = Σ Σ P(i,j,0)`

  
## ⚙️ Exact Numerical Method
Unlike Monte Carlo approximation, we build the **full transition probability matrix** `P`:
- Each row corresponds to a state (i,j,k).
- Each entry gives the exact probability of moving to another state.

The steady-state distribution π satisfies:
    `π = πP , Σ π = 1`


We solve this using **power iteration / dominant eigenvector of P^T** 
(from `scipy.sparse.linalg.eigs`).

## 🚀 Outputs
- `homeplug_markov_exact.csv`: steady-state distribution for all (BPC,DC,BC).
- Convergence plot of:
  - τ (transmission probability)
  - p (collision probability)

## ✅ Notes
- This version gives the **exact steady-state solution** (up to numerical tolerance),
  not just a random approximation.
- Therefore, results are stable and reproducible.

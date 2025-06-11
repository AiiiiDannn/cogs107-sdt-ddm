# run_std_ddm.py

import numpy as np
import pymc as pm
import arviz as az
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import os
from sdt_ddm import read_data, draw_delta_plots
from sdt import new_apply_hierarchical_sdt_model, new2nd_apply_hierarchical_sdt_model

if __name__ == "__main__":

    ### 0. Data file path ###

    # Ensure the data file exists
    file_to_print = Path(__file__).parent / 'data.csv'
    if not file_to_print.exists():
        raise FileNotFoundError(f"File {file_to_print} does not exist. Please ensure the data file is in the correct location.")


    # Create directories for figures
    FIGURE_DIR = Path(__file__).parent / 'figures'
    SDT_DIR = FIGURE_DIR / 'sdt'
    DELTA_DIR = FIGURE_DIR / 'delta'

    # Make sure the directories exist
    SDT_DIR.mkdir(parents=True, exist_ok=True)
    DELTA_DIR.mkdir(parents=True, exist_ok=True)


    ### 1. Read the data ###
    data_sdt = read_data(file_to_print, prepare_for='sdt', display=True)
    data_delta = read_data(file_to_print, prepare_for='delta plots')
    
    ### 2. Run the adapted hierarchical SDT model ###
    model = new_apply_hierarchical_sdt_model(data_sdt)
    
    ### 3. Sampling ### 
    with model:
        print("\n\n=== Starting sampling ===")
        trace = pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.95, seed=6657, progressbar=True)
    

    ### 4. Convergence diagnostics, Plot Trace & Pair ###
    print("\n=== Convergence Diagnostics ===")
    summary = az.summary(trace, var_names=[
        'alpha_d_prime', 'beta_stim', 'beta_diff', 'beta_int',
        'alpha_criterion', 'gamma_stim', 'gamma_diff', 'gamma_int'
    ])
    print(summary)

    az.plot_trace(trace, var_names=[
        'alpha_d_prime', 'beta_stim', 'beta_diff', 'beta_int',
        'alpha_criterion', 'gamma_stim', 'gamma_diff', 'gamma_int'
    ])
    plt.savefig(SDT_DIR / "trace_plots.png")

    az.plot_pair(trace, var_names=[
        'alpha_d_prime', 'beta_stim', 'beta_diff', 'beta_int',
        'alpha_criterion', 'gamma_stim', 'gamma_diff', 'gamma_int'
    ], kind='kde')
    plt.savefig(SDT_DIR / "pair_plots.png")



    ### 5. Posterior visualization ###
    az.plot_posterior(trace, var_names=[
        'alpha_d_prime', 'beta_stim', 'beta_diff', 'beta_int',
        'alpha_criterion', 'gamma_stim', 'gamma_diff', 'gamma_int'
    ])
    plt.savefig(SDT_DIR / "posterior_distributions.png")


    ### 6. Generate Delta Plots for Diffusion Comparison ###
    print("\n\n=== Generating Delta Plots ===")
    for pnum in data_delta['pnum'].unique():
        draw_delta_plots(data_delta, pnum)

    ### 7. Compare Trial Difficulty vs Stimulus Type Effects (SDT Model) ###
    print("\n=== Effect Size Comparison ===")

    # Extract posterior samples
    stim_d = trace.posterior['beta_stim'].values.flatten()
    diff_d = trace.posterior['beta_diff'].values.flatten()
    stim_c = trace.posterior['gamma_stim'].values.flatten()
    diff_c = trace.posterior['gamma_diff'].values.flatten()

    # Print posterior means and std deviations
    print(f"d_prime (sensitivity):")
    print(f"  Stimulus effect = {stim_d.mean():.3f} ± {stim_d.std():.3f}")
    print(f"  Difficulty effect = {diff_d.mean():.3f} ± {diff_d.std():.3f}")
    
    print(f"c (decision criterion):")
    print(f"  Stimulus effect = {stim_c.mean():.3f} ± {stim_c.std():.3f}")
    print(f"  Difficulty effect = {diff_c.mean():.3f} ± {diff_c.std():.3f}")

    # Probability one effect is larger than the other
    p_stim_gt_diff_d = (np.abs(stim_d) > np.abs(diff_d)).mean()
    p_stim_gt_diff_c = (np.abs(stim_c) > np.abs(diff_c)).mean()

    print("\n=== Posterior Probabilities ===")
    print(f"P(|Stimulus effect| > |Difficulty effect|) for d′: {p_stim_gt_diff_d:.3f}")
    print(f"P(|Stimulus effect| > |Difficulty effect|) for criterion: {p_stim_gt_diff_c:.3f}")

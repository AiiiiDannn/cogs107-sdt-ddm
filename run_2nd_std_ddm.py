import pymc as pm
import arviz as az
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sdt_ddm import read_data
from sdt_update import new2nd_apply_hierarchical_sdt_model

if __name__ == "__main__":
    ### 1. Load Data ###
    file_path = Path(__file__).parent / 'data.csv'
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found at: {file_path}")

    FIGURE_DIR = Path(__file__).parent / 'figures'
    SDT_DIR = FIGURE_DIR / 'sdt'
    SDT_DIR.mkdir(parents=True, exist_ok=True)
        
    with open(file_path, 'r') as file_path:
        data_sdt = read_data(file_path, prepare_for='sdt', display=True)

        ### 2. Run Alternative Model ###
        print("\n\n=== One More Step: Evaluating Alternative SDT Model ===")
        model = new2nd_apply_hierarchical_sdt_model(data_sdt)

        with model:
            print("\n--- Sampling Alternative Model ---")
            trace = pm.sample(draws=2000, tune=1000, chains=4, target_accept=0.95, seed=6657, progressbar=True)

        ### 3. Convergence Diagnostics ###
        print("\n--- Convergence Diagnostics ---")
        summary = az.summary(trace, var_names=[
            'mu_alpha_int', 'beta_stim', 'beta_diff', 'beta_int',
            'mu_c_int', 'gamma_stim', 'gamma_diff', 'gamma_int'
        ])
        print(summary)

        ### 4. Posterior visualization ###
        az.plot_posterior(trace, var_names=[
            'mu_alpha_int', 'beta_stim', 'beta_diff', 'beta_int',
            'mu_c_int', 'gamma_stim', 'gamma_diff', 'gamma_int'
        ])
        plt.suptitle("Posterior Distributions for SDT Model Parameters (Alternative Model)")
        plt.tight_layout()
        plt.savefig(SDT_DIR / "new2nd_posterior_distributions.png")

        ### 5. Posterior Distribution Summary ###
        print("\n--- Posterior Summary ---")
        stim_d = trace.posterior['beta_stim'].values.flatten()
        diff_d = trace.posterior['beta_diff'].values.flatten()
        stim_c = trace.posterior['gamma_stim'].values.flatten()
        diff_c = trace.posterior['gamma_diff'].values.flatten()

        print(f"d′ (sensitivity):")
        print(f"  Stimulus effect = {stim_d.mean():.3f} ± {stim_d.std():.3f}")
        print(f"  Difficulty effect = {diff_d.mean():.3f} ± {diff_d.std():.3f}")

        print(f"c (decision criterion):")
        print(f"  Stimulus effect = {stim_c.mean():.3f} ± {stim_c.std():.3f}")
        print(f"  Difficulty effect = {diff_c.mean():.3f} ± {diff_c.std():.3f}")

        p_stim_gt_diff_d = (np.abs(stim_d) > np.abs(diff_d)).mean()
        p_stim_gt_diff_c = (np.abs(stim_c) > np.abs(diff_c)).mean()

        print("\n--- Posterior Probabilities ---")
        print(f"P(|Stimulus effect| > |Difficulty effect|) for d′: {p_stim_gt_diff_d:.3f}")
        print(f"P(|Stimulus effect| > |Difficulty effect|) for criterion: {p_stim_gt_diff_c:.3f}")

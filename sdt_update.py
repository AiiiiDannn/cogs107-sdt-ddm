import pymc as pm
import numpy as np

def new_apply_hierarchical_sdt_model(data):
    """
    Hierarchical SDT model with group-level condition-wise predictors and participant-level variation.
    Structure:
        - Group-level mean d' and criterion depend on Stimulus x Difficulty
        - Individual variation modeled over (P x C)
    """

    P = data["pnum"].nunique()
    C = data["condition"].nunique()

    idx_p = data["pnum"].values - 1
    idx_c = data["condition"].values

    stimulus = np.array([c % 2 for c in range(C)])
    difficulty = np.array([c // 2 for c in range(C)])
    interaction = stimulus * difficulty

    with pm.Model() as model:
        # === d' group-level===
        alpha_d_prime = pm.Normal("alpha_d_prime", mu=0, sigma=1)
        beta_stim = pm.Normal("beta_stim", mu=0, sigma=1)
        beta_diff = pm.Normal("beta_diff", mu=0, sigma=1)
        beta_int = pm.Normal("beta_int", mu=0, sigma=1)

        mu_d = (
            alpha_d_prime
            + beta_stim * stimulus
            + beta_diff * difficulty
            + beta_int * interaction
        )

        sigma_d = pm.HalfNormal("sigma_d", sigma=1)
        d_prime = pm.Normal("d_prime", mu=mu_d, sigma=sigma_d, shape=(P, C))

        # === criterion group-level===
        alpha_criterion = pm.Normal("alpha_criterion", mu=0, sigma=1)
        gamma_stim = pm.Normal("gamma_stim", mu=0, sigma=1)
        gamma_diff = pm.Normal("gamma_diff", mu=0, sigma=1)
        gamma_int = pm.Normal("gamma_int", mu=0, sigma=1)

        mu_c = (
            alpha_criterion
            + gamma_stim * stimulus
            + gamma_diff * difficulty
            + gamma_int * interaction
        )

        sigma_c = pm.HalfNormal("sigma_c", sigma=1)
        criterion = pm.Normal("criterion", mu=mu_c, sigma=sigma_c, shape=(P, C))

        # === Calculating hit and false alarm rates ===
        hit_rate = pm.math.invlogit(d_prime[idx_p, idx_c] - criterion[idx_p, idx_c])
        false_alarm_rate = pm.math.invlogit(-criterion[idx_p, idx_c])

        # === Likelihood functions ===
        pm.Binomial("hit_obs", n=data["nSignal"], p=hit_rate, observed=data["hits"])
        pm.Binomial("false_alarm_obs", n=data["nNoise"], p=false_alarm_rate, observed=data["false_alarms"])

    return model



def new2nd_apply_hierarchical_sdt_model(data):
    
    P = data['pnum'].nunique()  # number of participants
    C = data['condition'].nunique()  # number of conditions
    
    # Index preprocessing
    idx_p = data['pnum'].values - 1  # participant indices (0-based)
    idx_c = data['condition'].values  # condition indices
    
    # Trial-level condition variables
    difficulty = (data['condition'] // 2).values  # 0=easy, 1=hard
    stimulus = (data['condition'] % 2).values  # 0=simple, 1=complex
    interaction = stimulus * difficulty

    with pm.Model() as model:
        # === d' parameters ===
        mu_alpha_int = pm.Normal("mu_alpha_int", mu=0, sigma=1)
        beta_stim = pm.Normal("beta_stim", mu=0, sigma=1)
        beta_diff = pm.Normal("beta_diff", mu=0, sigma=1)
        beta_int = pm.Normal("beta_int", mu=0, sigma=1)
        
        # Participant-level random effects on d′
        sigma_d = pm.HalfNormal("sigma_d", sigma=1)
        alpha_p = pm.Normal("alpha_p", mu=0, sigma=1, shape=P)  # participant offset
        
        # Trial-level d′ values (structured)
        d_prime = (
            mu_alpha_int +
            beta_stim * stimulus +
            beta_diff * difficulty +
            beta_int * interaction +
            alpha_p[idx_p] * sigma_d  # participant-specific effect
        )

        # === criterion parameters ===
        mu_c_int = pm.Normal("mu_c_int", mu=0, sigma=1)
        gamma_stim = pm.Normal("gamma_stim", mu=0, sigma=1)
        gamma_diff = pm.Normal("gamma_diff", mu=0, sigma=1)
        gamma_int = pm.Normal("gamma_int", mu=0, sigma=1)
        
        # Participant-level random effects on criterion
        sigma_c = pm.HalfNormal("sigma_c", sigma=1)
        c_p = pm.Normal("c_p", mu=0, sigma=1, shape=P)  # participant offset
        
        # Trial-level criterion values (structured)
        criterion = (
            mu_c_int +
            gamma_stim * stimulus +
            gamma_diff * difficulty +
            gamma_int * interaction +
            c_p[idx_p] * sigma_c  # participant-specific effect
        )

        # === SDT probability computations ===
        hit_rate = pm.math.invlogit(d_prime - criterion)
        false_alarm_rate = pm.math.invlogit(-criterion)
        
        # === Likelihood ===
        pm.Binomial("hit_obs", 
                   n=data["nSignal"], 
                   p=hit_rate, 
                   observed=data["hits"])
        pm.Binomial("false_alarm_obs", 
                   n=data["nNoise"], 
                   p=false_alarm_rate, 
                   observed=data["false_alarms"])
    
    return model
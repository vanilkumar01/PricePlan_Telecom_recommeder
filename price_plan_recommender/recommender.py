import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

# OTT options
ott_options = ["Netflix", "Amazon Prime", "Disney+", "Spotify", "SonyLiv", "Hotstar"]

# Build feature matrix for plans
def build_feature_matrix(plans):
    rows = []
    for p in plans:
        row = [p["calls"], p["sms"], p["data"]]
        row += [1 if o in p["ott"] else 0 for o in ott_options]
        rows.append(row)
    return np.array(rows)

# Load plans from tp.xlsx
def prepare_plans():
    df = pd.read_excel("tp.xlsx")
    plans = []
    for _, row in df.iterrows():
        plans.append({
            "plan": row['PlanID'],
            "calls": row['IncludedMins'],
            "sms": row['SMScount'],
            "data": row['IncludedatainGB'],
            "price": row['MonthlyCost'],
            "ott": [x.strip() for x in str(row['OTT']).split(",")] if pd.notna(row['OTT']) and str(row['OTT']).lower() != 'none' else [],
            "description": row['PlanDescription']
        })
    return plans

# Recommend top 3 plans using Weighted Cosine Similarity
def recommend_top3(user_usage, ott_pref, plans):
    plan_features = build_feature_matrix(plans)
    scaler = StandardScaler()
    plan_features[:, :3] = scaler.fit_transform(plan_features[:, :3])

    user_vector = np.array(
        [user_usage['calls'], user_usage['sms'], user_usage['data']] +
        [1 if o in ott_pref else 0 for o in ott_options]
    ).reshape(1, -1)

    user_vector[:, :3] = scaler.transform(user_vector[:, :3])

    sims = cosine_similarity(user_vector, plan_features)[0]
    top_idx = sims.argsort()[::-1][:3]
    top3 = [plans[i] for i in top_idx]
    return top3

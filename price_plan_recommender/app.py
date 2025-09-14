from flask import Flask, render_template, request
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # prevent GUI issues
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

# ------------------------------
# Load Plans from Excel
# ------------------------------
df = pd.read_excel("tariff_plans.xlsx")
plans = []
for _, row in df.iterrows():
    plans.append({
        "plan": row['PlanID'],
        "calls": row['IncludedMins'],
        "sms": row['SMScount'],
        "data": row['IncludedatainGB'],
        "price": row['MonthlyCost'],
        "ott": [o.strip() for o in str(row['OTT']).split(",")] if row['OTT'] != 'None' else [],
        "description": row['PlanDescription']
    })

ott_options = ["Netflix basic", "Netflix premium", "Amazon Prime", "Disney+", "Spotify", "SonyLiv", "Hotstar"]

# ------------------------------
# Recommendation Function
# ------------------------------
def recommend_plans(user_calls, user_sms, user_data, user_ott, plans):
    max_calls = max(p['calls'] for p in plans)
    max_sms   = max(p['sms'] for p in plans)
    max_data  = max(p['data'] for p in plans)

    scored_plans = []

    for p in plans:
        score = (abs(user_calls - p['calls']) / max_calls +
                 abs(user_sms - p['sms']) / max_sms +
                 abs(user_data - p['data']) / max_data)

        # OTT matching bonus
        if user_ott:
            ott_match_count = sum(1 for o in user_ott if o in p['ott'])
            score -= 0.5 * ott_match_count

        scored_plans.append((score, p))

    scored_plans.sort(key=lambda x: x[0])
    top3 = [p for _, p in scored_plans[:3]]
    return top3

# ------------------------------
# Helper to render Matplotlib chart to base64
# ------------------------------
def plot_to_img(x_labels, y_values, title):
    fig, ax = plt.subplots(figsize=(4,3))

    # Define different colors
    colors = ["#f97316", "#2563eb", "#16a34a", "#db2777"]  # max 4 bars: User + 3 plans
    for i, (x, y) in enumerate(zip(x_labels, y_values)):
        ax.bar(x, y, color=colors[i % len(colors)], width=0.4)

    ax.set_title(title)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

# ------------------------------
# Flask Routes
# ------------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    user_calls = 0
    user_sms = 0
    user_data = 0
    user_ott = []

    recommendations = []
    charts = {}

    if request.method == 'POST':
        user_calls = int(request.form.get('calls',0))
        user_sms   = int(request.form.get('sms',0))
        user_data  = int(request.form.get('data',0))
        user_ott   = request.form.getlist('ott')

        # Get top 3 recommendations
        recommendations = recommend_plans(user_calls, user_sms, user_data, user_ott, plans)

        # Generate charts
        metrics = ['calls', 'sms', 'data']
        for m in metrics:
            x_labels = ['User'] + [str(p['plan']) for p in recommendations]
            y_values = [user_calls if m=='calls' else user_sms if m=='sms' else user_data] + \
                       [p[m] for p in recommendations]
            charts[m] = plot_to_img(x_labels, y_values, f"{m.capitalize()} Comparison")

    return render_template('index.html',
                           calls=user_calls,
                           sms=user_sms,
                           data=user_data,
                           ott_options=ott_options,
                           selected_ott=user_ott,
                           recommendations=recommendations,
                           charts=charts)

if __name__ == '__main__':
    app.run(debug=True)

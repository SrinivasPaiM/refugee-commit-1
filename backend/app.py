from flask import Flask, request, jsonify, render_template_string
from transformers import AutoTokenizer, AutoModel
import torch
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from flask_cors import CORS  # Import Flask-CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load model and tokenizer
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

# Load job data
with open("state.json", "r") as f:
    states_data = json.load(f)

all_jobs = []
job_to_state = []
for state, details in states_data.items():
    for job in details.get("in_demand_jobs", []):
        all_jobs.append(job)
        job_to_state.append(state)

# Predefined categories to help with matching
job_categories = {
    "Tech": ["Software Developer", "Web Developer", "Data Analyst", "IT Support", "Network Engineer"],
    "Healthcare": ["Nurse", "Healthcare Assistant", "Doctor", "Medical Technician"],
    "Construction": ["Construction Worker", "Carpenter", "Painter", "Plumber", "Electrician", "Welder"],
    "Service": ["Cook", "Tailor", "Driver", "Security Guard", "Watchman", "Salesman", "Cashier"],
    "Education": ["Teacher", "Tutor"],
    "Office": ["Accountant", "Clerk", "Data Entry", "Call Center Agent"],
    "Agriculture": ["Farmer"]
}

job_to_category = {
    job.lower(): category
    for category, jobs in job_categories.items()
    for job in jobs
}

def get_embeddings(texts):
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
    return mean_pool(outputs, inputs["attention_mask"])

def mean_pool(outputs, mask):
    tokens = outputs[0]
    mask = mask.unsqueeze(-1).expand(tokens.size()).float()
    return torch.sum(tokens * mask, 1) / torch.clamp(mask.sum(1), min=1e-9)

def calculate_job_similarity(job, experiences):
    texts = [job] + experiences
    embeddings = get_embeddings(texts)
    job_embed = embeddings[0].unsqueeze(0)
    exp_embeds = embeddings[1:]

    scores = cosine_similarity(job_embed.cpu(), exp_embeds.cpu())[0]
    best_score = float(np.max(scores))

    category_bonus = 0.0
    job_cat = job_to_category.get(job.lower())
    if job_cat:
        for exp in experiences:
            if job_to_category.get(exp.lower()) == job_cat:
                category_bonus = 0.2
                break

    skill_bonus = 0.0
    job_keywords = re.findall(r'\w+', job.lower())
    for exp in experiences:
        if any(keyword in exp.lower() for keyword in job_keywords):
            skill_bonus = 0.15
            break

    return min(best_score + category_bonus + skill_bonus, 1.0)

# Templates
form_html = """
<!DOCTYPE html>
<html>
<head><title>Job Match</title></head>
<body>
<h1>Find a Matching Job</h1>
<form method="post" action="/submit">
    <label>Enter your work experience (comma-separated):</label><br>
    <input type="text" name="experience" required><br><br>
    <button type="submit">Submit</button>
</form>
</body>
</html>
"""

result_html = """
<!DOCTYPE html>
<html>
<head><title>Results</title></head>
<body>
<h1>Results</h1>
<p><strong>Top Match:</strong> {{ matched_job }} in {{ matched_state }} (Score: {{ score }})</p>
<h2>Top Suggestions:</h2>
<ul>
{% for item in top_matches %}
    <li>{{ item.job }} in {{ item.state }} (Score: {{ item.score }})</li>
{% endfor %}
</ul>
<a href="/">Try Again</a>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(form_html)

@app.route('/submit', methods=['POST'])
def submit():
    raw_exp = request.form.get("experience", "")
    experiences = [e.strip() for e in raw_exp.split(",") if e.strip()]
    if not experiences:
        return "Please enter valid work experience.", 400

    scores = [calculate_job_similarity(job, experiences) for job in all_jobs]
    top_indices = np.argsort(scores)[::-1][:5]

    top_matches = [
        {"job": all_jobs[i], "state": job_to_state[i], "score": scores[i]}
        for i in top_indices
    ]

    return render_template_string(
        result_html,
        matched_job=top_matches[0]["job"],
        matched_state=top_matches[0]["state"],
        score=top_matches[0]["score"],
        top_matches=top_matches
    )

@app.route('/similarity', methods=['POST'])
def api_similarity():
    data = request.json
    experiences = data.get("user_experience", [])
    if not experiences:
        return jsonify({"error": "Missing experience data"}), 400

    scores = [calculate_job_similarity(job, experiences) for job in all_jobs]
    top_indices = np.argsort(scores)[::-1][:5]

    top_matches = [
        {"job": all_jobs[i], "state": job_to_state[i], "score": scores[i]}
        for i in top_indices
    ]

    return jsonify({
        "matched_job": top_matches[0]["job"],
        "matched_state": top_matches[0]["state"],
        "score": top_matches[0]["score"],
        "top_matches": top_matches
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME})

if __name__ == '__main__':
    print("Server running...")
    app.run(host="0.0.0.0", port=5000, debug=True)

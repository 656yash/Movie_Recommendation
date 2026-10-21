import os
import pickle
import requests
from flask import Flask, render_template, request

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask with explicit template and static folder paths for Vercel
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)

# 1. Load data
movies = pickle.load(open(os.path.join(BASE_DIR, 'model', 'movie_list.pkl'), 'rb'))
recommendations_data = pickle.load(open(os.path.join(BASE_DIR, 'model', 'recommendations.pkl'), 'rb'))

# 2. Fetch poster from OMDb
def fetch_poster(movie_title):
    try:
        url = f"http://www.omdbapi.com/?t={movie_title}&apikey=trilogy"
        response = requests.get(url, timeout=3)
        data = response.json()
        poster = data.get('Poster')
        if poster and poster != 'N/A' and poster.startswith('http'):
            return poster
    except Exception:
        pass
    return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"

# 3. Recommend function
def recommend(movie_name):
    recommended_movie_names = []
    recommended_movie_posters = []

    top_5 = recommendations_data[movie_name][:5]
    for item in top_5:
        title = item['title']
        recommended_movie_names.append(title)
        recommended_movie_posters.append(fetch_poster(title))

    return recommended_movie_names, recommended_movie_posters

# 4. Route (handles '/', '/api', '/api/index' so Vercel never 404s)
@app.route('/', methods=['GET', 'POST'])
@app.route('/api', methods=['GET', 'POST'])
@app.route('/api/index', methods=['GET', 'POST'])
@app.route('/api/index.py', methods=['GET', 'POST'])
def home():
    movie_list = sorted(movies['title'].values)
    recommended_movies = []
    selected_movie = None

    if request.method == 'POST':
        selected_movie = request.form.get('selected_movie')
        if selected_movie:
            names, posters = recommend(selected_movie)
            recommended_movies = list(zip(names, posters))

    return render_template(
        'index.html',
        movie_list=movie_list,
        selected_movie=selected_movie,
        recommended_movies=recommended_movies
    )

if __name__ == '__main__':
    app.run(debug=True)

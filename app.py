import os
import pickle
import requests
from flask import Flask, render_template, request

# Initialize Flask app
app = Flask(__name__)

# Base directory path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Load movie list
movies = pickle.load(open(os.path.join(BASE_DIR, 'model', 'movie_list.pkl'), 'rb'))

# 2. Load precomputed recommendations (or similarity matrix)
recs_path = os.path.join(BASE_DIR, 'model', 'recommendations.pkl')
sim_path = os.path.join(BASE_DIR, 'model', 'similarity.pkl')

if os.path.exists(recs_path):
    recommendations_data = pickle.load(open(recs_path, 'rb'))
    similarity = None
else:
    recommendations_data = None
    similarity = pickle.load(open(sim_path, 'rb'))


# 3. Simple function to fetch movie poster using OMDb API (Amazon IMDb CDN)
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
    # Fallback placeholder image if poster is not found
    return "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"


# 4. Simple function to recommend top 5 similar movies
def recommend(movie_name):
    recommended_movie_names = []
    recommended_movie_posters = []

    # If we have the fast precomputed recommendations
    if recommendations_data and movie_name in recommendations_data:
        top_5 = recommendations_data[movie_name][:5]
        for item in top_5:
            title = item['title']
            recommended_movie_names.append(title)
            recommended_movie_posters.append(fetch_poster(title))

    # Otherwise fallback to cosine similarity matrix
    elif similarity is not None:
        index = movies[movies['title'] == movie_name].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
        for i in distances[1:6]:
            title = movies.iloc[i[0]].title
            recommended_movie_names.append(title)
            recommended_movie_posters.append(fetch_poster(title))

    return recommended_movie_names, recommended_movie_posters


# 5. Flask Route
@app.route('/', methods=['GET', 'POST'])
def home():
    # Sorted list of movie titles for the dropdown
    movie_list = sorted(movies['title'].values)
    recommended_movies = []
    selected_movie = None

    if request.method == 'POST':
        selected_movie = request.form.get('selected_movie')
        if selected_movie:
            names, posters = recommend(selected_movie)
            # Combine names and posters: [('Title 1', 'url1'), ('Title 2', 'url2'), ...]
            recommended_movies = list(zip(names, posters))

    return render_template(
        'index.html',
        movie_list=movie_list,
        selected_movie=selected_movie,
        recommended_movies=recommended_movies
    )


if __name__ == '__main__':
    app.run(debug=True)

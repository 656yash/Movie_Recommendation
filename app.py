import os
import pickle
import requests
from flask import Flask, render_template, request, jsonify

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static'),
    static_url_path='/static'
)

# Configuration
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "8265bd1679663a7ea12ac168da84d2e8")
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
FALLBACK_POSTER = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60"

# In-memory storage for models
movies_df = None
recommendations_map = None
similarity_matrix = None

def load_models():
    """Loads model files gracefully with fallback mechanisms."""
    global movies_df, recommendations_map, similarity_matrix

    movie_list_path = os.path.join(BASE_DIR, 'model', 'movie_list.pkl')
    recs_path = os.path.join(BASE_DIR, 'model', 'recommendations.pkl')
    sim_path = os.path.join(BASE_DIR, 'model', 'similarity.pkl')

    if os.path.exists(movie_list_path):
        with open(movie_list_path, 'rb') as f:
            movies_df = pickle.load(f)
        print(f"[INFO] Loaded movies dataset with {len(movies_df)} titles.")

    if os.path.exists(recs_path):
        with open(recs_path, 'rb') as f:
            recommendations_map = pickle.load(f)
        print("[INFO] Loaded precomputed recommendations map (Vercel-optimized).")

    elif os.path.exists(sim_path):
        with open(sim_path, 'rb') as f:
            similarity_matrix = pickle.load(f)
        print("[INFO] Loaded full similarity matrix.")

# Preload upon startup
load_models()

import urllib.parse
from concurrent.futures import ThreadPoolExecutor

# In-memory poster & details cache to minimize redundant requests
meta_cache = {}

def fetch_from_omdb(title):
    """Fetches high-res poster from OMDb / Amazon IMDb CDN."""
    try:
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(title)}&apikey=trilogy"
        res = requests.get(url, timeout=2.0)
        if res.status_code == 200:
            data = res.json()
            poster = data.get('Poster')
            if poster and poster != 'N/A' and poster.startswith('http'):
                return {
                    "poster_url": poster,
                    "rating": data.get('imdbRating', 'N/A'),
                    "overview": data.get('Plot') or "No synopsis available.",
                    "release_date": (data.get('Year') or "")[:4],
                    "genres": [g.strip() for g in data.get('Genre', '').split(',')[:3] if g.strip()]
                }
    except Exception:
        pass
    return None

def fetch_from_wikipedia(title):
    """Fetches official poster from Wikipedia / Wikimedia Commons CDN (no API key needed, never blocked)."""
    headers = {'User-Agent': 'CinePulseApp/1.0 (contact@cinepulse.app)'}
    try:
        # Step 1: Search Wikipedia for movie article
        query = title + " film"
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        s_res = requests.get(search_url, headers=headers, timeout=2.0)
        if s_res.status_code == 200:
            search_data = s_res.json()
            results = search_data.get('query', {}).get('search', [])
            if results:
                page_title = results[0]['title']
                # Step 2: Fetch summary and thumbnail
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title)}"
                sum_res = requests.get(summary_url, headers=headers, timeout=2.0)
                if sum_res.status_code == 200:
                    sum_data = sum_res.json()
                    thumb = sum_data.get('thumbnail', {}).get('source')
                    if thumb:
                        return {
                            "poster_url": thumb,
                            "rating": "N/A",
                            "overview": sum_data.get('extract') or "No synopsis available.",
                            "release_date": "",
                            "genres": []
                        }
    except Exception:
        pass
    return None

def fetch_from_tmdb(movie_id):
    """Fetches metadata from TMDB API if accessible."""
    if not movie_id:
        return None
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        res = requests.get(url, timeout=1.2)
        if res.status_code == 200:
            data = res.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return {
                    "poster_url": f"{TMDB_IMAGE_BASE_URL}{poster_path}",
                    "rating": round(data.get('vote_average', 0), 1),
                    "overview": data.get('overview') or "No overview provided.",
                    "release_date": (data.get('release_date') or "")[:4],
                    "genres": [g['name'] for g in data.get('genres', [])[:3]]
                }
    except Exception:
        pass
    return None

def fetch_movie_meta(movie_id, title):
    """Multi-source resolver: OMDb (Amazon CDN) -> Wikipedia (Wikimedia) -> TMDB -> Fallback."""
    cache_key = title.lower() if title else str(movie_id)
    if cache_key in meta_cache:
        return meta_cache[cache_key]

    # Source 1: OMDb API (Amazon/IMDb CDN, ultra-fast and reliable)
    if title:
        meta = fetch_from_omdb(title)
        if meta:
            meta_cache[cache_key] = meta
            return meta

    # Source 2: Wikipedia / Wikimedia Commons (100% open, zero API keys, never blocked)
    if title:
        meta = fetch_from_wikipedia(title)
        if meta:
            meta_cache[cache_key] = meta
            return meta

    # Source 3: TMDB API (if available)
    if movie_id:
        meta = fetch_from_tmdb(movie_id)
        if meta:
            meta_cache[cache_key] = meta
            return meta

    # Source 4: Fallback
    fallback = {
        "poster_url": FALLBACK_POSTER,
        "rating": "N/A",
        "overview": "No synopsis available.",
        "release_date": "",
        "genres": []
    }
    meta_cache[cache_key] = fallback
    return fallback

def get_recommendations(movie_title, top_n=5):
    """Computes recommendations with multi-source parallel poster fetching."""
    global movies_df, recommendations_map, similarity_matrix

    if movies_df is None:
        load_models()

    if movies_df is None:
        return []

    # Case-insensitive title match
    matched = movies_df[movies_df['title'].str.lower() == movie_title.lower()]
    if matched.empty:
        return []

    target_title = matched.iloc[0]['title']
    raw_recs = []

    # Priority 1: Fast precomputed mapping (recommended for Vercel)
    if recommendations_map and target_title in recommendations_map:
        for item in recommendations_map[target_title][:top_n]:
            raw_recs.append({
                "movie_id": item['movie_id'],
                "title": item['title'],
                "match_score": int(item.get('similarity_score', 0.8) * 100)
            })

    # Priority 2: Fallback to similarity matrix computation
    elif similarity_matrix is not None:
        try:
            movie_idx = movies_df[movies_df['title'] == target_title].index[0]
            distances = sorted(list(enumerate(similarity_matrix[movie_idx])), reverse=True, key=lambda x: x[1])
            for i in distances[1:top_n + 1]:
                movie_row = movies_df.iloc[i[0]]
                raw_recs.append({
                    "movie_id": int(movie_row['movie_id']),
                    "title": movie_row['title'],
                    "match_score": int(float(i[1]) * 100)
                })
        except Exception as e:
            print(f"[ERROR] Error calculating recommendations: {e}")

    # Parallel metadata fetching across all candidates
    recommended_movies = []
    with ThreadPoolExecutor(max_workers=max(1, len(raw_recs))) as executor:
        meta_results = list(executor.map(lambda r: fetch_movie_meta(r['movie_id'], r['title']), raw_recs))

    for rec, meta in zip(raw_recs, meta_results):
        recommended_movies.append({
            "movie_id": rec['movie_id'],
            "title": rec['title'],
            "poster_url": meta['poster_url'],
            "rating": meta['rating'],
            "overview": meta['overview'],
            "release_year": meta['release_date'],
            "genres": meta['genres'],
            "match_score": rec['match_score']
        })

    return recommended_movies

# ----------------- ROUTES ----------------- #

@app.route('/')
def home():
    """Serves the main single-page interface."""
    return render_template('index.html')

@app.route('/api/movies', methods=['GET'])
def get_movie_list():
    """Returns all available movie titles for search and typeahead."""
    global movies_df
    if movies_df is None:
        load_models()

    if movies_df is not None:
        titles = movies_df['title'].tolist()
        return jsonify({"count": len(titles), "movies": titles})
    return jsonify({"count": 0, "movies": []})

@app.route('/api/recommend', methods=['GET'])
def recommend_endpoint():
    """Returns movie recommendations for a given query."""
    movie = request.args.get('movie', '').strip()
    count = int(request.args.get('count', 6))
    count = min(max(1, count), 10)

    if not movie:
        return jsonify({"error": "Movie title parameter 'movie' is required."}), 400

    results = get_recommendations(movie, top_n=count)
    if not results:
        return jsonify({
            "error": f"Movie '{movie}' not found in the database. Please select a title from the list.",
            "recommendations": []
        }), 404

    # Also fetch selected movie metadata for banner/hero display
    matched = movies_df[movies_df['title'].str.lower() == movie.lower()]
    selected_meta = None
    if not matched.empty:
        sel_row = matched.iloc[0]
        meta = fetch_movie_meta(sel_row['movie_id'], sel_row['title'])
        selected_meta = {
            "movie_id": int(sel_row['movie_id']),
            "title": sel_row['title'],
            "poster_url": meta['poster_url'],
            "rating": meta['rating'],
            "overview": meta['overview'],
            "release_year": meta['release_date'],
            "genres": meta['genres']
        }

    return jsonify({
        "selected_movie": selected_meta,
        "recommendations": results
    })

@app.route('/api/random', methods=['GET'])
def random_movie():
    """Returns a random movie title from the dataset for quick discovery."""
    global movies_df
    if movies_df is None:
        load_models()

    if movies_df is not None and not movies_df.empty:
        sample = movies_df.sample(1).iloc[0]
        return jsonify({"title": sample['title']})
    return jsonify({"title": "Avatar"})

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "Movie Recommendation System API"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

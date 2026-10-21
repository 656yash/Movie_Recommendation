import os
import ast
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def convert(obj):
    L = []
    for i in ast.literal_eval(obj):
        L.append(i['name'])
    return L

def convert3(obj):
    L = []
    counter = 0
    for i in ast.literal_eval(obj):
        if counter < 3:
            L.append(i['name'])
            counter += 1
        else:
            break
    return L

def fetch_dir(obj):
    L = []
    for i in ast.literal_eval(obj):
        if i.get('job') == 'Director':
            L.append(i['name'])
            break
    return L

def main():
    print("Loading datasets...")
    movies = pd.read_csv('tmdb_5000_movies.csv')
    credits = pd.read_csv('tmdb_5000_credits.csv')

    print(f"Movies shape: {movies.shape}, Credits shape: {credits.shape}")
    movies = movies.merge(credits, on='title')

    print("Selecting features and cleaning...")
    # Keep movie_id / id
    movies = movies[['id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew', 'vote_average', 'release_date']]
    movies.rename(columns={'id': 'movie_id'}, inplace=True)
    movies.dropna(subset=['overview', 'title', 'movie_id'], inplace=True)

    movies['genres'] = movies['genres'].apply(convert)
    movies['keywords'] = movies['keywords'].apply(convert)
    movies['cast'] = movies['cast'].apply(convert3)
    movies['crew'] = movies['crew'].apply(fetch_dir)

    # Clean overview and whitespace
    movies['overview_list'] = movies['overview'].apply(lambda x: x.split() if isinstance(x, str) else [])
    clean_genres = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
    clean_keywords = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
    clean_cast = movies['cast'].apply(lambda x: [i.replace(" ", "") for i in x])
    clean_crew = movies['crew'].apply(lambda x: [i.replace(" ", "") for i in x])

    movies['tags'] = movies['overview_list'] + clean_genres + clean_keywords + clean_cast + clean_crew
    movies['tags_str'] = movies['tags'].apply(lambda x: " ".join(x).lower())

    movies.reset_index(drop=True, inplace=True)

    print("Vectorizing tags...")
    cv = CountVectorizer(max_features=5000, stop_words='english')
    vectors = cv.fit_transform(movies['tags_str']).toarray()

    print("Computing cosine similarity...")
    similarity = cosine_similarity(vectors)

    os.makedirs('model', exist_ok=True)

    # 1. Standard movie_list dataframe (matches user's original schema)
    movie_list_df = movies[['movie_id', 'title', 'vote_average', 'release_date']].copy()
    with open('model/movie_list.pkl', 'wb') as f:
        pickle.dump(movie_list_df, f)
    print("Saved model/movie_list.pkl")

    # 2. Precomputed top 10 recommendations mapping
    # This solves Vercel's serverless function memory and size limitations completely!
    print("Precomputing top recommendations mapping for fast Vercel deployment...")
    recommendations_map = {}
    for idx, row in movies.iterrows():
        movie_title = row['title']
        distances = sorted(list(enumerate(similarity[idx])), reverse=True, key=lambda x: x[1])
        top_recs = []
        for i in distances[1:11]:  # Top 10 recommendations
            rec_row = movies.iloc[i[0]]
            top_recs.append({
                'movie_id': int(rec_row['movie_id']),
                'title': rec_row['title'],
                'similarity_score': round(float(i[1]), 3)
            })
        recommendations_map[movie_title] = top_recs

    with open('model/recommendations.pkl', 'wb') as f:
        pickle.dump(recommendations_map, f)
    print(f"Saved model/recommendations.pkl ({len(recommendations_map)} movies)")

    # 3. Also save similarity.pkl (compressed as float16 to save space if needed)
    print("Saving float16 similarity matrix for compatibility...")
    sim_float16 = similarity.astype(np.float16)
    with open('model/similarity.pkl', 'wb') as f:
        pickle.dump(sim_float16, f)
    print("Saved model/similarity.pkl")

    rec_size = os.path.getsize('model/recommendations.pkl') / (1024)
    list_size = os.path.getsize('model/movie_list.pkl') / (1024)
    sim_size = os.path.getsize('model/similarity.pkl') / (1024 * 1024)

    print("\n--- File Sizes ---")
    print(f"movie_list.pkl: {list_size:.2f} KB")
    print(f"recommendations.pkl (Vercel-optimized): {rec_size:.2f} KB")
    print(f"similarity.pkl (Float16 matrix): {sim_size:.2f} MB")
    print("\nBuild complete successfully!")

if __name__ == '__main__':
    main()

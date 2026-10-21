# 🎬 Simple Movie Recommender System (Flask + Vercel)

A clean, beginner-friendly movie recommender built with **Python**, **Flask**, and **OMDb API**, optimized for easy understanding and **Vercel** serverless deployment.

---

## 💡 How It Works (In 3 Simple Steps)

1. **Movie Selection**: The user selects a movie from a dropdown list.
2. **Recommendation Engine**: The backend finds the 5 most similar movies based on plot, cast, and genres (precomputed via cosine similarity).
3. **Poster Fetching**: It fetches official high-definition movie posters using the simple OMDb API:
   ```python
   def fetch_poster(movie_title):
       url = f"http://www.omdbapi.com/?t={movie_title}&apikey=trilogy"
       response = requests.get(url)
       data = response.json()
       return data.get('Poster')
   ```

---

## 📂 Project Structure

```
d:/Movie Recommendation System/
├── api/
│   └── index.py            # Vercel Serverless entrypoint
├── model/
│   ├── movie_list.pkl      # List of 4,806 movie titles (211 KB)
│   └── recommendations.pkl # Precomputed top recommendations (1.38 MB)
├── static/
│   └── css/
│       └── style.css       # Clean, modern styling
├── templates/
│   └── index.html          # Simple HTML page with dropdown & movie cards
├── app.py                  # Main Flask application (~70 lines of clean code)
├── requirements.txt        # Flask, requests, pandas, gunicorn
├── vercel.json             # Vercel configuration
└── README.md
```

---


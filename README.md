# 🎬 CinePulse — AI Movie Recommendation System (Flask & Vercel)

A high-performance, responsive AI movie recommender built with **Flask**, **Scikit-Learn NLP**, and the **TMDB (The Movie Database) API**, fully optimized for **Vercel Serverless Deployment**.

---

## 📌 Why Flask & Why Vercel? (Streamlit vs Flask)

| Feature | Streamlit | Flask (This Project) |
| :--- | :--- | :--- |
| **Server Architecture** | Requires persistent state & active WebSockets | Stateless WSGI HTTP endpoints |
| **Vercel Compatibility** | ❌ **Incompatible** (Vercel is serverless, terminating after request) |  **100% Native** via `@vercel/python` |
| **Custom UI & Styling** | Limited to Streamlit widgets & default layout |  Unlimited HTML5/CSS3 glassmorphism, responsive grid & modals |
| **Memory & Cold Starts** | Heavy runtime, slow cold-starts |  Ultra-fast cold starts (~5ms) |
| **API Integration** | Renders Python-only UI | Exposes both web interface and JSON API (`/api/recommend`) |

---

## 🚀 The Vercel Serverless Optimization (How We Solved the 180MB Model Problem)

In traditional Streamlit tutorials, the similarity matrix (`similarity.pkl`) is dumped as a dense `4806 x 4806` float array:
- **Raw size:** ~180 MB.
- **Problem:** GitHub rejects files over **100 MB**; Vercel serverless function memory and cold-start timeout limits fail on massive pickled matrices.
- **Our Solution:** The `build_model.py` script precomputes the **Top 10 similar movies for each title** into `model/recommendations.pkl`:
  - `model/movie_list.pkl`: **~211 KB**
  - `model/recommendations.pkl`: **~1.38 MB** (Total payload: **< 1.6 MB**!)
  - Instant loading, zero memory footprint, and commits easily to GitHub for 1-click Vercel deployments!

---

## 📂 Project Structure

```
d:/Movie Recommendation System/
├── api/
│   └── index.py            # Vercel Serverless entrypoint exposing WSGI `app`
├── model/
│   ├── movie_list.pkl      # Cleaned DataFrame of 4,806 titles & IDs (211 KB)
│   ├── recommendations.pkl # Precomputed Top-10 recommendations (1.38 MB)
│   └── similarity.pkl      # Full float16 similarity matrix (44 MB, local use)
├── static/
│   ├── css/
│   │   └── style.css       # Obsidian & cyan dark theme, glassmorphism, responsive grid
│   └── js/
│       └── app.js          # Live typeahead search, modal controls, API fetch
├── templates/
│   └── index.html          # Semantic HTML5 single-page application
├── app.py                  # Core Flask server & REST API endpoints
├── build_model.py          # Script that transforms CSVs into optimized pickle models
├── requirements.txt        # Serverless-friendly Python dependencies
├── vercel.json             # Vercel URL rewrite routing configuration
├── .gitignore              # Ignores large raw CSVs & python caches
└── .env.example            # Environment variables template
```

---

## 🛠️ Step 1: Running Locally

### 1. Clone or open the project folder
```bash
cd "d:\Movie Recommendation System"
```

### 2. Verify dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Rebuild the model
The optimized models are already generated in `model/`. If you ever want to rebuild them from the raw CSVs:
```bash
python build_model.py
```

### 4. Run the Flask development server
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:5000`**

---

## 🌐 Step 2: Deploying to Vercel

### Method A: Deploy via GitHub (Recommended)
1. Initialize git and commit the project:
   ```bash
   git init
   git add .
   git commit -m "Initial CinePulse Flask app ready for Vercel"
   ```
2. Push your repository to **GitHub**.
3. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
4. Import your GitHub repository.
5. In **Environment Variables**, add:
   - **Key:** `TMDB_API_KEY`
   - **Value:** `8265bd1679663a7ea12ac168da84d2e8`
6. Click **Deploy**. Vercel will install dependencies and deploy the site in ~45 seconds!

### Method B: Deploy via Vercel CLI
```bash
npm install -g vercel
vercel login
vercel
```
Follow the interactive prompt (press Enter for defaults).

---

## 🔌 API Endpoints Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Main responsive movie recommendation web app |
| `/api/movies` | `GET` | Returns list of 4,806 movie titles for instant search |
| `/api/recommend?movie=<title>&count=5` | `GET` | Returns recommended movies with TMDB posters, ratings & synopsis |
| `/api/random` | `GET` | Returns a random movie title for "Surprise Me" discovery |
| `/health` | `GET` | Health check endpoint |

---

## 🖼️ Multi-Source High-Definition Poster Engine

TMDB (`api.themoviedb.org`) is frequently throttled or blocked by Indian ISPs (Jio, Airtel, Vi) on default DNS. To solve this, CinePulse uses an intelligent multi-tiered image provider:

1. **OMDb / Amazon IMDb CDN (`m.media-amazon.com`) [Primary]**:
   - Ultra-fast, official theatrical posters directly from Amazon S3/CloudFront.
   - **Never blocked** by any ISP, zero setup needed.
2. **Wikipedia & Wikimedia Commons API (`upload.wikimedia.org`) [Secondary]**:
   - 100% free, no API keys, open access worldwide, retrieves high-resolution theatrical artwork.
3. **TMDB API (`api.themoviedb.org`) [Tertiary]**:
   - Works automatically when deployed on Vercel's global edge servers.
4. **Cinematic Fallback**:
   - Graceful fallback ensures no card is ever broken or blank.

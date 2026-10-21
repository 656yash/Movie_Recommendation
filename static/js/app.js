// CinePulse App Logic

let allMovies = [];
let currentFocusIndex = -1;

// DOM Elements
const movieInput = document.getElementById('movieInput');
const clearBtn = document.getElementById('clearBtn');
const autocompleteList = document.getElementById('autocompleteList');
const countSelect = document.getElementById('countSelect');
const recommendBtn = document.getElementById('recommendBtn');
const randomBtn = document.getElementById('randomBtn');

const spotlightSection = document.getElementById('spotlightSection');
const spotlightPoster = document.getElementById('spotlightPoster');
const spotlightTitle = document.getElementById('spotlightTitle');
const spotlightYear = document.getElementById('spotlightYear');
const spotlightRating = document.getElementById('spotlightRating');
const spotlightGenres = document.getElementById('spotlightGenres');
const spotlightOverview = document.getElementById('spotlightOverview');

const recsHeader = document.getElementById('recsHeader');
const resultsCount = document.getElementById('resultsCount');
const movieGrid = document.getElementById('movieGrid');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');

const movieModal = document.getElementById('movieModal');
const modalClose = document.getElementById('modalClose');
const modalPoster = document.getElementById('modalPoster');
const modalTitle = document.getElementById('modalTitle');
const modalYear = document.getElementById('modalYear');
const modalRating = document.getElementById('modalRating');
const modalMatch = document.getElementById('modalMatch');
const modalGenres = document.getElementById('modalGenres');
const modalOverview = document.getElementById('modalOverview');
const modalTmdbLink = document.getElementById('modalTmdbLink');

// Initialize app & fetch movie catalogue for instant autocomplete
async function init() {
    try {
        const res = await fetch('/api/movies');
        const data = await res.json();
        allMovies = data.movies || [];
        console.log(`[CinePulse] Loaded ${allMovies.length} movies for instant autocomplete.`);
    } catch (err) {
        console.error('Failed to load movie index:', err);
    }
}

// Autocomplete logic
movieInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    clearBtn.style.display = val ? 'block' : 'none';
    currentFocusIndex = -1;

    if (!val || val.length < 1) {
        autocompleteList.style.display = 'none';
        return;
    }

    const matches = allMovies.filter(m => m.toLowerCase().includes(val.toLowerCase())).slice(0, 8);

    if (matches.length === 0) {
        autocompleteList.style.display = 'none';
        return;
    }

    autocompleteList.innerHTML = matches.map((m, idx) => `
        <div class="autocomplete-item" data-title="${m}" data-index="${idx}">
            <i class="fa-solid fa-film"></i>
            <span>${highlightMatch(m, val)}</span>
        </div>
    `).join('');

    autocompleteList.style.display = 'block';
});

function highlightMatch(text, query) {
    const regex = new RegExp(`(${query})`, 'gi');
    return text.replace(regex, '<strong style="color: var(--accent-cyan);">$1</strong>');
}

// Click on autocomplete item
autocompleteList.addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (item) {
        selectMovie(item.getAttribute('data-title'));
    }
});

// Clear button
clearBtn.addEventListener('click', () => {
    movieInput.value = '';
    clearBtn.style.display = 'none';
    autocompleteList.style.display = 'none';
    movieInput.focus();
});

// Keyboard navigation in autocomplete list
movieInput.addEventListener('keydown', (e) => {
    const items = autocompleteList.querySelectorAll('.autocomplete-item');
    if (!items.length || autocompleteList.style.display === 'none') {
        if (e.key === 'Enter') {
            triggerRecommendation();
        }
        return;
    }

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        currentFocusIndex = (currentFocusIndex + 1) % items.length;
        updateActiveItem(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        currentFocusIndex = (currentFocusIndex - 1 + items.length) % items.length;
        updateActiveItem(items);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (currentFocusIndex > -1 && items[currentFocusIndex]) {
            selectMovie(items[currentFocusIndex].getAttribute('data-title'));
        } else {
            triggerRecommendation();
        }
    } else if (e.key === 'Escape') {
        autocompleteList.style.display = 'none';
    }
});

function updateActiveItem(items) {
    items.forEach((item, idx) => {
        item.classList.toggle('active', idx === currentFocusIndex);
        if (idx === currentFocusIndex) {
            item.scrollIntoView({ block: 'nearest' });
        }
    });
}

// Close autocomplete on click outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
        autocompleteList.style.display = 'none';
    }
});

function selectMovie(title) {
    movieInput.value = title;
    autocompleteList.style.display = 'none';
    clearBtn.style.display = 'block';
    triggerRecommendation();
}

// Surprise Me button
randomBtn.addEventListener('click', async () => {
    try {
        randomBtn.disabled = true;
        randomBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Finding...';
        const res = await fetch('/api/random');
        const data = await res.json();
        if (data.title) {
            selectMovie(data.title);
        }
    } catch (e) {
        console.error('Error getting random movie:', e);
    } finally {
        randomBtn.disabled = false;
        randomBtn.innerHTML = '<i class="fa-solid fa-shuffle"></i> Surprise Me';
    }
});

// Recommend Button Click
recommendBtn.addEventListener('click', () => {
    triggerRecommendation();
});

// Fetch and render recommendations
async function triggerRecommendation() {
    const query = movieInput.value.trim();
    if (!query) {
        alert('Please enter or select a movie title first!');
        movieInput.focus();
        return;
    }

    autocompleteList.style.display = 'none';
    const count = countSelect.value;

    // UI State: Loading
    emptyState.style.display = 'none';
    movieGrid.innerHTML = '';
    recsHeader.style.display = 'none';
    loadingState.style.display = 'flex';
    recommendBtn.disabled = true;
    recommendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Recommending...</span>';

    try {
        const response = await fetch(`/api/recommend?movie=${encodeURIComponent(query)}&count=${count}`);
        const data = await response.json();

        loadingState.style.display = 'none';

        if (!response.ok || data.error) {
            showError(data.error || 'Movie not found. Please try another title.');
            return;
        }

        // Render Spotlight of Selected Movie
        if (data.selected_movie) {
            renderSpotlight(data.selected_movie);
        }

        // Render Recommendations Cards
        renderRecommendations(data.recommendations || []);

    } catch (err) {
        loadingState.style.display = 'none';
        showError('Network error or server timeout. Please check connection and try again.');
        console.error(err);
    } finally {
        recommendBtn.disabled = false;
        recommendBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Recommend</span>';
    }
}

function renderSpotlight(movie) {
    spotlightTitle.textContent = movie.title;
    spotlightYear.textContent = movie.release_year || 'Release year N/A';
    spotlightRating.innerHTML = `<i class="fa-solid fa-star"></i> ${movie.rating || 'N/A'}`;
    spotlightOverview.textContent = movie.overview || 'No overview available.';
    spotlightPoster.src = movie.poster_url;
    spotlightPoster.onerror = () => {
        spotlightPoster.src = 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60';
    };

    spotlightGenres.innerHTML = (movie.genres || []).map(g => `<span class="genre-tag">${g}</span>`).join('');
    spotlightSection.style.display = 'block';
}

function renderRecommendations(movies) {
    if (!movies.length) {
        showError('No similar movies found for this title.');
        return;
    }

    recsHeader.style.display = 'flex';
    resultsCount.textContent = `${movies.length} Movies Recommended`;

    movieGrid.innerHTML = movies.map((m, idx) => `
        <div class="movie-card" onclick="openModal(${idx})">
            <div class="poster-wrap">
                <span class="card-match-badge">${m.match_score || 85}% Match</span>
                <img src="${m.poster_url}" alt="${m.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60'">
            </div>
            <div class="card-content">
                <h4 class="card-title" title="${m.title}">${m.title}</h4>
                <div class="card-meta">
                    <span>${m.release_year || '—'}</span>
                    <span class="card-rating"><i class="fa-solid fa-star"></i> ${m.rating || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');

    // Save for modal lookup
    window.currentRecs = movies;
}

function showError(message) {
    emptyState.style.display = 'block';
    emptyState.innerHTML = `
        <i class="fa-solid fa-triangle-exclamation empty-icon" style="color: #ef4444; opacity: 0.8;"></i>
        <h3 style="color: #f87171;">Movie Not Found</h3>
        <p>${message}</p>
    `;
}

// Modal functions
window.openModal = function(index) {
    const movie = window.currentRecs && window.currentRecs[index];
    if (!movie) return;

    modalTitle.textContent = movie.title;
    modalYear.textContent = movie.release_year ? `Released: ${movie.release_year}` : '';
    modalRating.innerHTML = `<i class="fa-solid fa-star"></i> ${movie.rating || 'N/A'}`;
    modalMatch.textContent = `${movie.match_score || 85}% Similarity`;
    modalOverview.textContent = movie.overview || 'No synopsis available for this title.';
    modalPoster.src = movie.poster_url;
    modalPoster.onerror = () => {
        modalPoster.src = 'https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?w=500&auto=format&fit=crop&q=60';
    };

    modalGenres.innerHTML = (movie.genres || []).map(g => `<span class="genre-tag">${g}</span>`).join('');
    modalTmdbLink.href = movie.movie_id ? `https://www.themoviedb.org/movie/${movie.movie_id}` : '#';

    movieModal.style.display = 'flex';
};

modalClose.addEventListener('click', () => {
    movieModal.style.display = 'none';
});

movieModal.addEventListener('click', (e) => {
    if (e.target === movieModal) {
        movieModal.style.display = 'none';
    }
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && movieModal.style.display === 'flex') {
        movieModal.style.display = 'none';
    }
});

// Run
init();

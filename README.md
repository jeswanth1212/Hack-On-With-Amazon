# Last Minutes (Team 97) — Hack-On-With-Amazon • Season 5

## Theme 3: **Enhanced Fire TV Experience**
> “Develop a personalised content-recommendation engine for Fire TV that considers mood, past behaviour and time-of-day. Create innovative social features for shared viewing experiences. Focus on AI-driven content recommendation and social watching across OTT platforms.”

---

## 🎬 What we built
A full-stack, AI-powered companion for Fire TV that turns solitary streaming into a rich, social and *context-aware* experience.

| Layer | Highlights |
| ----- | ---------- |
| **Recommendation Engine** | • Hybrid model (CF + CBF + Context) trained on ➜ 500 K simulated interactions  
• Context vectors:<br/>  mood / age / time-of-day / day-of-week / weather / preferred-language  
• Real-time REST + WebSocket API (FastAPI + python-socketio) |
| **Front-End (Next JS 14 / React 18)** | • Regional "Trending this week" with Netflix-style ❶❷❸ overlay  
• Personalised "Recommended for you" row (language & mood aware)  
• *FOMO Driven Recommendation* – shows what friends loved  
• Genre rails (Action, Comedy, etc.) filtered to avoid trending duplicates  
• **LeetCode-inspired profile** — yearly yellow heat-map + hex-badge milestones + recently watched carousel  
• Friends page (search, requests, activity, watch-party invites) |
| **Watch Party** | • WebRTC (simple-peer) synchronous playback  
• Real-time chat & presence via Socket.IO  
• **Live emotion recognition** (TensorFlow.js) — sentiments flow back to the engine to refine recommendations! |
| **Dev-Ops** | Docker-ready, SQLite-based, logs & metrics, seed scripts |

---

## 📜 Feature list
1. **Regional Trending** — Fetches TMDB *trending/week* for the viewer's country and displays top-10 with oversized translucent ranks.
2. **Context-Aware Recommendations**  
   • Past ratings + CF/SVD  
   • Content-based TF-IDF fallback  
   • Context re-weighting (mood × time-of-day).
3. **Genre Rails** — Action & Comedy rails use TMDB *discover* with language + genre filters; duplicates with trending are removed.
4. **Social Graph** — Add friends, accept/decline requests, tier badges, notifications.
5. **FOMO Row** — "Recommended by Friends" shows items your circle highly rated.
6. **Profile Badges & Heat-map** — LeetCode-style contribution grid, deterministic mock data plus real interaction counts; hexagonal milestone badges.
7. **Watch Party**  
   • Create/join/leave parties  
   • Live chat  
   • Video state sync  
   • **Emotion recognition via webcam** — happy / neutral / sad scores overlay.
8. **Offline-first** — key lists cached in `localStorage`; server errors gracefully fallback.

---

## 🛠️  Tech stack & architecture

| Layer | Technologies |
| ----- | ------------ |
| **Backend API** | Python 3.9 · FastAPI · Uvicorn · python-socketio · SQLite (ACID mode) · Joblib model artefacts |
| **ML / Recommender** | Scikit-learn SVD (matrix factorisation) · TF-IDF / Cosine similarity · Context-aware re-ranking (LightGBM-style weighted blending) |
| **Front-End** | Next .js 14 (App Router) · React 18 · TypeScript · Tailwind CSS + Shadcn/ui · Zustand (state) |
| **Real-time** | Socket.IO v4 (browser ↔ API) · WebRTC (simple-peer) for P2P media sync |
| **AI on the Edge** | TensorFlow.js (BlazeFace + Emotion CNN) for client-side facial-expression inference |
| **Tooling / Ops** | ESLint · Prettier · Husky + lint-staged · Docker · GitHub Actions CI |

The system is **stateless** at the API layer—context is passed via JWT-like payloads, while long-term preferences live in the embedded SQLite DB shipped on Fire OS devices. Models are hot-swappable: new `*.joblib` snapshots are atomically loaded without downtime.

---

## 🚀 Quick start
### Prerequisites
* Node ≥ 18  
* Python 3.9  
* `npm`, `pip`

### 1. Backend (FastAPI)
```bash
cd recommendation_system_backend
pip install -r requirements.txt
py run.py --step all  # preprocess → train → start API on :8080
```

### 2. Front-end (Next JS)
```bash
npm install
npm run dev        # http://localhost:3000
```

> The front-end proxies API calls to `http://localhost:8080` (edit `RECOMMENDATION_API_URL` in `src/lib/utils.ts` if needed).

---

## 🗂️  Repo structure (high-level)
```
│  recommendation_system_backend/   ← FastAPI + model training code
│  src/                             ← Next JS app & components
│  └─ lib/                          ← TMDB client, hooks, utils
│  public/                          ← assets
│  README.md
└─ ...
```

---

## 👥 Team
**Last Minutes** — Team 97
*   Jeswanth S 
*   Rohith Krishna
*   Surjith Khannan

---

# CLAUDE.md - Project Context for Claude Code

## Project Overview

CashFlow Engine is a financial analysis and portfolio management SaaS application built with Python/Streamlit. It helps traders and portfolio managers analyze backtested trading data, build optimized portfolios, run Monte Carlo simulations, and compare live trading performance against historical backtests.

## Tech Stack

- **Backend/Web Framework**: Streamlit (Python)
- **Database**: Supabase (PostgreSQL with Row Level Security)
- **Authentication**: Supabase Auth (Magic Link + Google OAuth)
- **Data Analysis**: Pandas, NumPy, SciPy
- **Visualization**: Plotly, Matplotlib, Seaborn
- **AI**: Google Gemini (GenAI)
- **Frontend Build** (secondary): Vite + TypeScript

## Project Structure

```
CashFlowEngineTool/
├── app.py                    # Main entry point - routing, auth, layout
├── core/
│   └── auth.py               # Authentication (Magic Link, OAuth, JWT)
├── modules/                  # Feature modules
│   ├── landing.py            # Home page with data upload
│   ├── login.py              # Login UI
│   ├── portfolio_analytics.py # Performance metrics & charts
│   ├── portfolio_builder.py  # Portfolio assembly tool
│   ├── monte_carlo.py        # Monte Carlo simulations
│   ├── comparison.py         # Live vs Backtest comparison
│   ├── meic_analysis.py      # Trading strategy analysis
│   ├── meic_optimizer.py     # Strategy optimization
│   ├── ai_analyst.py         # Gemini AI analysis
│   ├── sales_landing.py      # Marketing page
│   └── privacy.py            # Privacy policy
├── database.py               # Supabase operations & helpers
├── ui_components.py          # Reusable UI components
├── utils.py                  # General utilities
├── calculations.py           # Financial calculations
├── views.py                  # UI views & overlays
├── supabase_schema.sql       # Database schema & RLS policies
├── requirements.txt          # Python dependencies
└── .streamlit/config.toml    # Streamlit theme config
```

## Commands

```bash
# Run the application locally
streamlit run app.py

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies (for Vite frontend, rarely needed)
npm install

# Run Vite dev server (frontend only)
npm run dev
```

## Environment Variables

Required environment variables (set via Streamlit secrets or env vars):
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/public API key
- `GEMINI_API_KEY` - Google Gemini API key (for AI features)

For local development, create `.streamlit/secrets.toml`:
```toml
SUPABASE_URL = "your-url"
SUPABASE_KEY = "your-key"
```

## Architecture Notes

### Authentication Flow
- Magic Link tokens arrive as URL fragments (not query params)
- JavaScript in app.py converts fragments to query params for Streamlit
- Uses two-method handler (SVG onload + iframe fallback) for reliability
- PKCE code exchange for OAuth providers
- Session tokens stored in `st.session_state`

### Data Isolation
- All user data protected by Row Level Security (RLS)
- Foreign key relationships to user profiles
- Authenticated Supabase client enforces RLS automatically

### UI/Styling
- Custom CSS heavily overrides Streamlit defaults
- Fonts: Exo 2 (headings), Poppins (body)
- Primary color: #302BFF (Electric Blue)
- Uses `!important` flags extensively for style enforcement

## Key Patterns

### Session State
```python
# Check authentication
if st.session_state.get("authenticated"):
    # User is logged in
    user_id = st.session_state.get("user_id")
```

### Database Operations
```python
from database import get_authenticated_client, get_current_user_id

# Get authenticated Supabase client (respects RLS)
client = get_authenticated_client()
user_id = get_current_user_id()
```

### Adding New Pages
1. Create module in `modules/` directory
2. Add navigation option in `app.py` radio button
3. Add route handler in app.py main routing logic
4. Ensure auth check at start of page function

## Code Style

- Functions use snake_case
- Streamlit components use `st.` prefix
- CSS classes use kebab-case
- SQL uses lowercase with underscores
- Docstrings for complex functions

## Testing

No automated tests currently exist. Manual testing is performed.

## Common Tasks

### Modifying the Login Page
Edit `modules/login.py` for UI changes, `core/auth.py` for auth logic.

### Adding Database Tables
1. Add SQL to `supabase_schema.sql`
2. Add RLS policies for multi-user access
3. Run SQL in Supabase dashboard
4. Add Python helpers in `database.py`

### Updating Styles
Global styles are in `app.py` within the `inject_custom_theme()` function.
Component-specific styles can be added inline with `st.markdown()`.

### Adding New Analysis Features
1. Create new module in `modules/`
2. Follow pattern of existing modules (e.g., `portfolio_analytics.py`)
3. Add navigation in `app.py`
4. Use `database.py` helpers for data persistence

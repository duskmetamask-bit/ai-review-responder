# ⭐ AI Review Responder

AI-powered review management for local service businesses. Fetches Google and Facebook reviews, generates personalized GPT-4o-mini responses, and posts them with one click.

**Revenue model:** $15/mo subscription

---

## Features

- 🔗 **Google Business API** — Live review fetching
- 🔗 **Facebook Graph API** — Live review fetching  
- 🤖 **GPT-4o-mini responses** — Personalized, in your voice
- ⚡ **One-click approve & post** — Streamlined workflow
- ⚡ **Auto-reply to 5-star reviews** — Thank-you templates
- 📊 **Dashboard** — Response rate, avg rating, rating distribution
- 🎛️ **Customizable templates** — Edit all response templates
- 🎨 **Demo mode** — Works out of the box with sample data

---

## Quick Start (Local)

```bash
cd projects/review-responder
pip install -r requirements.txt

# Add your API keys
cp .streamlit/secrets.toml .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your keys

streamlit run app.py
```

---

## API Keys Needed

| Service | Key | Where to get |
|---------|-----|-------------|
| OpenAI | `OPENAI_API_KEY` | platform.openai.com |
| Google | `GOOGLE_API_KEY` | console.cloud.google.com — enable "My Business Business Information API" |
| Google | `GOOGLE_PLACES_KEY` | Your Google Business location ID |
| Facebook | `FACEBOOK_ACCESS_TOKEN` | developers.facebook.com — Pages Manage Reviews permission |

---

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add secrets in the Streamlit dashboard:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
   - `GOOGLE_PLACES_KEY`
   - `FACEBOOK_ACCESS_TOKEN`
   - `BUSINESS_NAME`
   - `OWNER_NAME`
   - `OWNER_VOICE`
5. Deploy!

---

## Demo Mode

The app ships with 10 realistic demo reviews (Google + Facebook). No API keys needed to try it out. Configure API keys in the sidebar to connect real reviews.

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **OpenAI GPT-4o-mini** — Response generation
- **Google Business API** — Google reviews
- **Facebook Graph API** — Facebook reviews
- **Plotly** — Charts

---

## Revenue

**$15/month per business**

Target customers: plumbers, electricians, dentists, salons, mechanics, HVAC, real estate agents, and other local service businesses who want to manage their online reputation without spending hours manually responding to every review.

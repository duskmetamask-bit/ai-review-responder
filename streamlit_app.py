"""
AI Review Responder — Streamlit App
Connects Google Business + Facebook reviews, generates AI responses, auto-posts.
Revenue: $15/mo subscription for local service businesses.
"""

import streamlit as st
import openai
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random
import uuid
import os
from dotenv import load_dotenv

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="AI Review Responder",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .review-card {
        background: #f8f9fa;
        border-left: 4px solid #4285f4;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .review-card.positive { border-left-color: #34a853; }
    .review-card.negative { border-left-color: #ea4335; }
    .review-card.neutral  { border-left-color: #fbbc04; }
    .star-badge {
        background: #fef3c7;
        color: #92400e;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 13px;
        font-weight: 600;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
    }
    .metric-card.green  { background: linear-gradient(135deg, #11998e, #38ef7d); }
    .metric-card.red    { background: linear-gradient(135deg, #eb3349, #f45c43); }
    .metric-card.blue   { background: linear-gradient(135deg, #2193b0, #6dd5ed); }
    .metric-card.orange { background: linear-gradient(135deg, #f093fb, #f5576c); }
    .source-badge {
        border-radius: 6px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .source-google { background: #e8f0fe; color: #4285f4; }
    .source-facebook { background: #e7f3ff; color: #1877f2; }
    .response-box {
        background: #f0f4ff;
        border: 1px solid #c7d2fe;
        border-radius: 8px;
        padding: 14px;
        margin-top: 8px;
    }
    .approved-badge {
        background: #d1fae5;
        color: #065f46;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    .auto-badge {
        background: #fef3c7;
        color: #92400e;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 12px;
        font-weight: 600;
    }
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# API KEYS / SESSION INIT
# ─────────────────────────────────────────
def init_session():
    defaults = {
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "google_places_key": os.getenv("GOOGLE_PLACES_KEY", ""),
        "facebook_token": os.getenv("FACEBOOK_ACCESS_TOKEN", ""),
        "business_name": os.getenv("BUSINESS_NAME", "Your Business"),
        "owner_name": os.getenv("OWNER_NAME", "Alex"),
        "owner_voice": os.getenv("OWNER_VOICE", "friendly, professional, and genuine"),
        "auto_reply_5star": True,
        "responses": [],  # {id, review_id, text, approved, posted, timestamp}
        "refreshed_at": None,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

init_session()

# ─────────────────────────────────────────
# DEMO DATA
# ─────────────────────────────────────────
DEMO_REVIEWS = [
    {"id": "g1", "source": "google", "author": "Sarah M.", "rating": 5, "text": "Absolutely incredible service! The team went above and beyond for our family. Highly recommend to anyone looking for quality work.", "date": (datetime.now() - timedelta(days=1)).isoformat(), "respondable": True},
    {"id": "g2", "source": "google", "author": "James K.", "rating": 4, "text": "Really happy with the results. Minor delay in communication but the end product was fantastic. Would use again.", "date": (datetime.now() - timedelta(days=3)).isoformat(), "respondable": True},
    {"id": "g3", "source": "google", "author": "Priya R.", "rating": 5, "text": "Best decision we made! Professional, on-time, and the quality blew us away. Already booked them for our next project.", "date": (datetime.now() - timedelta(days=5)).isoformat(), "respondable": True},
    {"id": "g4", "source": "google", "author": "Tom H.", "rating": 2, "text": "Disappointed with the service. The work was okay but they didn't show up on time twice. Needs improvement.", "date": (datetime.now() - timedelta(days=7)).isoformat(), "respondable": True},
    {"id": "g5", "source": "google", "author": "Linda C.", "rating": 1, "text": "Terrible experience. The product arrived damaged and customer service was unhelpful. Requested a refund two weeks ago and still nothing.", "date": (datetime.now() - timedelta(days=10)).isoformat(), "respondable": True},
    {"id": "f1", "source": "facebook", "author": "Mark D.", "rating": 5, "text": "Can not say enough good things! From start to finish the experience was flawless. Already recommended to three friends.", "date": (datetime.now() - timedelta(days=2)).isoformat(), "respondable": True},
    {"id": "f2", "source": "facebook", "author": "Jenny L.", "rating": 3, "text": "Average experience overall. The product is decent but the price feels a bit high for what you get. Might be worth it for some.", "date": (datetime.now() - timedelta(days=4)).isoformat(), "respondable": True},
    {"id": "f3", "source": "facebook", "author": "Robert B.", "rating": 5, "text": "Phenomenal attention to detail. They really listened to what we wanted and delivered beyond expectations. Five stars easily.", "date": (datetime.now() - timedelta(days=6)).isoformat(), "respondable": True},
    {"id": "f4", "source": "facebook", "author": "Amy W.", "rating": 4, "text": "Really impressed! Only giving 4 stars because one small detail was missed, but overall very satisfied.", "date": (datetime.now() - timedelta(days=8)).isoformat(), "respondable": True},
    {"id": "f5", "source": "facebook", "author": "Chris P.", "rating": 2, "text": "Not great. The service was slow and the final result did not match what was promised in the consultation.", "date": (datetime.now() - timedelta(days=12)).isoformat(), "respondable": True},
]

TEMPLATE_RESPONSES = {
    "5star": [
        "Hi {author}! 🎉 Thank you so much for this wonderful review — we truly appreciate you taking the time to share your experience! We're so glad we could exceed your expectations and we're already looking forward to working with you again soon. Have a fantastic day! — {owner}",
    ],
    "4star": [
        "Hi {author}, thank you so much for the kind words and the 4 stars! We really appreciate you letting us know. We're sorry to hear about the minor hiccup — we'll definitely take that feedback on board. Hope to see you again soon! — {owner}",
    ],
    "3star": [
        "Hi {author}, thanks for your feedback! We appreciate you sharing your experience and we're sorry the overall result wasn't quite what you hoped. We'd love to make it right — please reach out to us directly so we can discuss. — {owner}",
    ],
    "2star": [
        "Hi {author}, we're truly sorry to hear about your experience. That's not the standard of service we aim for, and we've shared your feedback with our team. We'd love to discuss this further — please DM us. — {owner}",
    ],
    "1star": [
        "Hi {author}, we're devastated to read this and sincerely apologize. This is not the experience we want for any customer. Please contact us directly so we can make this right as quickly as possible. — {owner}",
    ],
}

# ─────────────────────────────────────────
# API FUNCTIONS
# ─────────────────────────────────────────
def fetch_google_reviews(location_id=None, api_key=None):
    """Fetch reviews from Google Business API."""
    if not api_key:
        return None, "Google API key not configured"
    try:
        url = f"https://mybusinessbusinessinformation.googleapis.com/v1/accounts/-/locations/{location_id}/reviews"
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("reviews", []), None
        return None, f"Google API error: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def fetch_facebook_reviews(page_id=None, access_token=None):
    """Fetch reviews from Facebook Graph API."""
    if not access_token:
        return None, "Facebook access token not configured"
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}/ratings"
        params = {"access_token": access_token, "fields": "reviewer{name, picture}, rating, open_graph_story{created_time, data}", "limit": 50}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("data", []), None
        return None, f"Facebook API error: {resp.status_code}"
    except Exception as e:
        return None, str(e)

def generate_ai_response(review_text, author_name, rating, owner_name, owner_voice, openai_key):
    """Generate a personalized response using OpenAI GPT-4o-mini."""
    if not openai_key:
        return None, "OpenAI API key not configured"

    star_bucket = "5star" if rating == 5 else "4star" if rating == 4 else "3star" if rating == 3 else "2star" if rating == 2 else "1star"
    template = random.choice(TEMPLATE_RESPONSES[star_bucket]).format(author=author_name.split()[0], owner=owner_name)

    prompt = f"""You are a business owner responding to a customer review.

BUSINESS OWNER VOICE: {owner_voice}
TEMPLATE (use as starting point): {template}

CUSTOMER REVIEW:
- Rating: {rating} stars
- Author: {author_name}
- Text: {review_text}

INSTRUCTIONS:
- Respond in the business owner's voice ({owner_voice})
- Reference specific details from the review
- Keep it warm and professional (50-120 words)
- If positive (4-5 stars): thank them enthusiastically and encourage repeat business
- If neutral (3 stars): acknowledge feedback, invite them to reach out
- If negative (1-2 stars): apologize sincerely, offer to make it right
- Do NOT be generic or use the same phrasing as the template
- Start with the customer's first name

Return ONLY the response text, no quotes or labels."""

    try:
        client = openai.OpenAI(api_key=openai_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip(), None
    except Exception as e:
        return None, str(e)

def post_google_response(review_id, response_text, location_id=None, api_key=None):
    """Post a response back to a Google review."""
    if not api_key:
        return False, "Google API key not configured"
    try:
        url = f"https://mybusinessbusinessinformation.googleapis.com/v1/accounts/-/locations/{location_id}/reviews/{review_id}/reply"
        payload = {"comment": response_text}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        resp = requests.patch(url, json=payload, headers=headers, timeout=10)
        return resp.status_code in (200, 201), None
    except Exception as e:
        return False, str(e)

def post_facebook_response(review_id, response_text, page_id=None, access_token=None):
    """Post a response back to a Facebook review."""
    if not access_token:
        return False, "Facebook access token not configured"
    try:
        url = f"https://graph.facebook.com/v18.0/{review_id}/comments"
        payload = {"access_token": access_token, "message": response_text}
        resp = requests.post(url, data=payload, timeout=10)
        return resp.status_code in (200, 201), None
    except Exception as e:
        return False, str(e)

# ─────────────────────────────────────────
# SIDEBAR / SETTINGS
# ─────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Settings")

    with st.expander("🔑 API Keys", expanded=True):
        openai_key = st.text_input("OpenAI API Key", value=st.session_state.openai_key, type="password", help="sk-...")
        google_key = st.text_input("Google API Key", value=st.session_state.google_api_key, type="password")
        google_places = st.text_input("Google Places Location ID", value=st.session_state.google_places_key, type="password", help="From Google Business API")
        fb_token = st.text_input("Facebook Access Token", value=st.session_state.facebook_token, type="password")

        if st.button("💾 Save Keys"):
            st.session_state.openai_key = openai_key
            st.session_state.google_api_key = google_key
            st.session_state.google_places_key = google_places
            st.session_state.facebook_token = fb_token
            st.success("Keys saved to session!")

    with st.expander("🏪 Business Info"):
        business_name = st.text_input("Business Name", value=st.session_state.business_name)
        owner_name = st.text_input("Your Name", value=st.session_state.owner_name)
        owner_voice = st.text_area("Your Voice", value=st.session_state.owner_voice, height=80,
                                    placeholder="e.g. friendly, professional, witty, uses casual language")
        if st.button("💾 Save Info"):
            st.session_state.business_name = business_name
            st.session_state.owner_name = owner_name
            st.session_state.owner_voice = owner_voice
            st.success("Business info saved!")

    with st.expander("🤖 Auto-Reply Settings"):
        auto_reply = st.checkbox("Auto-reply to 5-star reviews", value=st.session_state.auto_reply_5star)
        if st.button("💾 Save Auto-Reply"):
            st.session_state.auto_reply_5star = auto_reply

    st.markdown("---")
    st.caption("**$15/mo** — Local service businesses")

    if st.button("🔄 Refresh Reviews"):
        st.rerun()

# ─────────────────────────────────────────
# LOAD REVIEWS
# ─────────────────────────────────────────
def load_reviews():
    all_reviews = []

    # Try Google
    if st.session_state.google_api_key and st.session_state.google_places_key:
        reviews, err = fetch_google_reviews(st.session_state.google_places_key, st.session_state.google_api_key)
        if err:
            st.sidebar.warning(f"Google: {err}")
        elif reviews:
            for r in reviews:
                all_reviews.append({
                    "id": r.get("reviewId", str(uuid.uuid4())),
                    "source": "google",
                    "author": r.get("reviewer", {}).get("displayName", "Anonymous"),
                    "rating": r.get("rating", 0),
                    "text": r.get("comment", ""),
                    "date": r.get("createTime", datetime.now().isoformat()),
                    "respondable": True,
                })
    else:
        # Use demo data for google
        for r in DEMO_REVIEWS:
            if r["source"] == "google":
                all_reviews.append(r.copy())

    # Try Facebook
    if st.session_state.facebook_token:
        reviews, err = fetch_facebook_reviews(st.session_state.business_name.replace(" ", "").lower(), st.session_state.facebook_token)
        if err:
            st.sidebar.warning(f"Facebook: {err}")
        elif reviews:
            for r in reviews:
                all_reviews.append({
                    "id": r.get("id", str(uuid.uuid4())),
                    "source": "facebook",
                    "author": r.get("reviewer", {}).get("name", "Anonymous"),
                    "rating": r.get("rating", 0),
                    "text": r.get("open_graph_story", {}).get("data", {}).get("review_text", ""),
                    "date": r.get("open_graph_story", {}).get("created_time", datetime.now().isoformat()),
                    "respondable": True,
                })
    else:
        # Use demo data for facebook
        for r in DEMO_REVIEWS:
            if r["source"] == "facebook":
                all_reviews.append(r.copy())

    # Sort by date descending
    all_reviews.sort(key=lambda x: x["date"], reverse=True)
    st.session_state.refreshed_at = datetime.now().strftime("%H:%M:%S")
    return all_reviews

reviews = load_reviews()

# ─────────────────────────────────────────
# COMPUTE RESPONSES + STATS
# ─────────────────────────────────────────
def get_response_for_review(review_id):
    for resp in st.session_state.responses:
        if resp["review_id"] == review_id:
            return resp
    return None

# Stats
total = len(reviews)
if total == 0:
    st.warning("No reviews found. Add API keys in the sidebar or use demo mode.")
    st.stop()

avg_rating = sum(r["rating"] for r in reviews) / total
google_reviews = [r for r in reviews if r["source"] == "google"]
fb_reviews = [r for r in reviews if r["source"] == "facebook"]
responded = [r for r in reviews if get_response_for_review(r["id"])]
response_rate = len(responded) / total * 100 if total > 0 else 0

rating_distribution = {
    "5 ⭐": len([r for r in reviews if r["rating"] == 5]),
    "4 ⭐": len([r for r in reviews if r["rating"] == 4]),
    "3 ⭐": len([r for r in reviews if r["rating"] == 3]),
    "2 ⭐": len([r for r in reviews if r["rating"] == 2]),
    "1 ⭐": len([r for r in reviews if r["rating"] == 1]),
}

# ─────────────────────────────────────────
# DASHBOARD — STATS ROW
# ─────────────────────────────────────────
st.title("⭐ AI Review Responder")
st.caption(f"📥 Last refreshed: {st.session_state.refreshed_at} · Demo mode active (configure API keys to go live)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 Total Reviews", total)
with col2:
    st.metric("⭐ Avg Rating", f"{avg_rating:.1f}")
with col3:
    st.metric("✅ Response Rate", f"{response_rate:.0f}%")
with col4:
    st.metric("📊 Unresponded", total - len(responded))

st.markdown("---")

# ─────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📊 Rating Distribution")
    df_ratings = pd.DataFrame([{"Rating": k, "Count": v} for k, v in rating_distribution.items()])
    colors = ["#34a853", "#fbbc04", "#f8f9fa", "#ea4335", "#ea4335"]
    fig = px.bar(df_ratings, x="Rating", y="Count", color="Rating", color_discrete_sequence=colors)
    fig.update_layout(showlegend=False, height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    st.subheader("📱 Reviews by Source")
    source_data = pd.DataFrame([{"Source": "Google", "Count": len(google_reviews)}, {"Source": "Facebook", "Count": len(fb_reviews)}])
    fig2 = px.pie(source_data, names="Source", values="Count", hole=0.4, color="Source",
                  color_discrete_map={"Google": "#4285f4", "Facebook": "#1877f2"})
    fig2.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────
# REVIEW FEED
# ─────────────────────────────────────────
st.subheader("📬 Review Feed")

# Filter bar
filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    source_filter = st.selectbox("Source", ["All", "Google", "Facebook"])
with filter_col2:
    rating_filter = st.selectbox("Rating", ["All", "5 ⭐", "4 ⭐", "3 ⭐", "2 ⭐", "1 ⭐"])
with filter_col3:
    status_filter = st.selectbox("Status", ["All", "Needs Response", "Responded"])

filtered = reviews.copy()
if source_filter != "All":
    filtered = [r for r in filtered if r["source"] == source_filter.lower()]
if rating_filter != "All":
    star = int(rating_filter[0])
    filtered = [r for r in filtered if r["rating"] == star]
if status_filter == "Needs Response":
    filtered = [r for r in filtered if not get_response_for_review(r["id"])]
elif status_filter == "Responded":
    filtered = [r for r in filtered if get_response_for_review(r["id"])]

st.caption(f"Showing {len(filtered)} of {len(reviews)} reviews")

for review in filtered:
    resp_data = get_response_for_review(review["id"])
    responded_now = resp_data is not None
    star_label = "⭐" * review["rating"]
    sentiment = "positive" if review["rating"] >= 4 else "negative" if review["rating"] <= 2 else "neutral"
    date_str = datetime.fromisoformat(review["date"]).strftime("%b %d, %Y") if isinstance(review["date"], str) else str(review["date"])

    source_class = "source-google" if review["source"] == "google" else "source-facebook"

    st.markdown(f"""
    <div class="review-card {sentiment}">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
            <div>
                <strong>{review["author"]}</strong>
                <span class="star-badge">{star_label} ({review["rating"]}/5)</span>
                <span class="source-badge {source_class}">{review["source"]}</span>
                <span style="color:#888; font-size:12px; margin-left:8px;">{date_str}</span>
            </div>
            <div>
                {"<span class=\'approved-badge\'>✅ Responded</span>" if responded_now else ""}
            </div>
        </div>
        <div style="color:#333; font-size:14px; line-height:1.5;">{review["text"]}</div>
    </div>
    """, unsafe_allow_html=True)

    # Response section
    if not responded_now:
        # Generate response button
        gen_col1, gen_col2 = st.columns([1, 3])
        with gen_col1:
            if st.button(f"✨ Generate Response", key=f"gen_{review['id']}"):
                with st.spinner("🤖 Generating AI response..."):
                    response_text, err = generate_ai_response(
                        review["text"], review["author"], review["rating"],
                        st.session_state.owner_name, st.session_state.owner_voice,
                        st.session_state.openai_key,
                    )
                if err:
                    st.error(f"Error: {err}")
                else:
                    resp_entry = {
                        "id": str(uuid.uuid4()),
                        "review_id": review["id"],
                        "text": response_text,
                        "approved": False,
                        "posted": False,
                        "timestamp": datetime.now().isoformat(),
                        "is_auto": False,
                    }
                    st.session_state.responses.append(resp_entry)
                    st.rerun()

        # Auto-reply for 5-star if enabled
        if review["rating"] == 5 and st.session_state.auto_reply_5star and not responded_now:
            auto_text = random.choice(TEMPLATE_RESPONSES["5star"]).format(
                author=review["author"].split()[0], owner=st.session_state.owner_name
            )
            if st.button(f"⚡ Auto-Reply (5★ Thank You)", key=f"auto_{review['id']}"):
                resp_entry = {
                    "id": str(uuid.uuid4()),
                    "review_id": review["id"],
                    "text": auto_text,
                    "approved": True,
                    "posted": False,
                    "timestamp": datetime.now().isoformat(),
                    "is_auto": True,
                }
                st.session_state.responses.append(resp_entry)
                st.success("Auto-reply queued!")
                st.rerun()

    else:
        # Show existing response
        resp = resp_data
        badge = '<span class="auto-badge">⚡ Auto-Reply</span>' if resp.get("is_auto") else ""
        st.markdown(f"""
        <div class="response-box">
            <div style="margin-bottom:6px; font-size:12px; color:#666;">
                <strong>Your Response:</strong> {badge}
            </div>
            <div style="font-size:14px; line-height:1.5;">{resp["text"]}</div>
        </div>
        """, unsafe_allow_html=True)

        # Approve + Post
        post_col1, post_col2, post_col3 = st.columns([1, 1, 2])
        with post_col1:
            if not resp["posted"]:
                if st.button(f"✅ Approve & Post", key=f"post_{review['id']}"):
                    # Attempt to post
                    success = False
                    if review["source"] == "google":
                        ok, _ = post_google_response(review["id"], resp["text"],
                                                     st.session_state.google_places_key,
                                                     st.session_state.google_api_key)
                        success = ok
                    else:
                        ok, _ = post_facebook_response(review["id"], resp["text"],
                                                       st.session_state.business_name.replace(" ", "").lower(),
                                                       st.session_state.facebook_token)
                        success = ok

                    resp["approved"] = True
                    resp["posted"] = True
                    if success:
                        st.success("✅ Posted live!")
                    else:
                        st.warning("⚠️ Approved (API not configured — would post in live mode)")
                    st.rerun()
            else:
                st.success("✅ Posted")

        with post_col2:
            if st.button(f"✏️ Edit Response", key=f"edit_{review['id']}"):
                new_text = st.text_area("Edit your response:", value=resp["text"], key=f"edit_text_{review['id']}")
                if st.button("💾 Save Edit", key=f"save_edit_{review['id']}"):
                    resp["text"] = new_text
                    resp["posted"] = False
                    st.rerun()

        with post_col3:
            if st.button(f"🗑️ Discard", key=f"discard_{review['id']}"):
                st.session_state.responses = [r for r in st.session_state.responses if r["id"] != resp["id"]]
                st.rerun()

    st.markdown("---")

# ─────────────────────────────────────────
# RESPONSE TEMPLATES
# ─────────────────────────────────────────
with st.expander("📝 Response Templates (Customize)"):
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("**5-Star Template**")
        template_5 = st.text_area("5★ response", value=TEMPLATE_RESPONSES["5star"][0], height=100, key="tpl_5")
        st.markdown("**3-Star Template**")
        template_3 = st.text_area("3★ response", value=TEMPLATE_RESPONSES["3star"][0], height=100, key="tpl_3")
    with t_col2:
        st.markdown("**4-Star Template**")
        template_4 = st.text_area("4★ response", value=TEMPLATE_RESPONSES["4star"][0], height=100, key="tpl_4")
        st.markdown("**1-2 Star Template**")
        template_12 = st.text_area("1-2★ response", value=TEMPLATE_RESPONSES["1star"][0], height=100, key="tpl_12")

    if st.button("💾 Save Templates"):
        TEMPLATE_RESPONSES["5star"] = [template_5]
        TEMPLATE_RESPONSES["4star"] = [template_4]
        TEMPLATE_RESPONSES["3star"] = [template_3]
        TEMPLATE_RESPONSES["2star"] = [template_12]
        TEMPLATE_RESPONSES["1star"] = [template_12]
        st.success("Templates saved!")

# ─────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#888; font-size:12px; padding:20px 0;">
    <strong>AI Review Responder</strong> · $15/mo · Built for local service businesses<br>
    <a href="https://emvyai.com" target="_blank">emvyai.com</a> · AI-powered review management
</div>
""", unsafe_allow_html=True)

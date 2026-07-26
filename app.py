import streamlit as st
from groq import Groq
import datetime
import os
import json
import hashlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt, timedelta
import re
import requests
import io
from PIL import Image
import base64
import time
import random
from fpdf import FPDF
import tempfile

# ==================== CẤU HÌNH TRANG ====================
st.set_page_config(
    page_title="InnoMine-X",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== THEME & CSS ====================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def apply_theme():
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            /* Dark theme */
            .stApp { background-color: #0f1117; color: #e4e4e7; }
            section[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div,
            .stSlider > div { background-color: #21262d !important; color: #e4e4e7 !important; border: 1px solid #30363d; }
            h1, h2, h3, h4, h5, h6 { color: #f0f6fc !important; }
            .stMarkdown, .stMarkdown p { color: #c9d1d9 !important; }
            div[data-testid="stMetric"] { background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 16px; }
            .stAlert { background-color: #21262d; border: 1px solid #30363d; }
            .stButton > button { border-radius: 10px; font-weight: 600; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 16px; }
            .card { background: #161b22; border: 1px solid #30363d; border-radius: 14px; padding: 18px; margin-bottom: 12px; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            /* Light theme */
            .stApp { background-color: #f8fafc; color: #1e293b; }
            section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
            div[data-testid="stMetric"] { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .stButton > button { border-radius: 10px; font-weight: 600; }
            .stTabs [data-baseweb="tab-list"] { gap: 8px; }
            .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 10px 16px; }
            .card { background: white; border: 1px solid #e2e8f0; border-radius: 14px; padding: 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
            h1, h2, h3 { color: #0f172a !important; }
        </style>
        """, unsafe_allow_html=True)

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

apply_theme()

# ==================== CONSTANTS ====================
MOOD_SCORE = {
    "😢 Buồn": 2, "😐 Bình thường": 5, "😊 Vui vẻ": 8,
    "🤔 Suy tư": 6, "😎 Tự tin": 9, "✨ Hy vọng": 9
}
STRESS_KEYWORDS = ["stress", "áp lực", "mệt mỏi", "căng thẳng", "lo lắng", "mất ngủ", "cô đơn", "buồn", "chán nản", "tuyệt vọng"]
POSITIVE_MOODS = ["😊 Vui vẻ", "😎 Tự tin", "✨ Hy vọng"]

# ==================== SALT & PASSWORD ====================
SALT_LENGTH = 32

def get_salt():
    salt_file = "salt.bin"
    if os.path.exists(salt_file):
        with open(salt_file, "rb") as f:
            return f.read()
    salt = os.urandom(SALT_LENGTH)
    with open(salt_file, "wb") as f:
        f.write(salt)
    return salt

SALT = get_salt()

def hash_password(pwd: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pwd.encode("utf-8"), SALT, 100000).hex()

# ==================== USER MANAGEMENT ====================
USER_FILE = "users.json"

if not os.path.exists(USER_FILE):
    default_users = {
        "minh": hash_password("123"),
        "lan": hash_password("456"),
        "huy": hash_password("789")
    }
    with open(USER_FILE, "w") as f:
        json.dump(default_users, f)

@st.cache_data(ttl=60)
def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)
    st.cache_data.clear()

def authenticate(u, p):
    users = load_users()
    return users.get(u) == hash_password(p)

def register_user(u, p):
    users = load_users()
    if u in users:
        return False
    users[u] = hash_password(p)
    save_users(users)
    return True

def get_all_users():
    return list(load_users().keys())

# ==================== FRIENDS & SHARED ====================
@st.cache_data(ttl=30)
def get_friends(u):
    fname = f"{u}_friends.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []

def add_friend(u, f):
    friends = get_friends(u)
    if f not in friends:
        friends.append(f)
        with open(f"{u}_friends.json", "w") as fo:
            json.dump(friends, fo)
        st.cache_data.clear()

@st.cache_data(ttl=30)
def get_requests(u):
    fname = f"{u}_requests.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []

def send_request(fr, to):
    if fr == to or to in get_friends(fr):
        return False
    reqs = get_requests(to)
    if fr in reqs:
        return False
    reqs.append(fr)
    with open(f"{to}_requests.json", "w") as f:
        json.dump(reqs, f)
    st.cache_data.clear()
    return True

def accept_request(u, req):
    reqs = get_requests(u)
    if req in reqs:
        reqs.remove(req)
        with open(f"{u}_requests.json", "w") as f:
            json.dump(reqs, f)
        add_friend(u, req)
        add_friend(req, u)
        st.cache_data.clear()
        return True
    return False

@st.cache_data(ttl=30)
def get_shared_posts(u):
    fname = f"{u}_shared.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []

def add_shared_post(u, post):
    posts = get_shared_posts(u)
    posts.insert(0, post)
    with open(f"{u}_shared.json", "w") as f:
        json.dump(posts[:20], f)
    st.cache_data.clear()

# ==================== JOURNAL & GOALS ====================
@st.cache_data(ttl=30)
def load_journal(u):
    fname = f"{u}_journal.json"
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_journal(u, data):
    with open(f"{u}_journal.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    st.cache_data.clear()

def add_entry(u, entry):
    data = load_journal(u)
    data.append(entry)
    save_journal(u, data)

def delete_entry(u, index):
    data = load_journal(u)
    if 0 <= index < len(data):
        data.pop(index)
        save_journal(u, data)
        return True
    return False

@st.cache_data(ttl=30)
def load_goals(u):
    fname = f"{u}_goals.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []

def save_goals(u, goals):
    with open(f"{u}_goals.json", "w") as f:
        json.dump(goals, f)
    st.cache_data.clear()

def delete_goal(u, index):
    goals = load_goals(u)
    if 0 <= index < len(goals):
        goals.pop(index)
        save_goals(u, goals)
        return True
    return False

# ==================== MEMORY ====================
@st.cache_data(ttl=30)
def load_memory(u):
    fname = f"{u}_memory.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []

def save_memory(u, memory):
    with open(f"{u}_memory.json", "w") as f:
        json.dump(memory, f)
    st.cache_data.clear()

def add_memory(u, event):
    mem = load_memory(u)
    mem.append({"date": dt.now().isoformat(), "event": event})
    save_memory(u, mem[-20:])

# ==================== PGI ====================
@st.cache_data(ttl=60)
def compute_pgi(user):
    journal = load_journal(user)
    if len(journal) < 3:
        return None, {}

    scores = [MOOD_SCORE.get(e.get("mood", "😐 Bình thường"), 5) for e in journal[-10:]]
    emotional_stability = 100 - min(100, (max(scores) - min(scores)) * 10) if len(scores) > 1 else 50

    recent_days = {e["date"][:10] for e in journal[-14:]}
    consistency = (len(recent_days) / 14) * 100

    goals = load_goals(user)
    goal_completion = sum(g["progress"] for g in goals) / len(goals) if goals else 0

    recent_7 = journal[-7:]
    positive_count = sum(1 for e in recent_7 if e.get("mood") in POSITIVE_MOODS)
    positive_engagement = (positive_count / len(recent_7)) * 100 if recent_7 else 0

    pgi = (
        emotional_stability * 0.25 +
        consistency * 0.25 +
        goal_completion * 0.30 +
        positive_engagement * 0.20
    )
    pgi = round(pgi, 1)

    components = {
        "Ổn định cảm xúc": round(emotional_stability, 1),
        "Tính nhất quán": round(consistency, 1),
        "Hoàn thành mục tiêu": round(goal_completion, 1),
        "Tương tác tích cực": round(positive_engagement, 1)
    }
    return pgi, components

# ==================== EARLY WARNING ====================
def analyze_content(content):
    content_lower = content.lower()
    return sum(1 for kw in STRESS_KEYWORDS if kw in content_lower)

def early_warning_level(user):
    journal = load_journal(user)
    if len(journal) < 5:
        return "🟢 Xanh", "Chưa đủ dữ liệu", "green", "Hãy viết thêm nhật ký để hệ thống theo dõi tốt hơn."

    recent = journal[-10:]
    mood_neg = sum(1 for e in recent if e.get("mood") == "😢 Buồn")
    content_stress = sum(analyze_content(e.get("content", "")) for e in recent)
    risk_score = (mood_neg / len(recent)) * 100 + min(50, content_stress * 10)

    if risk_score >= 70:
        return "🔴 Đỏ", "Nguy cơ cao", "red", "Hãy nghỉ ngơi, nói chuyện với người thân hoặc giáo viên. Robot sẽ hỗ trợ cảnh báo."
    elif risk_score >= 50:
        return "🟠 Cam", "Nguy cơ trung bình", "orange", "Theo dõi sát hơn. Hãy dành thời gian thư giãn và viết nhật ký hàng ngày."
    elif risk_score >= 25:
        return "🟡 Vàng", "Nguy cơ nhẹ", "yellow", "Quan sát thêm. Cố gắng duy trì thói quen tích cực."
    else:
        return "🟢 Xanh", "Ổn định", "green", "Bạn đang duy trì trạng thái tốt. Tiếp tục phát huy!"

# ==================== STREAK ====================
def calculate_streak(user):
    journal = load_journal(user)
    if not journal:
        return 0
    dates = sorted({e["date"][:10] for e in journal}, reverse=True)
    today = dt.now().date()
    streak = 0
    for i, d in enumerate(dates):
        expected = (today - timedelta(days=i)).isoformat()
        if d == expected:
            streak += 1
        else:
            break
    return streak

# ==================== ROBOT ====================
if "robot_led" not in st.session_state:
    st.session_state.robot_led = False
if "robot_activities" not in st.session_state:
    st.session_state.robot_activities = []
if "robot_ip" not in st.session_state:
    st.session_state.robot_ip = "192.168.8.126"
if "robot_connected" not in st.session_state:
    st.session_state.robot_connected = False

def robot_alert(level):
    st.session_state.robot_led = (level == "red")

# ==================== GROQ ====================
if "GROQ_API_KEY" in st.secrets:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception:
        st.error("⚠️ Lỗi kết nối AI. Kiểm tra GROQ_API_KEY.")
        st.stop()
else:
    st.error("⚠️ Thiếu GROQ_API_KEY trong Secrets.")
    st.stop()

# ==================== LOGIN ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("""
        <div style="text-align:center; padding: 40px 0 20px;">
            <h1 style="font-size: 2.8rem; margin-bottom: 8px;">🧠 InnoMine-X</h1>
            <p style="font-size: 1.15rem; opacity: 0.85;">Hệ thống AI & Robot đồng hành hỗ trợ sức khỏe tinh thần học sinh</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        option = st.radio("Bạn muốn?", ["🔐 Đăng nhập", "🆕 Đăng ký"], horizontal=True, label_visibility="collapsed")
        if option == "🔐 Đăng nhập":
            u = st.text_input("Tên đăng nhập", placeholder="minh / lan / huy")
            p = st.text_input("Mật khẩu", type="password", placeholder="••••••")
            if st.button("Đăng nhập", use_container_width=True, type="primary"):
                if authenticate(u, p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Sai tên hoặc mật khẩu. Dùng: minh/123, lan/456, huy/789")
        else:
            u = st.text_input("Tên mới (chữ thường, không dấu)", placeholder="tennguoidung")
            p = st.text_input("Mật khẩu", type="password")
            c = st.text_input("Xác nhận mật khẩu", type="password")
            if st.button("Đăng ký", use_container_width=True, type="primary"):
                if u and p and p == c and u.isalnum():
                    if register_user(u, p):
                        st.success("Đăng ký thành công! Hãy đăng nhập.")
                    else:
                        st.error("Tên đã tồn tại.")
                else:
                    st.error("Tên chỉ gồm chữ và số, mật khẩu phải khớp.")
    st.stop()

user = st.session_state.username

# ==================== VOICE COMMAND ====================
def handle_voice_command():
    cmd = st.query_params.get("voice_cmd")
    if not cmd:
        return
    cmd = str(cmd).strip().lower()
    ip = st.session_state.get("robot_ip", "192.168.8.126")
    success = error = None
    try:
        if "led" in cmd and "vui" in cmd:
            requests.get(f"http://{ip}/control?action=led_vui", timeout=2)
            success = "😊 Đã bật LED Vui!"
        elif "led" in cmd and "buồn" in cmd:
            requests.get(f"http://{ip}/control?action=led_buon", timeout=2)
            success = "😢 Đã bật LED Buồn!"
        elif "led" in cmd and ("tắt" in cmd or "off" in cmd):
            requests.get(f"http://{ip}/control?action=led_off", timeout=2)
            success = "⏹ Đã tắt LED!"
        elif "rung" in cmd and ("bật" in cmd or "mở" in cmd):
            requests.get(f"http://{ip}/control?action=rung_on", timeout=2)
            success = "📳 Đã bật rung!"
        elif "rung" in cmd and ("tắt" in cmd or "đóng" in cmd):
            requests.get(f"http://{ip}/control?action=rung_off", timeout=2)
            success = "📳 Đã tắt rung!"
        elif "relay" in cmd and ("bật" in cmd or "mở" in cmd):
            requests.get(f"http://{ip}/control?action=relay_on", timeout=2)
            success = "🔴 Đã bật Relay!"
        elif "relay" in cmd and ("tắt" in cmd or "đóng" in cmd):
            requests.get(f"http://{ip}/control?action=relay_off", timeout=2)
            success = "⚫ Đã tắt Relay!"
        elif "chụp" in cmd or "ảnh" in cmd:
            success = "📸 Đã nhận lệnh chụp ảnh. Bấm nút thủ công nhé!"
        else:
            error = f"🤔 Không hiểu lệnh: '{cmd}'. Thử 'Bật LED vui', 'Tắt rung'..."
    except Exception as e:
        error = f"❌ Lỗi kết nối robot: {e}"
    if success:
        st.success(success)
    if error:
        st.error(error)
    st.query_params.clear()
    st.rerun()

handle_voice_command()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.button("🌓 Chế độ tối / sáng", on_click=toggle_theme, use_container_width=True)
    st.markdown(f"### 🧠 {user}")
    streak = calculate_streak(user)
    st.caption(f"🔥 Chuỗi nhật ký: **{streak} ngày**")
    st.markdown("---")

    # Mood nhanh
    st.markdown("#### Cảm xúc hôm nay")
    quick_mood = st.select_slider(
        "Mood",
        options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"],
        value="😐 Bình thường",
        label_visibility="collapsed"
    )
    if st.button("Lưu mood nhanh", use_container_width=True):
        entry = {
            "date": dt.now().isoformat(),
            "content": f"[Mood nhanh] {quick_mood}",
            "mood": quick_mood,
            "image": ""
        }
        add_entry(user, entry)
        st.success("Đã lưu mood!")
        st.rerun()

    st.markdown("---")
    reqs = get_requests(user)
    if reqs:
        st.markdown("### ✉️ Lời mời đến")
        for r in reqs:
            c1, c2 = st.columns([3, 1])
            c1.write(r)
            if c2.button("✅", key=f"accept_sb_{r}"):
                accept_request(user, r)
                st.rerun()
        st.markdown("---")

    st.markdown("### 👥 Bạn bè")
    friends = get_friends(user)
    if friends:
        for f in friends:
            st.write(f"• {f}")
    else:
        st.info("Chưa có bạn bè")

    st.markdown("---")
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
    st.caption("InnoMine-X • AI & Robot đồng hành")

# ==================== DASHBOARD ====================
st.markdown(f"<h1 style='text-align:center; margin-bottom: 4px;'>Chào {user} 👋</h1>", unsafe_allow_html=True)

pgi, pgi_components = compute_pgi(user)
warning_text, warning_desc, warning_color, warning_advice = early_warning_level(user)
robot_alert(warning_color)

colA, colB, colC, colD = st.columns(4)
colA.metric("📈 Chỉ số PGI", f"{pgi}/100" if pgi else "—", help="Personal Growth Index")
colB.metric("⚠️ Cảnh báo sớm", warning_text)
colC.metric("🔥 Streak", f"{streak} ngày")
colD.metric("📝 Nhật ký", f"{len(load_journal(user))} bài")

if pgi is not None:
    # Gauge PGI
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pgi,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "PGI"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#22c55e" if pgi >= 70 else "#f59e0b" if pgi >= 40 else "#ef4444"},
            "steps": [
                {"range": [0, 40], "color": "#fee2e2"},
                {"range": [40, 70], "color": "#fef3c7"},
                {"range": [70, 100], "color": "#dcfce7"}
            ],
            "threshold": {"line": {"color": "black", "width": 2}, "thickness": 0.75, "value": pgi}
        }
    ))
    fig_gauge.update_layout(height=220, margin=dict(t=30, b=10, l=20, r=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

if pgi_components:
    with st.expander("🔍 Chi tiết 4 thành phần PGI", expanded=False):
        for k, v in pgi_components.items():
            st.progress(v / 100, text=f"{k}: {v}/100")

# Cảnh báo
if warning_color == "red":
    st.error(f"🚨 **CẢNH BÁO ĐỎ**: {warning_desc} — {warning_advice}")
elif warning_color == "orange":
    st.warning(f"⚠️ **CẢNH BÁO CAM**: {warning_desc} — {warning_advice}")
elif warning_color == "yellow":
    st.warning(f"⚠️ **CẢNH BÁO VÀNG**: {warning_desc} — {warning_advice}")
else:
    st.success(f"✅ **TRẠNG THÁI XANH**: {warning_desc} — {warning_advice}")

# Nhắc mục tiêu
goals = load_goals(user)
if goals:
    overdue = [g for g in goals if g["progress"] < 50 and g.get("created_at", dt.now().isoformat()) < (dt.now() - timedelta(days=7)).isoformat()]
    if overdue:
        st.warning("⏰ Một số mục tiêu đã quá 7 ngày nhưng tiến độ dưới 50%:")
        for g in overdue:
            st.write(f"- **{g['name']}** ({g['progress']}%)")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📝 Nhật ký", "🧠 AI Insight", "🎯 Mục tiêu", "📊 Thống kê",
    "💬 Chat AI", "👥 Kết nối", "🤖 Robot"
])

# --- Tab 1: Nhật ký ---
with tab1:
    with st.form("journal_form", clear_on_submit=True):
        work = st.text_area("Hôm nay bạn đã làm gì?", height=120, placeholder="Viết tự do về ngày hôm nay...")
        mood = st.select_slider("Cảm xúc", options=list(MOOD_SCORE.keys()))
        image_url = st.text_input("🔗 Link ảnh (không bắt buộc)", placeholder="https://...")
        submitted = st.form_submit_button("💾 Lưu nhật ký", type="primary", use_container_width=True)

    if submitted and work.strip():
        entry = {
            "date": dt.now().isoformat(),
            "content": work.strip(),
            "mood": mood,
            "image": image_url.strip() if image_url else ""
        }
        add_entry(user, entry)

        # Memory
        lower = work.lower()
        if any(kw in lower for kw in STRESS_KEYWORDS):
            found = [kw for kw in STRESS_KEYWORDS if kw in lower]
            add_memory(user, f"Dấu hiệu: {', '.join(found)}")
        elif any(w in lower for w in ["vui", "hạnh phúc", "tự hào", "thích"]):
            add_memory(user, "Ghi nhận niềm vui / tích cực")

        st.success("Đã lưu nhật ký!")
        with st.spinner("InnoMine đang phân tích..."):
            prompt = f"Người dùng viết: {work}. Cảm xúc: {mood}. Đưa nhận xét ngắn gọn, chân thành, không tâng bốc. Chỉ ra xu hướng tích cực nếu có."
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.7
                )
                ai_reply = res.choices[0].message.content
                st.info(f"💡 {ai_reply}")
                st.session_state.last_ai_reply = ai_reply
            except Exception:
                st.info("AI tạm thời bận.")
        st.rerun()

    # Tìm kiếm
    journal = load_journal(user)
    if journal:
        search = st.text_input("🔍 Tìm trong nhật ký", placeholder="Từ khóa...")
        filtered = journal
        if search.strip():
            filtered = [e for e in journal if search.lower() in e.get("content", "").lower() or search.lower() in e.get("mood", "").lower()]

        st.markdown(f"**{len(filtered)}** bài gần đây")
        for idx, entry in enumerate(reversed(filtered[-15:])):
            real_idx = len(journal) - 1 - idx if not search else journal.index(entry)
            with st.container():
                c1, c2 = st.columns([12, 1])
                with c1:
                    st.markdown(f"**{entry['date'][:16]}** · {entry['mood']}")
                    st.write(entry["content"])
                    if entry.get("image"):
                        st.image(entry["image"], width=280)
                with c2:
                    if st.button("🗑️", key=f"del_j_{idx}_{entry['date']}"):
                        delete_entry(user, real_idx)
                        st.rerun()
                st.divider()
    else:
        st.info("Chưa có nhật ký. Hãy viết bài đầu tiên nhé!")

# --- Tab 2: AI Insight ---
with tab2:
    memory = load_memory(user)
    if memory:
        st.subheader("🧠 Ký ức quan trọng")
        for mem in reversed(memory[-6:]):
            st.markdown(f"- `{mem['date'][:16]}` — {mem['event']}")

    journal = load_journal(user)
    if len(journal) >= 3:
        st.subheader("Phân tích xu hướng")
        if st.button("🔄 Phân tích lại", type="primary"):
            recent = journal[-5:]
            summary = "\n".join([f"- {e['content']} ({e['mood']})" for e in recent])
            mem_txt = memory[-3:] if memory else "không có"
            prompt = f"Dựa trên nhật ký gần đây:\n{summary}\nLưu ý ký ức: {mem_txt}. Hãy nhận xét xu hướng cảm xúc và đưa 2-3 gợi ý thực tế, ngắn gọn."
            with st.spinner("Đang phân tích..."):
                try:
                    res = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant"
                    )
                    insight = res.choices[0].message.content
                    st.info(insight)
                    st.session_state.last_ai_reply = insight
                except Exception:
                    st.error("Lỗi AI.")
    else:
        st.info("Cần ít nhất 3 nhật ký để phân tích sâu.")

# --- Tab 3: Mục tiêu ---
with tab3:
    goals = load_goals(user)
    with st.form("goal_form"):
        goal_name = st.text_input("Mục tiêu mới", placeholder="Ví dụ: Đọc 10 cuốn sách")
        progress = st.slider("Tiến độ %", 0, 100, 0)
        if st.form_submit_button("Thêm / Cập nhật", type="primary"):
            if goal_name.strip():
                existing = {g["name"]: g for g in goals}
                existing[goal_name.strip()] = {
                    "name": goal_name.strip(),
                    "progress": progress,
                    "created_at": dt.now().isoformat()
                }
                save_goals(user, list(existing.values()))
                st.rerun()

    if goals:
        for idx, g in enumerate(goals):
            c1, c2 = st.columns([10, 1])
            with c1:
                st.write(f"**{g['name']}** — {g['progress']}%")
                st.progress(g["progress"] / 100)
            with c2:
                if st.button("🗑️", key=f"del_g_{idx}"):
                    delete_goal(user, idx)
                    st.rerun()
    else:
        st.info("Chưa có mục tiêu. Hãy đặt mục tiêu đầu tiên!")

# --- Tab 4: Thống kê ---
with tab4:
    journal = load_journal(user)
    if journal:
        df = pd.DataFrame(journal)
        df["date"] = pd.to_datetime(df["date"]).dt.date

        # Bar mood
        mood_counts = df.groupby(["date", "mood"]).size().reset_index(name="count")
        if not mood_counts.empty:
            fig = px.bar(mood_counts, x="date", y="count", color="mood", title="Cảm xúc theo ngày",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

        # Pie 7 ngày
        st.subheader("Phân bố cảm xúc 7 ngày qua")
        last_7 = df[df["date"] >= (dt.now().date() - timedelta(days=7))]
        if not last_7.empty:
            mood_pie = last_7["mood"].value_counts().reset_index()
            mood_pie.columns = ["mood", "count"]
            fig_pie = px.pie(mood_pie, names="mood", values="count", hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Chưa đủ dữ liệu 7 ngày.")

        # PGI over time
        st.subheader("Xu hướng PGI")
        pgi_over_time = []
        for i in range(3, len(journal) + 1):
            fake = journal[:i]
            scores = [MOOD_SCORE.get(e.get("mood", "😐 Bình thường"), 5) for e in fake]
            es = 100 - min(100, (max(scores) - min(scores)) * 10) if len(scores) > 1 else 50
            cons = (len({e["date"][:10] for e in fake}) / 14) * 100
            goals_tmp = load_goals(user)
            gc = sum(g["progress"] for g in goals_tmp) / len(goals_tmp) if goals_tmp else 0
            pos = sum(1 for e in fake if e.get("mood") in POSITIVE_MOODS) / len(fake) * 100
            pgi_val = es * 0.25 + cons * 0.25 + gc * 0.3 + pos * 0.2
            pgi_over_time.append(round(pgi_val, 1))

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=list(range(3, len(journal) + 1)),
            y=pgi_over_time,
            mode="lines+markers",
            name="PGI",
            line=dict(width=3, color="#3b82f6")
        ))
        fig2.update_layout(title="Chỉ số phát triển cá nhân theo thời gian", height=350)
        st.plotly_chart(fig2, use_container_width=True)

        if len(pgi_over_time) >= 5:
            x = list(range(len(pgi_over_time)))
            n = len(x)
            sum_x, sum_y = sum(x), sum(pgi_over_time)
            sum_xy = sum(x[i] * pgi_over_time[i] for i in range(n))
            sum_x2 = sum(i * i for i in x)
            denom = n * sum_x2 - sum_x * sum_x
            slope = (n * sum_xy - sum_x * sum_y) / denom if denom != 0 else 0
            intercept = (sum_y - slope * sum_x) / n
            next_pgi = slope * n + intercept
            st.metric("📈 Dự đoán PGI tiếp theo", f"{round(next_pgi, 1)}/100",
                      delta=round(next_pgi - pgi_over_time[-1], 1))

        # Export
        st.markdown("---")
        csv_data = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Tải CSV nhật ký", data=csv_data,
                           file_name=f"{user}_journal.csv", mime="text/csv")

        if st.button("📄 Xuất báo cáo PDF"):
            pdf = FPDF()
            pdf.add_page()
            # Dùng font mặc định + encode an toàn
            pdf.set_font("Arial", size=14)
            pdf.cell(0, 10, f"Bao cao InnoMine-X - {user}", ln=1, align="C")
            pdf.set_font("Arial", size=10)
            pdf.ln(5)
            for entry in journal[-12:]:
                date_str = entry["date"][:16]
                mood_str = entry["mood"].encode("latin-1", "replace").decode("latin-1")
                content_str = entry["content"][:180].encode("latin-1", "replace").decode("latin-1")
                pdf.cell(0, 8, f"{date_str} - {mood_str}", ln=1)
                pdf.multi_cell(0, 6, content_str)
                pdf.ln(3)
            pdf_bytes = pdf.output(dest="S").encode("latin-1")
            st.download_button("⬇️ Tải PDF", data=pdf_bytes,
                               file_name=f"{user}_report.pdf", mime="application/pdf")
    else:
        st.info("Chưa có dữ liệu thống kê.")

# --- Tab 5: Chat AI ---
with tab5:
    st.subheader("Trò chuyện cùng InnoMine")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        if msg.startswith("**Bạn:**"):
            st.markdown(f"<div style='background:#dbeafe;padding:10px 14px;border-radius:12px;margin:6px 0'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background:#f1f5f9;padding:10px 14px;border-radius:12px;margin:6px 0'>{msg}</div>", unsafe_allow_html=True)

    user_msg = st.chat_input("Bạn muốn nói gì với InnoMine?")
    if user_msg:
        st.session_state.chat_history.append(f"**Bạn:** {user_msg}")
        with st.spinner("Đang trả lời..."):
            try:
                res = client.chat.completions.create(
                    messages=[{"role": "user", "content": user_msg}],
                    model="llama-3.1-8b-instant"
                )
                reply = res.choices[0].message.content
                st.session_state.chat_history.append(f"**InnoMine:** {reply}")
                st.session_state.last_ai_reply = reply
            except Exception:
                st.session_state.chat_history.append("**InnoMine:** Lỗi kết nối AI.")
        st.rerun()

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
    with c2:
        if "last_ai_reply" in st.session_state and st.session_state.last_ai_reply:
            if st.button("🔊 Đọc phản hồi gần nhất", use_container_width=True):
                safe_text = json.dumps(st.session_state.last_ai_reply)
                js = f"""
                <script>
                    const utterance = new SpeechSynthesisUtterance({safe_text});
                    utterance.lang = 'vi-VN';
                    utterance.rate = 0.9;
                    window.speechSynthesis.speak(utterance);
                </script>
                """
                st.components.v1.html(js, height=0)

# --- Tab 6: Kết nối ---
with tab6:
    st.subheader("👥 Kết bạn")
    all_users = get_all_users()
    friends = get_friends(user)
    candidates = [u for u in all_users if u != user and u not in friends and u not in get_requests(user)]

    if candidates:
        target = st.selectbox("Chọn người dùng", candidates)
        if st.button("📨 Gửi lời mời", type="primary"):
            if send_request(user, target):
                st.success(f"Đã gửi lời mời đến {target}!")
                st.rerun()
    else:
        st.info("Không còn người dùng mới để kết bạn.")

    st.markdown("---")
    st.subheader("✉️ Lời mời đã nhận")
    reqs = get_requests(user)
    if reqs:
        for r in reqs:
            c1, c2 = st.columns([3, 1])
            c1.write(r)
            if c2.button("✅ Chấp nhận", key=f"acc_t6_{r}"):
                accept_request(user, r)
                st.rerun()
    else:
        st.info("Không có lời mời.")

    st.markdown("---")
    st.subheader("Danh sách bạn bè")
    if friends:
        for f in friends:
            st.write(f"• {f}")
    else:
        st.info("Chưa có bạn bè.")

    st.markdown("---")
    st.subheader("💬 Chia sẻ khoảnh khắc")
    share_content = st.text_area("Viết điều bạn muốn chia sẻ")
    share_image = st.text_input("Link ảnh (không bắt buộc)")
    if st.button("Chia sẻ"):
        if share_content.strip():
            post = {
                "date": dt.now().isoformat(),
                "content": share_content.strip(),
                "image": share_image.strip() if share_image else ""
            }
            add_shared_post(user, post)
            st.success("Đã chia sẻ!")
            st.rerun()

    st.markdown("### Bài viết từ bạn bè")
    for friend in get_friends(user):
        posts = get_shared_posts(friend)
        if posts:
            st.markdown(f"**{friend}**")
            for p in posts[:3]:
                st.write(f"- {p['content'][:120]}")
                if p.get("image"):
                    st.image(p["image"], width=220)

# --- Tab 7: Robot ---
with tab7:
    st.subheader("🤖 Điều khiển InnoMine-X")

    robot_ip = st.text_input("Địa chỉ IP robot", st.session_state.robot_ip)
    if st.button("🔗 Kết nối"):
        try:
            r = requests.get(f"http://{robot_ip}/capture", timeout=3)
            if r.status_code == 200:
                st.session_state.robot_ip = robot_ip
                st.session_state.robot_connected = True
                st.success("✅ Kết nối thành công!")
            else:
                st.error("❌ Lỗi kết nối")
        except Exception:
            st.error("❌ Không kết nối được robot")

    if st.session_state.get("robot_connected"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💡 LED")
            if st.button("😊 Vui", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_vui", timeout=2)
                    st.success("LED Vui")
                except Exception:
                    st.error("Lỗi")
            if st.button("😢 Buồn", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_buon", timeout=2)
                    st.success("LED Buồn")
                except Exception:
                    st.error("Lỗi")
            if st.button("⏹ Tắt LED", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_off", timeout=2)
                    st.success("Tắt LED")
                except Exception:
                    st.error("Lỗi")
        with c2:
            st.markdown("#### ⚡ Relay & Rung")
            if st.button("🔴 Bật Relay", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=relay_on", timeout=2)
                    st.success("Bật Relay")
                except Exception:
                    st.error("Lỗi")
            if st.button("⚫ Tắt Relay", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=relay_off", timeout=2)
                    st.success("Tắt Relay")
                except Exception:
                    st.error("Lỗi")
            if st.button("📳 Bật Rung", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=rung_on", timeout=2)
                    st.success("Bật Rung")
                except Exception:
                    st.error("Lỗi")
            if st.button("📳 Tắt Rung", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=rung_off", timeout=2)
                    st.success("Tắt Rung")
                except Exception:
                    st.error("Lỗi")

        st.markdown("#### 📷 Camera")
        if st.button("📸 Chụp ảnh"):
            try:
                r = requests.get(f"http://{st.session_state.robot_ip}/capture", timeout=5)
                if r.status_code == 200:
                    img = Image.open(io.BytesIO(r.content))
                    st.image(img, caption="Ảnh từ robot")
                    st.success("Đã chụp!")
                else:
                    st.error("Lỗi chụp ảnh")
            except Exception:
                st.error("Lỗi kết nối")

        if st.session_state.robot_activities:
            st.markdown("#### 📋 Hoạt động gần đây")
            for act in st.session_state.robot_activities[-5:]:
                st.write(f"- {act['time'][:16]}: {act['activity']} ({act['emotion']})")

    # Voice control
    st.markdown("---")
    st.markdown("#### 🎤 Điều khiển bằng giọng nói")
    st.caption("Nói lệnh như: 'Bật LED vui', 'Tắt rung', 'Chụp ảnh'")
    voice_html = """
    <div style="text-align:center;padding:10px">
        <button id="start_btn" style="padding:14px 28px;font-size:18px;background:#22c55e;color:white;border:none;border-radius:12px;cursor:pointer;font-weight:600">
            🎤 Nhấn và nói
        </button>
        <p id="status" style="margin-top:12px;color:#64748b">Nhấn nút để bắt đầu</p>
        <p id="result" style="margin-top:8px;font-weight:600;color:#ef4444"></p>
    </div>
    <script>
        const startBtn = document.getElementById('start_btn');
        const statusEl = document.getElementById('status');
        const resultEl = document.getElementById('result');
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognition = new SpeechRecognition();
            recognition.lang = 'vi-VN';
            recognition.continuous = false;
            recognition.interimResults = false;
            startBtn.onclick = () => {
                statusEl.textContent = '🎧 Đang nghe...';
                startBtn.disabled = true;
                startBtn.style.background = '#ef4444';
                resultEl.textContent = '';
                recognition.start();
            };
            recognition.onresult = (event) => {
                const text = event.results[event.results.length-1][0].transcript;
                resultEl.textContent = '✅ Bạn nói: ' + text;
                statusEl.textContent = '⏳ Đang gửi lệnh...';
                const url = new URL(window.location.href);
                url.searchParams.set('voice_cmd', text);
                window.location.href = url.toString();
            };
            recognition.onerror = (e) => {
                statusEl.textContent = '❌ Lỗi: ' + e.error;
                startBtn.disabled = false;
                startBtn.style.background = '#22c55e';
            };
            recognition.onend = () => {
                startBtn.disabled = false;
                startBtn.style.background = '#22c55e';
            };
        } else {
            statusEl.textContent = '❌ Trình duyệt không hỗ trợ. Dùng Chrome/Edge.';
        }
    </script>
    """
    st.components.v1.html(voice_html, height=180)

    # Learning path
    st.markdown("---")
    def generate_learning_path():
        activities = st.session_state.get("robot_activities", [])
        journal = load_journal(user)
        study_time = sum(1 for a in activities[-20:] if "học" in a.get("activity", "").lower())
        rest_time = sum(1 for a in activities[-20:] if "nghỉ" in a.get("activity", "").lower())
        suggestions = []
        if journal:
            sad = sum(1 for e in journal[-5:] if e.get("mood") == "😢 Buồn")
            if sad >= 3:
                suggestions.append("😢 Có dấu hiệu mệt mỏi. Hãy nghỉ ngơi và thư giãn.")
        if study_time > 10:
            suggestions.append("📚 Học nhiều rồi! Nghỉ 15 phút và vận động nhẹ.")
        elif study_time < 3:
            suggestions.append("📖 Hôm nay chưa học nhiều. Hãy dành ít nhất 1 giờ ôn bài.")
        if rest_time < 2:
            suggestions.append("😴 Cần nghỉ ngơi nhiều hơn. Ngủ đủ 7-8 tiếng.")
        if not suggestions:
            suggestions.append("🌟 Lịch trình tốt! Hãy duy trì.")
        return suggestions

    if st.button("🔄 Tạo lộ trình học tập"):
        st.session_state.learning_path = generate_learning_path()

    if "learning_path" in st.session_state:
        st.subheader("📝 Lộ trình đề xuất")
        for i, s in enumerate(st.session_state.learning_path, 1):
            st.write(f"{i}. {s}")

    st.markdown("#### 📝 Ghi nhận hoạt động")
    act = st.text_input("Hoạt động (ví dụ: học Toán, nghỉ ngơi)")
    emo = st.selectbox("Cảm xúc", ["😊 Vui", "😐 Bình thường", "😢 Buồn", "🤔 Suy tư"])
    if st.button("Ghi nhận"):
        if act.strip():
            st.session_state.robot_activities.append({
                "time": dt.now().isoformat(),
                "activity": act.strip(),
                "emotion": emo
            })
            st.success("Đã ghi nhận!")
            st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
st.caption("InnoMine-X • Hệ thống AI & Robot hỗ trợ sức khỏe tinh thần học sinh • 2025")

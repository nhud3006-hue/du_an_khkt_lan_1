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
import csv
from fpdf import FPDF
import time
import random

# ==================== IMPORT VOICE UTILS ====================
try:
    from voice_utils import get_speech_html, handle_voice_command, render_tts
except ModuleNotFoundError:
    st.error("⚠️ Không tìm thấy file voice_utils.py. Hãy tạo file này cùng thư mục với app.py")
    st.stop()

# ==================== CẤU HÌNH TRANG + THEME ====================
st.set_page_config(
    page_title="InnoMine-X",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== THEME TOGGLE ====================
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
                .stApp { background-color: #1e1e1e; color: #f0f0f0; }
                .stSidebar { background-color: #2d2d2d; }
                .stTextInput, .stTextArea, .stSelectbox, .stSlider { background-color: #333; color: white; }
                h1, h2, h3, h4, h5, h6 { color: #f0f0f0; }
                .stMarkdown { color: #f0f0f0; }
                .stAlert { background-color: #333; }
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
                .stApp { background-color: white; color: black; }
                .stSidebar { background-color: #f0f2f6; }
            </style>
        """, unsafe_allow_html=True)

# ==================== GLOBAL CONSTANTS ====================
MOOD_SCORE = {"😢 Buồn": 2, "😐 Bình thường": 5, "😊 Vui vẻ": 8, "🤔 Suy tư": 6, "😎 Tự tin": 9, "✨ Hy vọng": 9}
STRESS_KEYWORDS = ["stress", "áp lực", "mệt mỏi", "căng thẳng", "lo lắng", "mất ngủ", "cô đơn", "buồn"]

# ==================== SALT CHO MẬT KHẨU ====================
SALT_LENGTH = 32
def get_salt():
    salt_file = "salt.bin"
    if os.path.exists(salt_file):
        with open(salt_file, "rb") as f:
            return f.read()
    else:
        salt = os.urandom(SALT_LENGTH)
        with open(salt_file, "wb") as f:
            f.write(salt)
        return salt

SALT = get_salt()

def hash_password(pwd):
    return hashlib.pbkdf2_hmac('sha256', pwd.encode('utf-8'), SALT, 100000).hex()

# ==================== QUẢN LÝ USER ====================
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
    except:
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

# ==================== BẠN BÈ & CHIA SẺ ====================
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
    if fr == to: return False
    if to in get_friends(fr): return False
    reqs = get_requests(to)
    if fr in reqs: return False
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

# ==================== NHẬT KÝ & MỤC TIÊU ====================
@st.cache_data(ttl=30)
def load_journal(u):
    fname = f"{u}_journal.json"
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_journal(u, data):
    with open(f"{u}_journal.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
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

# ==================== MEMORY ENGINE ====================
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

# ==================== TÍNH TOÁN PGI ====================
@st.cache_data(ttl=60)
def compute_pgi(user):
    journal = load_journal(user)
    if len(journal) < 3:
        return None, {}
    scores = [MOOD_SCORE.get(e.get("mood", "😐 Bình thường"), 5) for e in journal[-10:]]
    if len(scores) > 1:
        emotional_stability = 100 - min(100, (max(scores)-min(scores)) * 10)
    else:
        emotional_stability = 50
    recent_days = set()
    for e in journal[-14:]:
        recent_days.add(e["date"][:10])
    consistency = (len(recent_days) / 14) * 100
    goals = load_goals(user)
    if goals:
        goal_completion = sum([g["progress"] for g in goals]) / len(goals)
    else:
        goal_completion = 0
    positive_moods = ["😊 Vui vẻ", "😎 Tự tin", "✨ Hy vọng"]
    recent_7 = journal[-7:]
    if recent_7:
        positive_count = sum(1 for e in recent_7 if e.get("mood") in positive_moods)
        positive_engagement = (positive_count / len(recent_7)) * 100
    else:
        positive_engagement = 0
    pgi = emotional_stability * 0.25 + consistency * 0.25 + goal_completion * 0.3 + positive_engagement * 0.2
    pgi = round(pgi, 1)
    components = {
        "Emotional Stability": round(emotional_stability, 1),
        "Consistency": round(consistency, 1),
        "Goal Completion": round(goal_completion, 1),
        "Positive Engagement": round(positive_engagement, 1)
    }
    return pgi, components

# ==================== EARLY WARNING ====================
def analyze_content(content):
    content_lower = content.lower()
    stress_score = 0
    for kw in STRESS_KEYWORDS:
        if kw in content_lower:
            stress_score += 1
    return stress_score

def early_warning_level(user):
    journal = load_journal(user)
    if len(journal) < 5:
        return "🟢 Xanh", "Chưa đủ dữ liệu", "green"
    negative_moods = ["😢 Buồn"]
    recent = journal[-10:]
    mood_neg = sum(1 for e in recent if e.get("mood") in negative_moods)
    content_stress = sum(analyze_content(e.get("content", "")) for e in recent)
    risk_score = (mood_neg / len(recent)) * 100 + min(50, content_stress * 10)
    if risk_score >= 70:
        return "🔴 Đỏ", "Nguy cơ cao - Can thiệp ngay", "red"
    elif risk_score >= 50:
        return "🟠 Cam", "Nguy cơ trung bình - Theo dõi sát", "orange"
    elif risk_score >= 25:
        return "🟡 Vàng", "Nguy cơ nhẹ - Quan sát thêm", "yellow"
    else:
        return "🟢 Xanh", "Ổn định", "green"

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
    if level == "red":
        st.session_state.robot_led = True
    else:
        st.session_state.robot_led = False

# ==================== GROQ ====================
if "GROQ_API_KEY" in st.secrets:
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        st.error("⚠️ Lỗi kết nối AI.")
        st.stop()
else:
    st.error("⚠️ Thiếu GROQ_API_KEY trong Secrets.")
    st.stop()

# ==================== ĐĂNG NHẬP ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;'>🧠 InnoMine-X</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Hệ thống AI & Robot đồng hành hỗ trợ sức khỏe tinh thần học sinh</p>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            option = st.radio("Bạn muốn?", ["🔐 Đăng nhập", "🆕 Đăng ký"], horizontal=True)
            if option == "🔐 Đăng nhập":
                u = st.text_input("Tên đăng nhập")
                p = st.text_input("Mật khẩu", type="password")
                if st.button("Đăng nhập", use_container_width=True):
                    if authenticate(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("Sai tên hoặc mật khẩu. Dùng: minh/123, lan/456, huy/789")
            else:
                u = st.text_input("Tên mới (chữ thường, không dấu)")
                p = st.text_input("Mật khẩu", type="password")
                c = st.text_input("Xác nhận mật khẩu", type="password")
                if st.button("Đăng ký", use_container_width=True):
                    if u and p and p == c and u.isalnum():
                        if register_user(u, p):
                            st.success("Đăng ký thành công! Hãy đăng nhập.")
                        else:
                            st.error("Tên đã tồn tại.")
                    else:
                        st.error("Tên chỉ gồm chữ và số, mật khẩu phải khớp.")
    st.stop()

user = st.session_state.username
avatar = "🧠"

# ==================== XỬ LÝ LỆNH VOICE (THÊM MỚI) ====================
# Lấy IP robot từ session (nếu đã kết nối) hoặc dùng mặc định
robot_ip = st.session_state.get("robot_ip", "192.168.8.126")
handle_voice_command(robot_ip)

# ==================== THEME TOGGLE BUTTON ====================
st.sidebar.button("🌓 Chế độ tối/sáng", on_click=toggle_theme)

# ==================== SIDEBAR ====================
st.sidebar.markdown(f"### {avatar} {user}")
st.sidebar.markdown("---")

reqs = get_requests(user)
if reqs:
    st.sidebar.markdown("### ✉️ Lời mời đến")
    for r in reqs:
        col1, col2 = st.sidebar.columns([3,1])
        col1.write(r)
        if col2.button("✅", key=f"accept_sidebar_{r}"):
            accept_request(user, r)
            st.rerun()
    st.sidebar.markdown("---")

st.sidebar.markdown("### 👥 Bạn bè")
friends = get_friends(user)
if friends:
    for f in friends:
        st.sidebar.write(f"• {f}")
else:
    st.sidebar.info("Chưa có bạn bè.")
st.sidebar.markdown("---")

# ==================== DASHBOARD ====================
st.markdown(f"<h1 style='text-align:center;'>Chào {user} 👋</h1>", unsafe_allow_html=True)
pgi, pgi_components = compute_pgi(user)
warning_text, warning_desc, warning_color = early_warning_level(user)
robot_alert(warning_color)

colA, colB, colC = st.columns(3)
colA.metric("📈 Chỉ số PGI", f"{pgi}/100" if pgi else "Chưa đủ dữ liệu")
colB.metric("⚠️ Cảnh báo sớm", warning_text, delta=warning_desc)
colC.metric("🎭 Cảm xúc hôm nay", "Chưa ghi")

if pgi_components:
    with st.expander("🔍 4 thành phần PGI (đề xuất bởi nhóm nghiên cứu)"):
        for k, v in pgi_components.items():
            st.progress(v/100, text=f"{k}: {v}/100")

if warning_color == "red":
    st.error(f"🚨 CẢNH BÁO ĐỎ: {warning_desc} - Robot sẽ nhấp nháy")
elif warning_color == "orange":
    st.warning(f"⚠️ CẢNH BÁO CAM: {warning_desc}")
elif warning_color == "yellow":
    st.warning(f"⚠️ CẢNH BÁO VÀNG: {warning_desc}")
else:
    st.success(f"✅ TRẠNG THÁI XANH: {warning_desc}")

# ==================== NHẮC NHỞ MỤC TIÊU ====================
goals = load_goals(user)
if goals:
    overdue_goals = [g for g in goals if g["progress"] < 50 and g.get("created_at", dt.now().isoformat()) < (dt.now() - timedelta(days=7)).isoformat()]
    if overdue_goals:
        st.warning("⏰ Một số mục tiêu đã quá 7 ngày nhưng tiến độ dưới 50%:")
        for g in overdue_goals:
            st.write(f"- {g['name']} ({g['progress']}%)")

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📝 Nhật ký", 
    "🧠 AI Insight", 
    "🎯 Mục tiêu", 
    "📊 Thống kê", 
    "💬 Chat AI", 
    "👥 Kết nối",
    "🤖 Robot"
])

# --- Tab 1: Nhật ký ---
with tab1:
    with st.form("journal_form"):
        work = st.text_area("Hôm nay bạn đã làm gì?")
        mood = st.select_slider("Cảm xúc", options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"])
        image_url = st.text_input("🔗 Link ảnh (không bắt buộc)", placeholder="https://...")
        submitted = st.form_submit_button("💾 Lưu nhật ký")
    if submitted and work:
        entry = {"date": dt.now().isoformat(), "content": work, "mood": mood, "image": image_url if image_url else ""}
        add_entry(user, entry)
        if any(kw in work.lower() for kw in STRESS_KEYWORDS):
            add_memory(user, f"Người dùng cảm thấy có dấu hiệu {', '.join([kw for kw in STRESS_KEYWORDS if kw in work.lower()])}")
        elif "vui" in work.lower() or "hạnh phúc" in work.lower():
            add_memory(user, "Người dùng ghi nhận niềm vui.")
        st.success("Đã lưu nhật ký!")
        with st.spinner("InnoMine đang phân tích..."):
            prompt = f"Người dùng viết: {work}. Cảm xúc: {mood}. Đưa ra nhận xét ngắn, không tâng bốc, chỉ ra xu hướng tích cực nếu có."
            try:
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.1-8b-instant", temperature=0.7)
                st.info(f"💡 {res.choices[0].message.content}")
            except:
                st.info("AI tạm thời bận.")
        st.rerun()
    journal = load_journal(user)
    if journal:
        for idx, entry in enumerate(reversed(journal[-10:])):
            d = entry["date"][:16]
            col1, col2 = st.columns([10, 1])
            with col1:
                st.markdown(f"**{d}** {entry['mood']}")
                st.write(entry['content'])
                if entry.get("image"):
                    st.image(entry["image"], width=250)
                st.markdown("---")
            with col2:
                if st.button("🗑️", key=f"del_journal_{idx}"):
                    delete_entry(user, len(journal) - idx - 1)
                    st.rerun()
    else:
        st.info("Chưa có nhật ký.")

# --- Tab 2: AI Insight ---
with tab2:
    memory = load_memory(user)
    if memory:
        st.subheader("🧠 Ký ức quan trọng")
        for mem in memory[-5:]:
            st.write(f"🔹 {mem['date'][:16]}: {mem['event']}")
    journal = load_journal(user)
    if len(journal) >= 3:
        st.subheader("Phân tích xu hướng")
        recent = journal[-5:]
        summary = "\n".join([f"- {e['content']} ({e['mood']})" for e in recent])
        prompt = f"Dựa trên nhật ký gần đây: {summary}\nLưu ý các sự kiện trong quá khứ: {memory[-3:] if memory else 'không có'}. Hãy nhận xét xu hướng cảm xúc và đưa gợi ý."
        with st.spinner("Đang phân tích..."):
            try:
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.1-8b-instant")
                st.info(res.choices[0].message.content)
            except:
                st.error("Lỗi AI.")
    else:
        st.info("Cần ít nhất 3 nhật ký để phân tích.")

# --- Tab 3: Mục tiêu ---
with tab3:
    goals = load_goals(user)
    with st.form("goal_form"):
        goal_name = st.text_input("Mục tiêu mới (ví dụ: Đọc 10 cuốn sách)")
        progress = st.slider("Tiến độ %", 0, 100, 0)
        submitted_goal = st.form_submit_button("Thêm/Cập nhật")
        if submitted_goal and goal_name:
            existing = {g["name"]: g for g in goals}
            existing[goal_name] = {"name": goal_name, "progress": progress, "created_at": dt.now().isoformat()}
            save_goals(user, list(existing.values()))
            st.rerun()
    if goals:
        for idx, g in enumerate(goals):
            col1, col2 = st.columns([10, 1])
            with col1:
                st.write(f"- {g['name']}: {g['progress']}%")
            with col2:
                if st.button("🗑️", key=f"del_goal_{idx}"):
                    delete_goal(user, idx)
                    st.rerun()
    else:
        st.info("Chưa có mục tiêu.")

# --- Tab 4: Thống kê ---
with tab4:
    journal = load_journal(user)
    if journal:
        df = pd.DataFrame(journal)
        df["date"] = pd.to_datetime(df["date"]).dt.date
        mood_counts = df.groupby(["date", "mood"]).size().reset_index(name="count")
        if not mood_counts.empty:
            fig = px.bar(mood_counts, x="date", y="count", color="mood", title="Cảm xúc theo ngày")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📊 Tỉ lệ cảm xúc trong 7 ngày qua")
        last_7 = df[df["date"] >= (dt.now().date() - timedelta(days=7))]
        if not last_7.empty:
            mood_pie = last_7["mood"].value_counts().reset_index()
            mood_pie.columns = ["mood", "count"]
            fig_pie = px.pie(mood_pie, names="mood", values="count", title="Phân bố cảm xúc tuần")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Chưa đủ dữ liệu 7 ngày.")
        
        st.subheader("Biểu đồ PGI")
        pgi_over_time = []
        for i in range(3, len(journal)+1):
            fake = journal[:i]
            scores = [MOOD_SCORE.get(e.get("mood", "😐 Bình thường"), 5) for e in fake]
            es = 100 - min(100, (max(scores)-min(scores))*10) if len(scores)>1 else 50
            cons = (len(set([e["date"][:10] for e in fake])) / 14)*100
            goals = load_goals(user)
            gc = sum([g["progress"] for g in goals])/len(goals) if goals else 0
            pos = sum(1 for e in fake if e.get("mood") in ["😊 Vui vẻ","😎 Tự tin","✨ Hy vọng"]) / len(fake)*100
            pgi_val = es*0.25 + cons*0.25 + gc*0.3 + pos*0.2
            pgi_over_time.append(round(pgi_val,1))
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=list(range(3, len(journal)+1)), y=pgi_over_time, mode='lines+markers', name='PGI'))
        fig2.update_layout(title="Chỉ số phát triển cá nhân theo thời gian")
        st.plotly_chart(fig2, use_container_width=True)
        
        if len(pgi_over_time) >= 5:
            x = list(range(len(pgi_over_time)))
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(pgi_over_time)
            sum_xy = sum(x[i]*pgi_over_time[i] for i in range(n))
            sum_x2 = sum(i*i for i in x)
            slope = (n*sum_xy - sum_x*sum_y) / (n*sum_x2 - sum_x*sum_x) if (n*sum_x2 - sum_x*sum_x) != 0 else 0
            intercept = (sum_y - slope*sum_x) / n
            next_pgi = slope * n + intercept
            st.metric("📈 Dự đoán PGI tiếp theo", f"{round(next_pgi, 1)}/100", delta=round(next_pgi - pgi_over_time[-1], 1))
        
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="📥 Tải xuống CSV (nhật ký)",
            data=csv_data,
            file_name=f"{user}_journal.csv",
            mime="text/csv"
        )
        
        if st.button("📄 Xuất báo cáo PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Báo cáo InnoMine-X của {user}", ln=1, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=10)
            for entry in journal[-10:]:
                pdf.cell(200, 10, txt=f"{entry['date'][:16]} - {entry['mood']}", ln=1)
                pdf.multi_cell(0, 10, txt=entry['content'][:200])
                pdf.ln(5)
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="⬇️ Tải PDF",
                data=pdf_output,
                file_name=f"{user}_report.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Chưa có dữ liệu.")

# --- Tab 5: Chat AI (có TTS) ---
with tab5:
    st.subheader("Trò chuyện cùng InnoMine")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        st.write(msg)
    user_msg = st.text_input("Bạn muốn nói gì?")
    if st.button("Gửi"):
        if user_msg:
            st.session_state.chat_history.append(f"**Bạn:** {user_msg}")
            with st.spinner("Đang trả lời..."):
                try:
                    res = client.chat.completions.create(messages=[{"role":"user","content":user_msg}], model="llama-3.1-8b-instant")
                    reply = res.choices[0].message.content
                    st.session_state.chat_history.append(f"**InnoMine:** {reply}")
                    # Lưu reply để đọc TTS
                    st.session_state.reply = reply
                except:
                    st.session_state.chat_history.append("**InnoMine:** Lỗi kết nối.")
            st.rerun()
    
    # Phát âm thanh phản hồi AI nếu có
    if "reply" in st.session_state and st.session_state.reply:
        render_tts(st.session_state.reply)

# --- Tab 6: Kết nối ---
with tab6:
    st.subheader("👥 Kết bạn")
    all_users = get_all_users()
    friends = get_friends(user)
    candidates = [u for u in all_users if u != user and u not in friends and u not in get_requests(user)]
    if candidates:
        target = st.selectbox("Chọn người dùng để kết bạn", candidates, key="target_tab6")
        if st.button("📨 Gửi lời mời", key="send_invite_tab6"):
            send_request(user, target)
            st.success(f"Đã gửi lời mời đến {target}!")
            st.rerun()
    else:
        st.info("Không có người dùng mới để kết bạn hoặc bạn đã gửi lời mời rồi.")
    
    st.markdown("---")
    st.subheader("✉️ Lời mời kết bạn đã nhận")
    reqs = get_requests(user)
    if reqs:
        for r in reqs:
            col1, col2 = st.columns([3,1])
            col1.write(r)
            if col2.button("✅ Chấp nhận", key=f"accept_tab6_{r}"):
                accept_request(user, r)
                st.rerun()
    else:
        st.info("Không có lời mời nào.")
    
    st.markdown("---")
    st.subheader("👥 Danh sách bạn bè")
    friends = get_friends(user)
    if friends:
        for f in friends:
            st.write(f"• {f}")
    else:
        st.info("Chưa có bạn bè. Hãy gửi lời mời ở trên.")
    
    st.markdown("---")
    st.subheader("💬 Chia sẻ khoảnh khắc")
    share_content = st.text_area("Viết điều bạn muốn chia sẻ", key="share_area")
    share_image = st.text_input("🔗 Link ảnh (không bắt buộc)", placeholder="https://...", key="share_image")
    if st.button("Chia sẻ", key="share_btn"):
        if share_content:
            post = {"date": dt.now().isoformat(), "content": share_content, "image": share_image if share_image else ""}
            add_shared_post(user, post)
            st.success("Đã chia sẻ!")
            st.rerun()
    
    st.markdown("### Bài viết từ bạn bè")
    for friend in get_friends(user):
        posts = get_shared_posts(friend)
        if posts:
            st.markdown(f"**{friend}**")
            for p in posts[:3]:
                st.write(f"- {p['content'][:100]}")
                if p.get("image"):
                    st.image(p["image"], width=200)

# --- Tab 7: Robot (có voice) ---
with tab7:
    st.subheader("🤖 Điều khiển InnoMine-X")
    
    # Kết nối robot
    robot_ip = st.text_input("Địa chỉ IP robot:", st.session_state.robot_ip)
    if st.button("🔗 Kết nối"):
        try:
            response = requests.get(f"http://{robot_ip}/capture", timeout=3)
            if response.status_code == 200:
                st.session_state.robot_ip = robot_ip
                st.session_state.robot_connected = True
                st.success("✅ Kết nối robot thành công!")
            else:
                st.error("❌ Lỗi kết nối")
        except:
            st.error("❌ Không kết nối được robot")
    
    if st.session_state.get("robot_connected", False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💡 LED")
            if st.button("😊 Vui", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_vui")
                    st.success("✅ LED Vui")
                except:
                    st.error("❌ Lỗi")
            if st.button("😢 Buồn", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_buon")
                    st.success("✅ LED Buồn")
                except:
                    st.error("❌ Lỗi")
            if st.button("⏹ Tắt LED", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=led_off")
                    st.success("✅ Tắt LED")
                except:
                    st.error("❌ Lỗi")
        
        with col2:
            st.markdown("#### ⚡ Relay & Rung")
            if st.button("🔴 Bật Relay", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=relay_on")
                    st.success("✅ Bật Relay")
                except:
                    st.error("❌ Lỗi")
            if st.button("⚫ Tắt Relay", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=relay_off")
                    st.success("✅ Tắt Relay")
                except:
                    st.error("❌ Lỗi")
            if st.button("📳 Bật Rung", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=rung_on")
                    st.success("✅ Bật Rung")
                except:
                    st.error("❌ Lỗi")
            if st.button("📳 Tắt Rung", use_container_width=True):
                try:
                    requests.get(f"http://{st.session_state.robot_ip}/control?action=rung_off")
                    st.success("✅ Tắt Rung")
                except:
                    st.error("❌ Lỗi")
        
        st.markdown("#### 📷 Camera")
        if st.button("📸 Chụp ảnh"):
            try:
                response = requests.get(f"http://{st.session_state.robot_ip}/capture", timeout=5)
                if response.status_code == 200:
                    img = Image.open(io.BytesIO(response.content))
                    st.image(img, caption="📷 Ảnh từ robot")
                    st.success("✅ Đã chụp ảnh!")
                else:
                    st.error("❌ Lỗi chụp ảnh")
            except:
                st.error("❌ Lỗi kết nối")
        
        # Hiển thị hoạt động robot
        if st.session_state.robot_activities:
            st.markdown("#### 📋 Hoạt động gần đây")
            for act in st.session_state.robot_activities[-5:]:
                st.write(f"- {act['time']}: {act['activity']} (cảm xúc: {act['emotion']})")
    
    # ===== PHẦN VOICE ĐIỀU KHIỂN ROBOT (THÊM MỚI) =====
    st.markdown("---")
    st.markdown("#### 🎤 Điều khiển robot bằng giọng nói")
    st.write("Nhấn nút và nói lệnh (ví dụ: 'Bật LED vui', 'Tắt rung', 'Bật Relay')")
    st.components.v1.html(get_speech_html(), height=200)
    
    # ===== TẠO LỘ TRÌNH HỌC TẬP =====
    def generate_learning_path():
        activities = st.session_state.get("robot_activities", [])
        journal = load_journal(user)
        study_time = 0
        rest_time = 0
        for act in activities[-20:]:
            if "học" in act.get("activity", "").lower():
                study_time += 1
            elif "nghỉ" in act.get("activity", "").lower():
                rest_time += 1
        suggestions = []
        if journal:
            recent = journal[-5:]
            sad_count = sum(1 for e in recent if e.get("mood") in ["😢 Buồn"])
            if sad_count >= 3:
                suggestions.append("😢 Bạn có dấu hiệu mệt mỏi. Hãy dành thời gian nghỉ ngơi và thư giãn.")
        if study_time > 10:
            suggestions.append("📚 Bạn đã học nhiều! Hãy nghỉ 15 phút và vận động nhẹ.")
        elif study_time < 3:
            suggestions.append("📖 Hôm nay bạn chưa học nhiều. Hãy dành ít nhất 1 tiếng để ôn bài.")
        if rest_time < 2:
            suggestions.append("😴 Bạn cần nghỉ ngơi nhiều hơn. Hãy ngủ đủ 7-8 tiếng mỗi ngày.")
        if not suggestions:
            suggestions.append("🌟 Bạn đang có lịch trình tốt! Hãy duy trì nhé.")
        return suggestions
    
    if st.button("🔄 Tạo lộ trình học tập"):
        suggestions = generate_learning_path()
        st.session_state.learning_path = suggestions
    
    if "learning_path" in st.session_state and st.session_state.learning_path:
        st.subheader("📝 Lộ trình học tập đề xuất")
        for i, suggestion in enumerate(st.session_state.learning_path, 1):
            st.write(f"{i}. {suggestion}")
    
    # Ghi nhận hoạt động thủ công
    st.markdown("#### 📝 Ghi nhận hoạt động (mô phỏng)")
    activity_input = st.text_input("Nhập hoạt động bạn vừa làm (ví dụ: học Toán, nghỉ ngơi, ...)")
    emotion_input = st.selectbox("Cảm xúc khi đó", ["😊 Vui", "😐 Bình thường", "😢 Buồn", "🤔 Suy tư"])
    if st.button("Ghi nhận"):
        if activity_input:
            st.session_state.robot_activities.append({
                "time": dt.now().isoformat(),
                "activity": activity_input,
                "emotion": emotion_input
            })
            st.success("Đã ghi nhận hoạt động!")
            st.rerun()

# ==================== FOOTER ====================
st.sidebar.markdown("---")
st.sidebar.caption("InnoMine-X | Hệ thống AI & Robot")

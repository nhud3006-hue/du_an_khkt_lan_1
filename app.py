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

# ==================== CẤU HÌNH TRANG ====================
st.set_page_config(page_title="InnoMine-X", page_icon="🧠", layout="wide")
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;400;500;600;700&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #F8FAFF 0%, #EEF2FF 100%); }
    header, footer { visibility: hidden; }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .journal-entry {
        background: white;
        border-radius: 24px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #3B82F6;
        transition: 0.15s;
    }
    .stButton button {
        border-radius: 40px !important;
        background: #3B82F6 !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton button:hover { background: #2563EB !important; transform: scale(1.02); }
    .warning-green { background: #D1FAE5; border-left: 6px solid #10B981; padding: 0.75rem; border-radius: 16px; margin: 0.5rem 0; }
    .warning-yellow { background: #FEF3C7; border-left: 6px solid #F59E0B; padding: 0.75rem; border-radius: 16px; margin: 0.5rem 0; }
    .warning-orange { background: #FFEDD5; border-left: 6px solid #EA580C; padding: 0.75rem; border-radius: 16px; margin: 0.5rem 0; }
    .warning-red { background: #FEE2E2; border-left: 6px solid #DC2626; padding: 0.75rem; border-radius: 16px; margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ==================== GLOBAL CONSTANTS ====================
MOOD_SCORE = {"😢 Buồn": 2, "😐 Bình thường": 5, "😊 Vui vẻ": 8, "🤔 Suy tư": 6, "😎 Tự tin": 9, "✨ Hy vọng": 9}
STRESS_KEYWORDS = ["stress", "áp lực", "mệt mỏi", "căng thẳng", "lo lắng", "mất ngủ", "cô đơn", "buồn"]

# ==================== HASH MẬT KHẨU ====================
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

# ==================== QUẢN LÝ USER ====================
USER_FILE = "users.json"
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({"minh": hash_password("123"), "lan": hash_password("456"), "huy": hash_password("789")}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)
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
    return True
def accept_request(u, req):
    reqs = get_requests(u)
    if req in reqs:
        reqs.remove(req)
        with open(f"{u}_requests.json", "w") as f:
            json.dump(reqs, f)
        add_friend(u, req)
        add_friend(req, u)
        return True
    return False
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

# ==================== NHẬT KÝ & MỤC TIÊU ====================
def load_journal(u):
    fname = f"{u}_journal.json"
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
def save_journal(u, data):
    with open(f"{u}_journal.json", "w", encoding="utf-8") as f:
        json.dump(data, f)
def add_entry(u, entry):
    data = load_journal(u)
    data.append(entry)
    save_journal(u, data)

def load_goals(u):
    fname = f"{u}_goals.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []
def save_goals(u, goals):
    with open(f"{u}_goals.json", "w") as f:
        json.dump(goals, f)

# ==================== MEMORY ENGINE ====================
def load_memory(u):
    fname = f"{u}_memory.json"
    if os.path.exists(fname):
        with open(fname, "r") as f:
            return json.load(f)
    return []
def save_memory(u, memory):
    with open(f"{u}_memory.json", "w") as f:
        json.dump(memory, f)
def add_memory(u, event):
    mem = load_memory(u)
    mem.append({"date": dt.now().isoformat(), "event": event})
    save_memory(u, mem[-20:])

# ==================== TÍNH TOÁN PGI ====================
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

# ==================== ROBOT COMPANION ====================
if "robot_led" not in st.session_state:
    st.session_state.robot_led = False
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
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 class='main-title'>🧠 InnoMine-X</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center'>Hệ thống AI & Robot đồng hành hỗ trợ sức khỏe tinh thần học sinh</p>", unsafe_allow_html=True)
        option = st.radio("", ["🔐 Đăng nhập", "🆕 Đăng ký"])
        if option == "🔐 Đăng nhập":
            u = st.text_input("Tên đăng nhập")
            p = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập", use_container_width=True):
                if authenticate(u, p):
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Sai tên hoặc mật khẩu.")
        else:
            u = st.text_input("Tên mới")
            p = st.text_input("Mật khẩu", type="password")
            c = st.text_input("Xác nhận mật khẩu", type="password")
            if st.button("Đăng ký", use_container_width=True):
                if u and p and p == c and u.isalnum():
                    if register_user(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("Tên đã tồn tại.")
                else:
                    st.error("Thông tin không hợp lệ.")
    st.stop()

user = st.session_state.username
avatar = "🧠"

# ==================== SIDEBAR (chỉ hiển thị lời mời và danh sách bạn bè) ====================
st.sidebar.markdown(f"### {avatar} {user}")
st.sidebar.markdown("---")

# Lời mời kết bạn
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

# Danh sách bạn bè
st.sidebar.markdown("### 👥 Bạn bè")
friends = get_friends(user)
if friends:
    for f in friends:
        st.sidebar.write(f"• {f}")
else:
    st.sidebar.info("Chưa có bạn bè.")
st.sidebar.markdown("---")

# ==================== DASHBOARD ====================
st.markdown(f"<h1 class='main-title'>Chào {user} 👋</h1>", unsafe_allow_html=True)
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
    st.markdown(f"<div class='warning-red'><strong>⚠️ CẢNH BÁO ĐỎ:</strong> {warning_desc}<br>🤖 Robot sẽ nhấp nháy. Hãy trò chuyện với AI hoặc tìm sự hỗ trợ.</div>", unsafe_allow_html=True)
elif warning_color == "orange":
    st.markdown(f"<div class='warning-orange'><strong>⚠️ CẢNH BÁO CAM:</strong> {warning_desc}</div>", unsafe_allow_html=True)
elif warning_color == "yellow":
    st.markdown(f"<div class='warning-yellow'><strong>⚠️ CẢNH BÁO VÀNG:</strong> {warning_desc}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='warning-green'><strong>✅ TRẠNG THÁI XANH:</strong> {warning_desc}</div>", unsafe_allow_html=True)

# ==================== TABS ====================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Nhật ký", "🧠 AI Insight", "🎯 Mục tiêu", "📊 Thống kê", "💬 Chat AI", "👥 Kết nối"])

# --- Tab 1: Nhật ký ---
with tab1:
    with st.form("journal_form"):
        work = st.text_area("Hôm nay bạn đã làm gì?")
        mood = st.select_slider("Cảm xúc", options=["😢 Buồn", "😐 Bình thường", "😊 Vui vẻ", "🤔 Suy tư", "😎 Tự tin", "✨ Hy vọng"])
        submitted = st.form_submit_button("💾 Lưu nhật ký")
    if submitted and work:
        entry = {"date": dt.now().isoformat(), "content": work, "mood": mood}
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
        for entry in reversed(journal[-10:]):
            d = entry["date"][:16]
            st.markdown(f"""
            <div class='journal-entry'>
                <div><strong>{d}</strong>  {entry['mood']}</div>
                <div>{entry['content']}</div>
            </div>
            """, unsafe_allow_html=True)
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
        if st.form_submit_button("Thêm/Cập nhật"):
            existing = {g["name"]: g for g in goals}
            existing[goal_name] = {"name": goal_name, "progress": progress}
            save_goals(user, list(existing.values()))
            st.rerun()
    if goals:
        for g in goals:
            st.write(f"- {g['name']}: {g['progress']}%")
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
        st.subheader("Biểu đồ PGI (dữ liệu thực tế)")
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
    else:
        st.info("Chưa có dữ liệu.")

# --- Tab 5: Chat AI ---
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
                except:
                    st.session_state.chat_history.append("**InnoMine:** Lỗi kết nối.")
            st.rerun()

# --- Tab 6: Kết nối (kết bạn + chia sẻ) ---
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
    share_content = st.text_area("Viết điều bạn muốn chia sẻ với bạn bè", key="share_area")
    if st.button("Chia sẻ", key="share_btn"):
        if share_content:
            post = {"date": dt.now().isoformat(), "content": share_content}
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

# ==================== FOOTER (sidebar) ====================
st.sidebar.markdown("---")
st.sidebar.caption("InnoMine-X | Hệ thống AI & Robot đồng hành | Bản demo chính thức")

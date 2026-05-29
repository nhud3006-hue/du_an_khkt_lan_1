import streamlit as st
from groq import Groq

st.set_page_config(page_title="InnoMine", page_icon="🤖")
st.title("🤖 InnoMine - Nhật ký của em")

# Kiểm tra API Key từ Secrets
if "GROQ_API_KEY" not in st.secrets:
    st.error("Lỗi: Chưa tìm thấy GROQ_API_KEY trong phần Secrets!")
    st.stop()

# Khởi tạo client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Giao diện
nhat_ky = st.text_area("Hôm nay em làm gì?")
cam_xuc = st.text_input("Cảm xúc của em hôm nay là gì?")

if st.button("Lưu & Phân tích"):
    if nhat_ky and cam_xuc:
        with st.spinner("AI đang lắng nghe và suy nghĩ..."):
            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Bạn là một người bạn tâm giao, đưa ra lời khuyên nhẹ nhàng, ngắn gọn và sâu sắc."},
                        {"role": "user", "content": f"Nhật ký: {nhat_ky}. Cảm xúc: {cam_xuc}. Hãy đưa cho tôi lời khuyên."}
                    ],
                    model="llama-3.1-8b-instant", # Model ổn định nhất hiện nay
                )
                st.success(chat_completion.choices[0].message.content)
            except Exception as e:
                st.error(f"Lỗi kết nối AI: {e}")
    else:
        st.warning("Em nhớ điền đủ cả 2 ô nhé!")

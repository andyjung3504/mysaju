import streamlit as st
import sqlite3
import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 정통 만세력", page_icon="🔮", layout="wide")

# --- 상수 데이터 (오행, 십성 로직) ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_COLOR = {
    "목": "#4CAF50", "화": "#FF5722", "토": "#FFC107", "금": "#9E9E9E", "수": "#2196F3"
}
GAN_OHAENG = {"甲":"목", "乙":"목", "丙":"화", "丁":"화", "戊":"토", "己":"토", "庚":"금", "辛":"금", "壬":"수", "癸":"수"}
JI_OHAENG = {"子":"수", "丑":"토", "寅":"목", "卯":"목", "辰":"토", "巳":"화", "午":"화", "未":"토", "申":"금", "酉":"금", "戌":"토", "亥":"수"}

# --- 함수: 시주 계산 (시두법) ---
def get_time_pillar(day_gan, hour_ji):
    ji_list = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    if hour_ji not in ji_list: return ""
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    start_idx = start_idx_map.get(day_gan, 0)
    ji_idx = ji_list.index(hour_ji)
    final_gan_idx = (start_idx + ji_idx) % 10
    return GAN[final_gan_idx]

# --- 함수: 십성(Sipseong) 계산 ---
def get_ten_gods(day_gan, target_gan):
    if not target_gan: return ""
    # 오행 인덱스 (목0 화1 토2 금3 수4)
    order = ["목", "화", "토", "금", "수"]
    d_oh = GAN_OHAENG.get(day_gan, JI_OHAENG.get(day_gan)) # 지지가 들어올 수도 있음
    t_oh = GAN_OHAENG.get(target_gan, JI_OHAENG.get(target_gan))
    
    if not d_oh or not t_oh: return ""

    d_idx = order.index(d_oh)
    t_idx = order.index(t_oh)
    diff = (t_idx - d_idx) % 5
    
    # 음양 계산 (천간 기준: 갑병무경임+, 을정기신계- / 지지: 자인진오신술+, 축묘사미유해-)
    # 간단하게 리스트 인덱스의 홀짝으로 구분
    gan_all = GAN + JI
    d_yy = gan_all.index(day_gan) % 2
    t_yy = gan_all.index(target_gan) % 2
    same_yy = (d_yy == t_yy)

    if diff == 0: return "비견" if same_yy else "겁재"
    if diff == 1: return "식신" if same_yy else "상관"
    if diff == 2: return "편재" if same_yy else "정재"
    if diff == 3: return "편관" if same_yy else "정관"
    if diff == 4: return "편인" if same_yy else "정인"
    return ""

# --- UI 메인 ---
st.title("🔮 AI 정통 만세력 (Pro)")
st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    d = st.date_input("양력 생일", datetime.date(1990, 1, 1), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
with col2:
    t = st.selectbox("태어난 시간", ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"])
with col3:
    st.write("") # 여백
    st.write("") 
    btn = st.button("운세 분석 시작", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gan, y_kr, m_gan, m_kr, d_gan, d_kr = row
        
        # 1. 시주 계산
        day_master = d_gan[0] # 일간 (예: 甲)
        time_gan = get_time_pillar(day_master, t)
        time_pillar = f"{time_gan}{t}"
        time_ji_kr = t # 한글 지지

        # 2. 십성 계산 (일간 기준)
        # 천간 십성
        ten_y_gan = get_ten_gods(day_master, y_gan[0])
        ten_m_gan = get_ten_gods(day_master, m_gan[0])
        ten_t_gan = get_ten_gods(day_master, time_gan)
        
        # 지지 십성
        ten_y_ji = get_ten_gods(day_master, y_gan[1])
        ten_m_ji = get_ten_gods(day_master, m_gan[1])
        ten_d_ji = get_ten_gods(day_master, d_gan[1])
        ten_t_ji = get_ten_gods(day_master, datetime.time) # 임시

        # 3. 화면 출력 (카드 스타일)
        st.success(f"🗓️ 양력 {d.year}년 {d.month}월 {d.day}일 {t}시생 사주명식")
        
        # 스타일링을 위한 CSS
        st.markdown("""
        <style>
        .card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ddd; }
        .big-text { font-size: 24px; font-weight: bold; }
        .sub-text { font-size: 14px; color: #555; }
        .ten-god { font-size: 12px; color: #e91e63; font-weight: bold; display: block; margin-bottom: 5px;}
        </style>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        
        def draw_card(col, title, gan, ji, t_gan, t_ji):
            with col:
                st.markdown(f"""
                <div class="card">
                    <div class="sub-text">{title}</div>
                    <div class="ten-god">{t_gan}</div>
                    <div class="big-text" style="color:{OHAENG_COLOR.get(GAN_OHAENG.get(gan, '목'), '#000')}">{gan}</div>
                    <div class="big-text" style="color:{OHAENG_COLOR.get(JI_OHAENG.get(ji, '목'), '#000')}">{ji}</div>
                    <div class="ten-god">{t_ji}</div>
                </div>
                """, unsafe_allow_html=True)

        # 시/일/월/연 순서 출력
        # 지지 십성은 간략화를 위해 임시 로직 적용 (JI_OHAENG 매핑 필요)
        # (실제로는 지지->오행->십성 변환 로직이 완벽해야 함, 위 함수 사용)
        t_ji_ten = get_ten_gods(day_master, list(JI_OHAENG.keys())[["자","축","인","묘","진","사","오","미","신","유","술","해"].index(t)])
        
        draw_card(c1, "시주 (자녀)", time_gan, t, ten_t_gan, t_ji_ten)
        draw_card(c2, "일주 (본인)", d_gan[0], d_gan[1], "일간(나)", ten_d_ji)
        draw_card(c3, "월주 (사회)", m_gan[0], m_gan[1], ten_m_gan, ten_m_ji)
        draw_card(c4, "연주 (조상)", y_gan[0], y_gan[1], ten_y_gan, ten_y_ji)
        
        st.markdown("---")
        st.info(f"당신의 핵심 성향(일주)은 **'{d_gan[0]}({d_kr[0]})'** 입니다. 이는 **{GAN_OHAENG[d_gan[0]]}**의 기운을 타고났음을 의미합니다.")

    else:
        st.error("데이터 조회 실패")

import streamlit as st
import sqlite3
import datetime
from datetime import timedelta
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS (디자인 핵심) ---
st.set_page_config(page_title="AI 정통 만세력", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #f5f7f9; }
    
    /* 사주 카드 컨테이너 */
    .pillar-card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        padding: 0;
        margin: 5px;
        overflow: hidden;
        text-align: center;
    }
    
    /* 카드 헤더 (시주, 일주 등) */
    .card-header {
        background-color: #f1f3f5;
        color: #495057;
        font-size: 14px;
        font-weight: bold;
        padding: 8px 0;
        border-bottom: 1px solid #e1e4e8;
    }
    
    /* 십성 (육친) 태그 */
    .ten-god-tag {
        font-size: 11px;
        color: #868e96;
        margin-top: 8px;
        margin-bottom: 2px;
        font-weight: bold;
    }
    
    /* 한자 스타일 (천간/지지) */
    .hanja {
        font-family: 'KoPub Batang', serif;
        font-size: 36px;
        font-weight: 900;
        line-height: 1.1;
    }
    
    /* 지장간 (작은 글씨) */
    .jijanggan {
        font-size: 11px;
        color: #adb5bd;
        margin: 5px 0;
        letter-spacing: 2px;
    }

    /* 12운성 및 신살 박스 */
    .bottom-info {
        background-color: #f8f9fa;
        padding: 8px 0;
        border-top: 1px dashed #e1e4e8;
    }
    .unseong { font-size: 13px; color: #495057; font-weight: bold; }
    .shinsal { font-size: 11px; color: #e03131; margin-top: 2px; font-weight: bold; }
    
    /* 오행 색상 */
    .wood { color: #51cf66; } /* 목 - 초록 */
    .fire { color: #ff6b6b; } /* 화 - 빨강 */
    .earth { color: #fcc419; } /* 토 - 노랑 */
    .metal { color: #adb5bd; } /* 금 - 회색 */
    .water { color: #339af0; } /* 수 - 파랑 */
    
</style>
""", unsafe_allow_html=True)

# --- 2. 기초 데이터 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_MAP = {
    "甲":"wood", "乙":"wood", "寅":"wood", "卯":"wood",
    "丙":"fire", "丁":"fire", "巳":"fire", "午":"fire",
    "戊":"earth", "己":"earth", "辰":"earth", "戌":"earth", "丑":"earth", "未":"earth",
    "庚":"metal", "辛":"metal", "申":"metal", "酉":"metal",
    "壬":"water", "癸":"water", "亥":"water", "子":"water"
}
OHAENG_KR = {"wood":"목", "fire":"화", "earth":"토", "metal":"금", "water":"수"}

# 지장간 데이터 (여기, 중기, 본기)
JIJANGGAN = {
    "子": "壬 癸", "丑": "癸 辛 己", "寅": "戊 丙 甲", "卯": "甲 乙",
    "辰": "乙 癸 戊", "巳": "戊 庚 丙", "午": "丙 己 丁", "未": "丁 乙 己",
    "申": "戊 壬 庚", "酉": "庚 辛", "戌": "辛 丁 戊", "亥": "戊 甲 壬"
}

# 12운성 테이블
UNSEONG_TABLE = {
    "甲": ["목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양","장생"], 
    "乙": ["병","쇠","제왕","건록","관대","목욕","장생","양","태","절","묘","사"],
    "丙": ["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "丁": ["절","묘","사","병","쇠","제왕","건록","관대","목욕","장생","양","태"],
    "戊": ["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "己": ["절","묘","사","병","쇠","제왕","건록","관대","목욕","장생","양","태"],
    "庚": ["사","묘","절","태","양","장생","목욕","관대","건록","제왕","쇠","병"],
    "辛": ["장생","양","태","절","묘","사","병","쇠","제왕","건록","관대","목욕"],
    "壬": ["제왕","쇠","병","사","묘","절","태","양","장생","목욕","관대","건록"],
    "癸": ["건록","제왕","쇠","병","사","묘","절","태","양","장생","목욕","관대"]
}

# 주요 도시 경도
LOCATIONS = {
    "서울/경기": 127.0, "강원(강릉)": 128.9, "강원(춘천)": 127.7,
    "대전/충남": 127.4, "충북(청주)": 127.5, "광주/전남": 126.8, "전북(전주)": 127.1,
    "부산/경남": 129.1, "대구/경북": 128.6, "울산": 129.3, "제주": 126.5, "인천": 126.7
}

# --- 3. 로직 함수들 ---

def calculate_time_ji(hour, minute, location_name):
    """진태양시 계산"""
    longitude = LOCATIONS.get(location_name, 127.0)
    correction = (longitude - 135.0) * 4
    total_min = hour * 60 + minute + correction
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    idx = int((total_min + 60) // 120) % 12
    return JI[idx], total_min

def get_time_pillar_gan(day_gan, time_ji):
    """시간 도출"""
    if time_ji not in JI: return "甲"
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    return GAN[(start_idx_map.get(day_gan, 0) + JI.index(time_ji)) % 10]

def get_sibseong(day_gan, target_char):
    """십성 계산"""
    if not target_char: return ""
    o_map = {"wood":0, "fire":1, "earth":2, "metal":3, "water":4}
    try:
        d_oh = o_map[OHAENG_MAP[day_gan]]
        t_oh = o_map[OHAENG_MAP[target_char]]
    except: return ""
    
    gan_all = GAN + JI
    d_yy = gan_all.index(day_gan) % 2
    t_yy = gan_all.index(target_char) % 2
    same_yy = (d_yy == t_yy)
    
    diff = (t_oh - d_oh) % 5
    if diff == 0: return "비견" if same_yy else "겁재"
    if diff == 1: return "식신" if same_yy else "상관"
    if diff == 2: return "편재" if same_yy else "정재"
    if diff == 3: return "편관" if same_yy else "정관"
    if diff == 4: return "편인" if same_yy else "정인"

def get_unseong(day_gan, target_ji):
    return UNSEONG_TABLE[day_gan][JI.index(target_ji)] if target_ji in JI else ""

def get_shinsal(day_ji, target_ji):
    # 간단 신살 로직
    if day_ji in ["亥","卯","未"] and target_ji == "子": return "도화살"
    if day_ji in ["寅","午","戌"] and target_ji == "卯": return "도화살"
    if day_ji in ["巳","酉","丑"] and target_ji == "午": return "도화살"
    if day_ji in ["申","子","辰"] and target_ji == "酉": return "도화살"
    if target_ji in ["辰","戌","丑","未"]: return "화개살"
    if target_ji in ["寅","申","巳","亥"]: return "역마살"
    if day_ji == target_ji: return "지살" # 임시
    return ""

def calculate_daewoon_num(birth_date, is_forward, current_month_ganji):
    """대운수 계산"""
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_sy, cd_sm, cd_sd, cd_kyganjee FROM calenda_data WHERE cd_sy BETWEEN ? AND ?", (birth_date.year-1, birth_date.year+1))
    rows = cur.fetchall()
    conn.close()
    
    if not rows: return 5
    df = pd.DataFrame(rows, columns=['y', 'm', 'd', 'month_ganji'])
    df['date'] = pd.to_datetime(df[['y', 'm', 'd']].astype(str).agg('-'.join, axis=1))
    
    birth_ts = pd.Timestamp(birth_date)
    target_date = None

    if is_forward:
        future = df[df['date'] > birth_ts].sort_values('date')
        for _, row in future.iterrows():
            if row['month_ganji'] != current_month_ganji:
                target_date = row['date']; break
    else:
        past = df[df['date'] <= birth_ts].sort_values('date', ascending=False)
        for _, row in past.iterrows():
            if row['month_ganji'] != current_month_ganji:
                target_date = row['date']; break
        if target_date is None and not past.empty: target_date = past.iloc[-1]['date']

    if target_date is None: return 5
    daewoon_num = round(abs((birth_ts - target_date).days) / 3)
    return 1 if daewoon_num == 0 else daewoon_num

def get_daewoon_list(year_gan, year_ji, month_gan, month_ji, gender, birth_date):
    is_yang = (GAN.index(year_gan) % 2 == 0)
    is_man = (gender == "남자")
    is_forward = (is_yang and is_man) or (not is_yang and not is_man)
    
    dw_num = calculate_daewoon_num(birth_date, is_forward, f"{month_gan}{month_ji}")
    
    s_gan_idx = GAN.index(month_gan)
    s_ji_idx = JI.index(month_ji)
    
    lst = []
    for i in range(1, 9):
        step = i if is_forward else -i
        g = GAN[(s_gan_idx + step) % 10]
        j = JI[(s_ji_idx + step) % 12]
        lst.append({"나이": dw_num + (i-1)*10, "간지": f"{g}{j}", "육친": get_sibseong(year_gan, g)}) # 예시 육친
        
    return lst, "순행" if is_forward else "역행", dw_num

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🔮 사주 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("태어난 시간", datetime.time(6, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    btn = st.button("분석하기", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gj, y_kr, m_gj, m_kr, d_gj, d_kr = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        real_ji, s_min = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_pillar_gan(d_g, real_ji)
        t_j = real_ji
        
        day_master = d_g
        
        dw_list, dw_dir, dw_num = get_daewoon_list(y_g, y_j, m_g, m_j, gender, d)
        
        st.header(f"{name}님의 사주명식")
        st.markdown(f"**양력** {d.year}.{d.month}.{d.day} / **진태양시** {int(s_min//60):02d}:{int(s_min%60):02d} ({t_j}시)")
        
        # [사주 4기둥 카드 출력] - 여기가 핵심 디자인 부분
        cols = st.columns(4)
        pillars = [
            {"name": "시주 (말년)", "g": t_g, "j": t_j},
            {"name": "일주 (본인)", "g": d_g, "j": d_j},
            {"name": "월주 (사회)", "g": m_g, "j": m_j},
            {"name": "연주 (초년)", "g": y_g, "j": y_j},
        ]
        
        for i, col in enumerate(cols):
            p = pillars[i]
            
            # 십성 계산
            ten_g = "일간" if i == 1 else get_sibseong(day_master, p['g'])
            ten_j = get_sibseong(day_master, p['j'])
            
            # 스타일 클래스
            c_g = OHAENG_MAP[p['g']]
            c_j = OHAENG_MAP[p['j']]
            
            # 지장간/운성/신살
            jijang = JIJANGGAN.get(p['j'], "")
            unseong = get_unseong(day_master, p['j'])
            shinsal = get_shinsal(d_j, p['j'])
            
            # HTML 렌더링
            col.markdown(f"""
            <div class="pillar-card">
                <div class="card-header">{p['name']}</div>
                <div class="ten-god-tag">{ten_g}</div>
                <div class="hanja {c_g}">{p['g']}</div>
                <div class="hanja {c_j}">{p['j']}</div>
                <div class="jijanggan">{jijang}</div>
                <div class="ten-god-tag">{ten_j}</div>
                <div class="bottom-info">
                    <div class="unseong">{unseong}</div>
                    <div class="shinsal">{shinsal}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        
        # [대운 및 오행 차트]
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader(f"대운 (대운수 {dw_num}, {dw_dir})")
            dw_df = pd.DataFrame(dw_list)
            st.dataframe(dw_df.set_index("나이").T, use_container_width=True)
            
        with c2:
            st.subheader("오행 분포")
            all_c = [y_g, y_j, m_g, m_j, d_g, d_j, t_g, t_j]
            cnt = {"목":0, "화":0, "토":0, "금":0, "수":0}
            for c in all_c: cnt[OHAENG_KR[OHAENG_MAP[c]]] += 1
            
            df_oh = pd.DataFrame({"오행":cnt.keys(), "개수":cnt.values(), "색상":["#51cf66","#ff6b6b","#fcc419","#adb5bd","#339af0"]})
            
            chart = alt.Chart(df_oh).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("개수", stack=True),
                color=alt.Color("오행", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#51cf66","#ff6b6b","#fcc419","#adb5bd","#339af0"]))
            )
            st.altair_chart(chart, use_container_width=True)

    else:
        st.error("데이터 조회 실패")

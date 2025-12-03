import streamlit as st
import sqlite3
import datetime
from datetime import timedelta
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 스타일 ---
st.set_page_config(page_title="AI 정통 만세력 (Pro)", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .saju-card {
        background-color: white; border-radius: 15px; padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin: 5px;
        border: 1px solid #e0e0e0;
    }
    .pillar-title { font-size: 14px; color: #666; margin-bottom: 10px; font-weight: bold; }
    .gan-ji { font-size: 32px; font-weight: 900; line-height: 1.2; font-family: 'Serif'; }
    .ten-god { font-size: 12px; font-weight: bold; color: #555; background-color: #eee; border-radius: 5px; padding: 2px 6px; display: inline-block; margin-bottom: 2px; }
    .unseong { font-size: 13px; color: #888; margin-top: 5px; display: block; }
    .shinsal { font-size: 12px; color: #e91e63; margin-top: 2px; display: block; font-weight: bold; }
    .wood { color: #4CAF50; } .fire { color: #E91E63; } .earth { color: #FFC107; } .metal { color: #9E9E9E; } .water { color: #2196F3; }
</style>
""", unsafe_allow_html=True)

# --- 2. 상수 데이터 ---
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

# 주요 도시 경도 데이터 (진태양시 계산용)
LOCATIONS = {
    "서울/경기": 127.0,
    "강원(강릉)": 128.9, "강원(춘천)": 127.7,
    "대전/충남": 127.4, "충북(청주)": 127.5,
    "광주/전남": 126.8, "전북(전주)": 127.1,
    "부산/경남": 129.1, "대구/경북": 128.6,
    "울산": 129.3, "제주": 126.5,
    "인천": 126.7
}

# --- 3. 핵심 로직 함수들 ---

def calculate_time_ji(hour, minute, location_name):
    """
    [핵심] 입력된 시간과 지역(경도)을 이용하여 '진태양시'를 계산하고 12지지를 반환
    공식: 진태양시 = 평균태양시 + (해당지역경도 - 표준자오선135) * 4분
    """
    longitude = LOCATIONS.get(location_name, 127.0) # 기본값 서울
    standard_meridian = 135.0 # 한국 표준시 기준 (동경 135도)
    
    # 1. 경도 보정값 계산 (분 단위)
    correction_minutes = (longitude - standard_meridian) * 4
    
    # 2. 입력 시간을 분으로 환산 후 보정
    total_minutes = hour * 60 + minute + correction_minutes
    
    # 3. 24시간 순환 처리 (음수나 24시 초과 처리)
    if total_minutes < 0: total_minutes += 1440
    if total_minutes >= 1440: total_minutes -= 1440
    
    # 4. 진태양시 기준 12지지 매핑
    # 자시: 23:00 ~ 01:00 (진태양시 기준으로는 정각 기준임)
    # (분 + 60) // 120 -> 0=자, 1=축 ...
    
    idx = int((total_minutes + 60) // 120) % 12
    return JI[idx], total_minutes

def get_time_pillar_gan(day_gan, time_ji):
    """일간과 시지를 이용해 시간(Time Gan) 도출 (시두법)"""
    if time_ji not in JI: return "甲"
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    return GAN[(start_idx_map.get(day_gan, 0) + JI.index(time_ji)) % 10]

def get_sibseong(day_gan, target_char):
    if not target_char: return ""
    o_map = {"wood":0, "fire":1, "earth":2, "metal":3, "water":4}
    try:
        d_oh = o_map[OHAENG_MAP[day_gan]]
        t_oh = o_map[OHAENG_MAP[target_char]]
    except: return ""
    
    gan_all = GAN + JI
    same_yy = (gan_all.index(day_gan) % 2) == (gan_all.index(target_char) % 2)
    diff = (t_oh - d_oh) % 5
    
    if diff == 0: return "비견" if same_yy else "겁재"
    if diff == 1: return "식신" if same_yy else "상관"
    if diff == 2: return "편재" if same_yy else "정재"
    if diff == 3: return "편관" if same_yy else "정관"
    if diff == 4: return "편인" if same_yy else "정인"

def get_unseong(day_gan, target_ji):
    return UNSEONG_TABLE[day_gan][JI.index(target_ji)] if target_ji in JI else ""

def get_shinsal(day_ji, target_ji):
    if day_ji in ["亥","卯","未"] and target_ji == "子": return "도화살"
    if day_ji in ["寅","午","戌"] and target_ji == "卯": return "도화살"
    if day_ji in ["巳","酉","丑"] and target_ji == "午": return "도화살"
    if day_ji in ["申","子","辰"] and target_ji == "酉": return "도화살"
    if target_ji in ["辰","戌","丑","未"]: return "화개살" 
    if target_ji in ["寅","申","巳","亥"]: return "역마살"
    return ""

def calculate_daewoon_num(birth_date, is_forward, current_month_ganji):
    """대운수 계산 (DB 조회 방식)"""
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    
    # 효율성을 위해 해당 년도 앞뒤 1년 데이터 조회
    cur.execute("SELECT cd_sy, cd_sm, cd_sd, cd_kyganjee FROM calenda_data WHERE cd_sy BETWEEN ? AND ?", 
                (birth_date.year-1, birth_date.year+1))
    rows = cur.fetchall()
    conn.close()
    
    if not rows: return 5
    
    df = pd.DataFrame(rows, columns=['y', 'm', 'd', 'month_ganji'])
    df['date'] = pd.to_datetime(df[['y', 'm', 'd']].astype(str).agg('-'.join, axis=1))
    
    birth_ts = pd.Timestamp(birth_date)
    target_date = None

    if is_forward:
        future_data = df[df['date'] > birth_ts].sort_values('date')
        for _, row in future_data.iterrows():
            if row['month_ganji'] != current_month_ganji:
                target_date = row['date']
                break
    else:
        past_data = df[df['date'] <= birth_ts].sort_values('date', ascending=False)
        for _, row in past_data.iterrows():
            if row['month_ganji'] != current_month_ganji:
                target_date = row['date']
                break
        if target_date is None and not past_data.empty:
            target_date = past_data.iloc[-1]['date']

    if target_date is None: return 5

    diff_days = abs((birth_ts - target_date).days)
    daewoon_num = round(diff_days / 3)
    if daewoon_num == 0: daewoon_num = 1
    
    return daewoon_num

def get_daewoon_list(year_gan, year_ji, month_gan, month_ji, gender, birth_date):
    is_year_yang = (GAN.index(year_gan) % 2 == 0)
    is_man = (gender == "남자")
    is_forward = (is_year_yang and is_man) or (not is_year_yang and not is_man)
    
    month_ganji = f"{month_gan}{month_ji}"
    daewoon_num = calculate_daewoon_num(birth_date, is_forward, month_ganji)
    
    start_gan_idx = GAN.index(month_gan)
    start_ji_idx = JI.index(month_ji)
    
    daewoon_list = []
    for i in range(1, 9):
        step = i if is_forward else -i
        gan = GAN[(start_gan_idx + step) % 10]
        ji = JI[(start_ji_idx + step) % 12]
        age = daewoon_num + (i-1)*10
        daewoon_list.append({"나이": age, "간지": f"{gan}{ji}"})
        
    return daewoon_list, "순행" if is_forward else "역행", daewoon_num

# --- 4. UI 및 실행 ---
with st.sidebar:
    st.header("📋 정보 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    
    # [수정] 시간 입력 방식 변경 (자,축.. -> 시간,분)
    t_time = st.time_input("태어난 시간", datetime.time(6, 0)) # 기본값 06:00
    
    # [수정] 지역 입력 추가
    loc = st.selectbox("출생 지역 (시/도)", list(LOCATIONS.keys()))
    
    st.write("---")
    btn = st.button("결과 확인하기", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_ganji, y_kr, m_ganji, m_kr, d_ganji, d_kr = row
        y_gan, y_ji = y_ganji[0], y_ganji[1]
        m_gan, m_ji = m_ganji[0], m_ganji[1]
        d_gan, d_ji = d_ganji[0], d_ganji[1]
        
        # [핵심] 진태양시 계산 적용
        real_ji, solar_minutes = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_gan = get_time_pillar_gan(d_gan, real_ji) # 시간 도출
        t_ji = real_ji
        
        day_master = d_gan

        # 대운 계산
        dw_list, dw_dir, dw_num = get_daewoon_list(y_gan, y_ji, m_gan, m_ji, gender, d)

        st.header(f"📜 {name}님의 사주팔자")
        
        # 진태양시 안내 문구
        solar_h = int(solar_minutes // 60)
        solar_m = int(solar_minutes % 60)
        st.info(f"입력하신 시간은 **{t_time.strftime('%H:%M')}** 이지만, **{loc}** 지역의 경도를 반영한 실제 태양시(진태양시)는 **{solar_h:02d}:{solar_m:02d}** 입니다. 이에 따라 **'{t_ji}({OHAENG_KR[OHAENG_MAP[t_ji]]})시'**로 판명되었습니다.")
        
        st.markdown("---")

        # [사주 원국]
        cols = st.columns(4)
        pillars = [
            {"title": "시주 (말년)", "gan": t_gan, "ji": t_ji},
            {"title": "일주 (본인)", "gan": d_gan, "ji": d_ji},
            {"title": "월주 (사회)", "gan": m_gan, "ji": m_ji},
            {"title": "연주 (초년)", "gan": y_gan, "ji": y_ji},
        ]

        for i, col in enumerate(cols):
            p = pillars[i]
            ten_gan = "일간" if i == 1 else get_sibseong(day_master, p['gan'])
            ten_ji = get_sibseong(day_master, p['ji'])
            cls_gan = OHAENG_MAP[p['gan']]
            cls_ji = OHAENG_MAP[p['ji']]
            unseong = get_unseong(day_master, p['ji'])
            shinsal = get_shinsal(d_ji, p['ji'])
            
            with col:
                st.markdown(f"""
                <div class="saju-card">
                    <div class="pillar-title">{p['title']}</div>
                    <div class="ten-god">{ten_gan}</div>
                    <div class="gan-ji {cls_gan}">{p['gan']}</div>
                    <div class="gan-ji {cls_ji}">{p['ji']}</div>
                    <div class="ten-god">{ten_ji}</div>
                    <div class="unseong">{unseong}</div>
                    <div class="shinsal">{shinsal}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.write("")
        
        # [대운 및 오행]
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            st.subheader(f"🌊 대운 (대운수: {dw_num})")
            st.caption(f"방향: {dw_dir}")
            dw_df = pd.DataFrame(dw_list)
            st.dataframe(dw_df.set_index("나이").T, use_container_width=True)

        with c_right:
            st.subheader("📊 오행 분석")
            all_chars = [y_gan, y_ji, m_gan, m_ji, d_gan, d_ji, t_gan, t_ji]
            ohaeng_cnt = {"목":0, "화":0, "토":0, "금":0, "수":0}
            for char in all_chars:
                ohaeng_cnt[OHAENG_KR[OHAENG_MAP[char]]] += 1
            
            df_oh = pd.DataFrame({
                "오행": list(ohaeng_cnt.keys()),
                "개수": list(ohaeng_cnt.values()),
                "색상": ["#4CAF50", "#E91E63", "#FFC107", "#9E9E9E", "#2196F3"]
            })
            
            chart = alt.Chart(df_oh).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("개수", stack=True),
                color=alt.Color("오행", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#4CAF50", "#E91E63", "#FFC107", "#9E9E9E", "#2196F3"])),
                tooltip=["오행", "개수"]
            )
            st.altair_chart(chart, use_container_width=True)

    else:
        st.error("데이터 조회 실패")

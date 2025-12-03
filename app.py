import streamlit as st
import sqlite3
import datetime
from datetime import timedelta
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS ---
st.set_page_config(page_title="AI 정통 만세력", page_icon="🔮", layout="wide")

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

# --- 3. 핵심 로직 함수들 ---

def get_time_pillar(day_gan, hour_ji):
    if hour_ji not in JI: return "甲"
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    return GAN[(start_idx_map.get(day_gan, 0) + JI.index(hour_ji)) % 10]

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
    if target_ji in ["辰","戌","丑","未"]: return "화개살" # 약식
    if target_ji in ["寅","申","巳","亥"]: return "역마살" # 약식
    return ""

def calculate_daewoon_num(birth_date, is_forward, current_month_ganji):
    """
    [핵심 수정] 대운수 정밀 계산 함수
    - DB에서 월주가 바뀌는 날(=절기일)을 찾아 생일과의 차이를 3으로 나눔
    """
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    
    # 앞뒤로 넉넉하게 40일치 데이터를 가져와서 언제 월주가 바뀌는지 확인
    check_start = birth_date - timedelta(days=40)
    check_end = birth_date + timedelta(days=40)
    
    sql = "SELECT cd_sy, cd_sm, cd_sd, cd_kyganjee FROM calenda_data WHERE "
    # 날짜 범위 쿼리 생성 (단순화를 위해 년/월/일 비교 로직 대신 범위 루프 사용)
    # SQLite 날짜 함수 대신 파이썬에서 처리
    
    # 효율성을 위해 해당 년도의 데이터만 가져옴
    cur.execute("SELECT cd_sy, cd_sm, cd_sd, cd_kyganjee FROM calenda_data WHERE cd_sy BETWEEN ? AND ?", 
                (birth_date.year-1, birth_date.year+1))
    rows = cur.fetchall()
    conn.close()
    
    # 데이터프레임으로 변환하여 검색 편의성 증대
    df = pd.DataFrame(rows, columns=['y', 'm', 'd', 'month_ganji'])
    df['date'] = pd.to_datetime(df[['y', 'm', 'd']].astype(str).agg('-'.join, axis=1))
    
    # 생일 기준 인덱스 찾기
    birth_ts = pd.Timestamp(birth_date)
    
    # 절기 찾기 (월주 글자가 현재와 달라지는 지점 찾기)
    if is_forward:
        # 순행: 미래로 가면서 월주가 바뀌는 날 찾기
        future_data = df[df['date'] > birth_ts].sort_values('date')
        target_date = None
        for _, row in future_data.iterrows():
            if row['month_ganji'] != current_month_ganji:
                target_date = row['date']
                break
    else:
        # 역행: 과거로 가면서 월주가 바뀌었던 날(절기 시작일) 찾기
        past_data = df[df['date'] <= birth_ts].sort_values('date', ascending=False)
        target_date = None
        # 현재 월주와 같은 구간의 '시작일'을 찾아야 함 (즉, 더 과거로 갔을 때 월주가 달라지는 날 바로 다음날, 혹은 현재 월주의 가장 이른 날)
        # 역행은 '생일 - 지난 절기일' 이므로, 현재 월주가 시작된 날을 찾으면 됨
        
        # 현재 월주가 아닌 데이터가 나올 때까지 과거로 탐색
        for _, row in past_data.iterrows():
            if row['month_ganji'] != current_month_ganji:
                # 이 날짜는 전달임. 따라서 절기일은 이 날짜 + 1일 (혹은 현재 월주가 유지되는 가장 빠른 날)
                # 단순화: 그냥 이 row의 날짜와 생일의 차이를 구하면 됨
                target_date = row['date']
                break
        
        # 만약 1월 1일이라 과거 데이터가 없으면? (예외처리)
        if target_date is None and not past_data.empty:
            target_date = past_data.iloc[-1]['date'] # 가장 옛날 데이터

    if target_date is None:
        return 5 # 데이터 부족시 기본값

    # 날짜 차이 계산
    diff_days = abs((birth_ts - target_date).days)
    
    # 대운수 공식: 날짜차이 / 3 (반올림)
    daewoon_num = round(diff_days / 3)
    if daewoon_num == 0: daewoon_num = 1 # 0이면 1로 보정
    
    return daewoon_num

def get_daewoon_list(year_gan, year_ji, month_gan, month_ji, gender, birth_date):
    """대운 리스트 생성"""
    # 순행/역행 결정
    # 양년(갑병무경임) + 남자 = 순행 / 음년(을정기신계) + 여자 = 순행
    # 그 외 역행
    is_year_yang = (GAN.index(year_gan) % 2 == 0)
    is_man = (gender == "남자")
    
    is_forward = False
    if is_year_yang and is_man: is_forward = True
    if not is_year_yang and not is_man: is_forward = True
    
    # 대운수 계산 (DB조회 포함)
    month_ganji = f"{month_gan}{month_ji}" # 예: 甲子
    daewoon_num = calculate_daewoon_num(birth_date, is_forward, month_ganji)
    
    # 대운 간지 뽑기 (월주 기준)
    start_gan_idx = GAN.index(month_gan)
    start_ji_idx = JI.index(month_ji)
    
    daewoon_list = []
    for i in range(1, 9): # 8개 대운
        step = i if is_forward else -i
        gan = GAN[(start_gan_idx + step) % 10]
        ji = JI[(start_ji_idx + step) % 12]
        
        age = daewoon_num + (i-1)*10
        daewoon_list.append({"나이": age, "간지": f"{gan}{ji}"})
        
    direction_str = "순행 (Forward)" if is_forward else "역행 (Backward)"
    return daewoon_list, direction_str, daewoon_num

# --- 4. UI 및 실행 ---
with st.sidebar:
    st.header("📋 정보 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t = st.selectbox("태어난 시간", JI, index=3) # 기본값 묘(卯)
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
        
        t_gan = get_time_pillar(d_gan, t)
        t_ji = t
        day_master = d_gan

        # 대운 계산
        dw_list, dw_dir, dw_num = get_daewoon_list(y_gan, y_ji, m_gan, m_ji, gender, d)

        st.header(f"📜 {name}님의 사주팔자")
        st.caption(f"양력 {d.year}년 {d.month}월 {d.day}일 {t}시생 ({gender})")
        st.markdown("---")

        # [사주 원국]
        cols = st.columns(4)
        pillars = [
            {"title": "시주", "gan": t_gan, "ji": t_ji},
            {"title": "일주", "gan": d_gan, "ji": d_ji},
            {"title": "월주", "gan": m_gan, "ji": m_ji},
            {"title": "연주", "gan": y_gan, "ji": y_ji},
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
            
            # 대운 표 디자인
            dw_df = pd.DataFrame(dw_list)
            st.dataframe(dw_df.set_index("나이").T, use_container_width=True)
            
            st.info("대운수는 태어난 날부터 절기까지의 날짜를 계산하여 산출된 정확한 값입니다.")

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

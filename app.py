import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt # 그래프용 라이브러리

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 정통 만세력", page_icon="🔮", layout="wide")

# --- 상수 데이터 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
GAN_OHAENG = {"甲":"목", "乙":"목", "丙":"화", "丁":"화", "戊":"토", "己":"토", "庚":"금", "辛":"금", "壬":"수", "癸":"수"}
JI_OHAENG = {"子":"수", "丑":"토", "寅":"목", "卯":"목", "辰":"토", "巳":"화", "午":"화", "未":"토", "申":"금", "酉":"금", "戌":"토", "亥":"수"}
OHAENG_COLOR = {"목": "#4CAF50", "화": "#FF5722", "토": "#FFC107", "금": "#9E9E9E", "수": "#2196F3"}

# --- 함수 모음 ---
def get_time_pillar(day_gan, hour_ji):
    if hour_ji not in JI: return ""
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    start_idx = start_idx_map.get(day_gan, 0)
    ji_idx = JI.index(hour_ji)
    return GAN[(start_idx + ji_idx) % 10]

def get_daewoon(year_gan, year_ji, gender):
    # 대운 계산 (간략 로직: 양남음녀 순행, 음남양녀 역행)
    # 실제로는 '절입일' 기준 날짜 계산이 필요하나, 여기서는 순서만 보여줌
    # 연간의 음양: 갑병무경임(+) 을정기신계(-)
    is_year_yang = (GAN.index(year_gan) % 2 == 0)
    is_man = (gender == "남자")
    
    # 순행/역행 결정
    forward = True
    if is_man and not is_year_yang: forward = False # 음남 -> 역행
    if not is_man and is_year_yang: forward = False # 양녀 -> 역행
    
    # 월주 기준 시작 (DB에서 월주를 받아와야 정확하나 예시로 랜덤 시작 대신 고정)
    # 실제 구현시엔 월주 인덱스부터 시작해야 함. 여기선 편의상 갑자부터 시작한다고 가정하고 방향만 보여줌
    start_idx = 0 
    daewoon_list = []
    
    for i in range(1, 9): # 8개 대운
        idx = start_idx + i if forward else start_idx - i
        gan = GAN[idx % 10]
        ji = JI[idx % 12]
        daewoon_list.append({"age": i*10, "ganji": f"{gan}{ji}"})
        
    return daewoon_list, "순행" if forward else "역행"

# --- UI 메인 ---
st.title("🔮 AI 정통 만세력 (Full Ver.)")
st.markdown("---")

# 입력 폼
with st.sidebar:
    st.header("사주 정보 입력")
    name = st.text_input("이름", "홍길동")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1990, 1, 1), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t = st.selectbox("태어난 시간", JI)
    st.markdown("---")
    btn = st.button("분석하기", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gan, y_kr, m_gan, m_kr, d_gan, d_kr = row
        day_master = d_gan[0]
        time_gan = get_time_pillar(day_master, t)
        
        # 사주 8글자 리스트 (오행 분석용)
        eight_chars = [y_gan[0], y_gan[1], m_gan[0], m_gan[1], d_gan[0], d_gan[1], time_gan, t]
        
        # 1. 오행 분석 (차트 데이터)
        ohaeng_cnt = {"목":0, "화":0, "토":0, "금":0, "수":0}
        for char in eight_chars:
            oh = GAN_OHAENG.get(char, JI_OHAENG.get(char))
            if oh: ohaeng_cnt[oh] += 1
            
        df_ohaeng = pd.DataFrame({
            '오행': list(ohaeng_cnt.keys()),
            '점수': list(ohaeng_cnt.values()),
            '색상': list(OHAENG_COLOR.values())
        })

        # 2. 결과 화면 구성
        st.header(f"{name}님의 사주 분석 결과")
        
        # (A) 사주 원국 (카드)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("시주", f"{time_gan}{t}")
        c2.metric("일주", f"{d_gan}")
        c3.metric("월주", f"{m_gan}")
        c4.metric("연주", f"{y_gan}")
        st.markdown("---")

        # (B) 오행 분석 차트 & 대운
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.subheader("📊 오행 분포")
            chart = alt.Chart(df_ohaeng).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="점수", type="quantitative"),
                color=alt.Color(field="오행", type="nominal", scale=alt.Scale(domain=list(OHAENG_COLOR.keys()), range=list(OHAENG_COLOR.values()))),
                tooltip=["오행", "점수"]
            )
            st.altair_chart(chart, use_container_width=True)
            
            my_oh = GAN_OHAENG[day_master]
            st.info(f"당신은 **{my_oh}** 기운을 타고났습니다.")

        with col_right:
            st.subheader("🌊 대운 흐름 (10년 주기)")
            daewoon_data, direction = get_daewoon(y_gan[0], y_gan[1], gender)
            st.write(f"대운 방향: **{direction}**")
            
            dw_df = pd.DataFrame(daewoon_data)
            st.dataframe(dw_df.set_index("age").T, use_container_width=True)
            st.caption("* 대운수는 절기 데이터 정밀 계산 전이라 임의로 표시되었습니다.")

    else:
        st.error("DB 데이터 없음")

import streamlit as st
import sqlite3
import datetime
import pandas as pd

# --- [1] 페이지 설정 및 루나 스타일 CSS ---
st.set_page_config(page_title="루나 만세력", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    /* 폰트: 프리텐다드 */
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    
    html, body, .stApp {
        font-family: "Pretendard Variable", -apple-system, sans-serif;
        background-color: #f0f2f5;
        color: #333;
    }

    /* 메인 컨테이너 */
    .luna-container {
        background-color: #ffffff;
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        padding: 30px 20px;
        margin-bottom: 30px;
        overflow-x: auto;
    }

    /* 헤더 */
    .header-box {
        text-align: center; margin-bottom: 25px;
        border-bottom: 2px solid #f0f2f5; padding-bottom: 15px;
    }
    .user-name { font-size: 22px; font-weight: 800; color: #1a1a1a; }
    .birth-info { font-size: 14px; color: #666; margin-top: 5px; }
    .solar-time { font-size: 13px; color: #ff6b6b; font-weight: bold; }

    /* 원국표 */
    .pillars-wrapper {
        display: flex; justify-content: space-around; text-align: center;
    }
    .pillar-col {
        flex: 1; min-width: 70px; position: relative;
    }
    .pillar-col:not(:last-child)::after {
        content: ""; position: absolute; right: 0; top: 10%;
        height: 80%; border-right: 1px dashed #e0e0e0;
    }

    /* 요소 스타일 */
    .pillar-label { font-size: 13px; color: #888; margin-bottom: 8px; font-weight: 600; }
    
    .ten-god-tag {
        display: inline-block; font-size: 11px; font-weight: 700; color: #fff;
        background-color: #5c5c5c; padding: 4px 8px; border-radius: 10px;
        margin: 4px 0; min-width: 40px;
    }
    
    .hanja-box { padding: 10px 0; }
    .hanja { font-family: 'Noto Serif KR', serif; font-size: 38px; font-weight: 900; line-height: 1.2; }
    
    .detail-info { margin-top: 10px; }
    .jijanggan { font-size: 11px; color: #aaa; letter-spacing: 1px; margin-bottom: 6px; min-height: 15px; }
    .unseong { font-size: 13px; color: #339af0; font-weight: 800; margin-bottom: 4px; display: block; }
    .shinsal { font-size: 12px; color: #fa5252; font-weight: 700; display: block; min-height: 18px; }

    /* 오행 색상 */
    .wood { color: #52ba68; } .fire { color: #ff6b6b; } .earth { color: #fcc419; } .metal { color: #adb5bd; } .water { color: #343a40; }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #fff; border-radius: 8px; padding: 10px 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stTabs [aria-selected="true"] { background-color: #e3fafc; color: #0c8599; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 상수 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_MAP = {
    "甲":"wood","乙":"wood","丙":"fire","丁":"fire","戊":"earth","己":"earth","庚":"metal","辛":"metal","壬":"water","癸":"water",
    "寅":"wood","卯":"wood","巳":"fire","午":"fire","辰":"earth","戌":"earth","丑":"earth","未":"earth","申":"metal","酉":"metal","亥":"water","子":"water"
}

# [수정] 누락되었던 변수 추가 완료!
KR_OH = {"wood":"목", "fire":"화", "earth":"토", "metal":"금", "water":"수"}

LOCATIONS = {"서울":127.0, "부산":129.1, "대구":128.6, "인천":126.7, "광주":126.8, "대전":127.4, "울산":129.3, "강릉":128.9, "제주":126.5}

JIJANGGAN = {
    "子":"壬 癸", "丑":"癸 辛 己", "寅":"戊 丙 甲", "卯":"甲 乙", "辰":"乙 癸 戊", "巳":"戊 庚 丙",
    "午":"丙 己 丁", "未":"丁 乙 己", "申":"戊 壬 庚", "酉":"庚 辛", "戌":"辛 丁 戊", "亥":"戊 甲 壬"
}
UNSEONG_TABLE = {
    "甲":["목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양","장생"],
    "丙":["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "戊":["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "庚":["사","묘","절","태","양","장생","목욕","관대","건록","제왕","쇠","병"],
    "壬":["제왕","쇠","병","사","묘","절","태","양","장생","목욕","관대","건록"],
    "乙":["병","쇠","제왕","건록","관대","목욕","장생","양","태","절","묘","사"],
    "丁":["절","묘","사","병","쇠","제왕","건록","관대","목욕","장생","양","태"],
    "己":["절","묘","사","병","쇠","제왕","건록","관대","목욕","장생","양","태"],
    "辛":["장생","양","태","절","묘","사","병","쇠","제왕","건록","관대","목욕"],
    "癸":["건록","제왕","쇠","병","사","묘","절","태","양","장생","목욕","관대"]
}

# --- 3. 로직 함수 ---

def calc_solar_time(h, m, loc):
    lon = LOCATIONS.get(loc, 127.0)
    diff = (lon - 135.0) * 4
    total_min = h * 60 + m + diff
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    ji_idx = int((total_min + 60) // 120) % 12
    return JI[ji_idx], total_min, diff

def get_time_gan(day_gan, time_ji):
    if time_ji not in JI: return "甲"
    idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    start = idx_map.get(day_gan, 0)
    ji_idx = JI.index(time_ji)
    return GAN[(start + ji_idx) % 10]

def get_sibseong(day_gan, target):
    if not target: return ""
    o_map = {"wood":0, "fire":1, "earth":2, "metal":3, "water":4}
    try:
        d_val = o_map[OHAENG_MAP[day_gan]]
        t_val = o_map[OHAENG_MAP[target]]
    except: return ""
    d_pol = GAN.index(day_gan) % 2
    t_pol = (GAN.index(target) if target in GAN else JI.index(target)) % 2
    same = (d_pol == t_pol)
    diff = (t_val - d_val) % 5
    if diff == 0: return "비견" if same else "겁재"
    if diff == 1: return "식신" if same else "상관"
    if diff == 2: return "편재" if same else "정재"
    if diff == 3: return "편관" if same else "정관"
    if diff == 4: return "편인" if same else "정인"

def get_shinsal(day_ji, target_ji):
    # 삼합 기준 약식 구현
    if day_ji in "亥卯未":
        if target_ji == "子": return "년살(도화)"
        if target_ji == "酉": return "재살"
        if target_ji == "巳": return "역마살"
    if day_ji in "寅午戌":
        if target_ji == "卯": return "년살(도화)"
        if target_ji == "子": return "재살"
        if target_ji == "申": return "역마살"
    if day_ji in "巳酉丑":
        if target_ji == "午": return "년살(도화)"
        if target_ji == "卯": return "재살"
        if target_ji == "亥": return "역마살"
    if day_ji in "申子辰":
        if target_ji == "酉": return "년살(도화)"
        if target_ji == "午": return "재살"
        if target_ji == "寅": return "역마살"
    return ""

def get_daewoon(y_g, gender):
    is_yang = (GAN.index(y_g) % 2 == 0)
    is_man = (gender == "남자")
    fwd = (is_yang and is_man) or (not is_yang and not is_man)
    return 4, "순행" if fwd else "역행" # 대운수 예시

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    st.info("정확한 사주 분석을 위해 정보를 입력해주세요.")
    
    name = st.text_input("이름", "홍길동")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1990, 5, 5), min_value=datetime.date(1900,1,1))
    t_time = st.time_input("태어난 시간", datetime.time(11, 28))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    
    if st.button("분석하기", type="primary"):
        st.session_state.run = True

if 'run' in st.session_state and st.session_state.run:
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ saju.db 파일이 없습니다.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        # 화면 구성
        st.markdown(f'<div class="luna-container">', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="header-box">
            <div class="user-name">{name}님의 사주명식</div>
            <div class="birth-info">양력 {d.year}년 {d.month}월 {d.day}일 / {gender}</div>
            <div class="solar-time">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} ({t_j}시)</div>
        </div>
        """, unsafe_allow_html=True)

        pillars = [
            {"n":"시주", "g":t_g, "j":t_j},
            {"n":"일주", "g":d_g, "j":d_j},
            {"n":"월주", "g":m_g, "j":m_j},
            {"n":"연주", "g":y_g, "j":y_j}
        ]
        
        html = '<div class="pillars-wrapper">'
        for idx, p in enumerate(pillars):
            t_top = "일간" if idx==1 else get_sibseong(day_master, p['g'])
            t_bot = get_sibseong(day_master, p['j'])
            c_g = OHAENG_MAP[p['g']]
            c_j = OHAENG_MAP[p['j']]
            un = UNSEONG_TABLE[day_master][JI.index(p['j'])]
            ss = get_shinsal(d_j, p['j'])
            jj = JIJANGGAN[p['j']]
            
            html += f"""
            <div class="pillar-col">
                <div class="pillar-label">{p['n']}</div>
                <span class="ten-god-tag">{t_top}</span>
                <div class="hanja-box">
                    <div class="hanja {c_g}">{p['g']}</div>
                    <div class="hanja {c_j}">{p['j']}</div>
                </div>
                <span class="ten-god-tag">{t_bot}</span>
                <div class="detail-info">
                    <div class="jijanggan">{jj}</div>
                    <span class="unseong">{un}</span>
                    <span class="shinsal">{ss}</span>
                </div>
            </div>
            """
        html += '</div></div>'
        st.markdown(html, unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📊 오행/십성", "⚡ 합충분석", "🌊 대운흐름"])
        
        with t1:
            all_char = [p['g'] for p in pillars] + [p['j'] for p in pillars]
            cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
            for c in all_char: cnt[KR_OH[OHAENG_MAP[c]]] += 1
            
            st.write("**오행 분포**")
            cols = st.columns(5)
            for i, (k, v) in enumerate(cnt.items()):
                cols[i].metric(k, f"{v}개", f"{int(v/8*100)}%")
                
        with t2:
            st.info("원국 내 합(合)과 충(冲) 분석 결과가 표시됩니다.")
            
        with t3:
            num, direct = get_daewoon(y_g, gender)
            st.write(f"**대운수: {num} ({direct})**")
            dw_data = pd.DataFrame({
                "나이": [num + 10*i for i in range(8)],
                "간지": ["예시" for _ in range(8)]
            }).set_index("나이").T
            st.dataframe(dw_data)

    else:
        st.error("해당 날짜의 데이터가 DB에 없습니다.")

import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS (디자인) ---
st.set_page_config(page_title="AI 프로 만세력", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f7f9fc; }
    
    /* [1] 메인 사주 카드 디자인 */
    .pillar-card {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #e1e4e8;
        padding: 0; margin: 4px;
        text-align: center;
        overflow: hidden;
    }
    .card-header {
        background-color: #495057; color: white;
        font-size: 14px; font-weight: bold; padding: 8px 0;
    }
    .ten-god-top { font-size: 13px; font-weight: bold; color: #333; background-color: #e9ecef; padding: 4px; border-bottom: 1px dashed #dee2e6; }
    .hanja-area { padding: 15px 0; }
    .hanja { font-family: 'Serif'; font-size: 40px; font-weight: 900; line-height: 1.2; margin: 2px 0; }
    .ten-god-bottom { font-size: 13px; font-weight: bold; color: #333; background-color: #f8f9fa; padding: 4px; border-top: 1px dashed #dee2e6; }
    
    /* 하단 정보 박스 (지장간, 12운성, 신살) */
    .bottom-info { font-size: 12px; padding: 8px; background-color: #fff; border-top: 1px solid #eee; }
    .jijanggan { color: #868e96; letter-spacing: 2px; margin-bottom: 4px; font-size: 11px; }
    .unseong { color: #1c7ed6; font-weight: bold; display: block; margin-bottom: 2px;}
    .shinsal { color: #e03131; font-weight: bold; font-size: 11px; }

    /* [2] 탭 및 상세 분석 스타일 */
    .interaction-box {
        background-color: white; border-radius: 10px; padding: 15px;
        margin-bottom: 10px; border-left: 5px solid #ccc; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .box-hap { border-left-color: #4CAF50; }
    .box-chung { border-left-color: #F44336; }
    .box-wonjin { border-left-color: #FF9800; }
    .box-gongmang { border-left-color: #9E9E9E; }
    
    /* 오행 색상 */
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
LOCATIONS = {"서울/경기": 127.0, "강원(강릉)": 128.9, "대전/충남": 127.4, "광주/전남": 126.8, "부산/경남": 129.1, "제주": 126.5}

# 지장간/12운성
JIJANGGAN = {
    "子": "壬 癸", "丑": "癸 辛 己", "寅": "戊 丙 甲", "卯": "甲 乙",
    "辰": "乙 癸 戊", "巳": "戊 庚 丙", "午": "丙 己 丁", "未": "丁 乙 己",
    "申": "戊 壬 庚", "酉": "庚 辛", "戌": "辛 丁 戊", "亥": "戊 甲 壬"
}
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

# --- [상세 분석용 데이터] 합/충/형/파/해 ---
CHEONGAN_HAP = {"甲己":"토", "乙庚":"금", "丙辛":"수", "丁壬":"목", "戊癸":"화"}
CHEONGAN_CHUNG = ["甲庚", "甲戊", "乙辛", "乙己", "丙壬", "丙庚", "丁癸", "丁辛", "戊壬", "己癸"]
JIJI_YUKHAP = {"子丑":"토", "寅亥":"목", "卯戌":"화", "辰酉":"금", "巳申":"수", "午未":"화"}
JIJI_SAMHAP = {"申子辰":"수국", "亥卯未":"목국", "寅午戌":"화국", "巳酉丑":"금국"}
JIJI_BANGHAP = {"寅卯辰":"목국", "巳午未":"화국", "申酉戌":"금국", "亥子丑":"수국"}
JIJI_CHUNG = ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"]
JIJI_WONJIN = ["子未", "丑午", "寅酉", "卯申", "辰亥", "巳戌"]
JIJI_HYEONG = ["寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑", "子卯", "辰辰", "午午", "酉酉", "亥亥"]
JIJI_PA = ["子酉", "丑辰", "寅亥", "卯午", "巳申", "戌未"]

# --- 3. 로직 함수 ---

def calculate_time_ji(hour, minute, location_name):
    correction = (LOCATIONS.get(location_name, 127.0) - 135.0) * 4
    total_min = hour * 60 + minute + correction
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    return JI[int((total_min + 60) // 120) % 12], total_min

def get_time_pillar_gan(day_gan, time_ji):
    if time_ji not in JI: return "甲"
    start_idx = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}.get(day_gan, 0)
    return GAN[(start_idx + JI.index(time_ji)) % 10]

def get_sibseong(day_gan, target):
    if not target: return ""
    o_idx = {"wood":0, "fire":1, "earth":2, "metal":3, "water":4}
    try:
        d_oh = o_idx[OHAENG_MAP[day_gan]]
        t_oh = o_idx[OHAENG_MAP[target]]
    except: return ""
    same_yy = ((GAN+JI).index(day_gan)%2) == ((GAN+JI).index(target)%2)
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

def get_gongmang(day_gan, day_ji):
    """공망 계산"""
    res = JI.index(day_ji) - GAN.index(day_gan)
    if res < 0: res += 12
    return [JI[res], JI[(res+1)%12]]

def analyze_interactions(pillars):
    """합/충/형/파/해 상세 분석"""
    gans = [p['g'] for p in pillars]
    jis = [p['j'] for p in pillars]
    names = ["시", "일", "월", "연"]
    log = {"hap": [], "chung": [], "etc": []}

    # 1. 천간 합/충 (인접한 기둥끼리)
    for i in range(3):
        pair = "".join(sorted([gans[i], gans[i+1]]))
        loc = f"{names[i+1]}-{names[i]}"
        # 합
        for k, v in CHEONGAN_HAP.items():
            if "".join(sorted(k)) == pair: log['hap'].append(f"[{loc}] 천간합: {k} → {v}")
        # 충
        for k in CHEONGAN_CHUNG:
            if "".join(sorted(k)) == pair: log['chung'].append(f"[{loc}] 천간충: {k}")

    # 2. 지지 육합/충/원진/형/파 (인접한 기둥)
    for i in range(3):
        j1, j2 = jis[i], jis[i+1]
        pair_set = {j1, j2}
        loc = f"{names[i+1]}-{names[i]}"
        
        # 육합
        for k, v in JIJI_YUKHAP.items():
            if {k[0], k[1]} == pair_set: log['hap'].append(f"[{loc}] 지지육합: {k} → {v}")
        # 충
        for k in JIJI_CHUNG:
            if set(k) == pair_set: log['chung'].append(f"[{loc}] 지지충: {k}")
        # 원진
        for k in JIJI_WONJIN:
            if set(k) == pair_set: log['etc'].append(f"[{loc}] 원진살: {k} (불화/원망)")
        # 형
        for k in JIJI_HYEONG:
            if set(k) == pair_set: log['etc'].append(f"[{loc}] 형살: {k} (조정/수술)")
        # 파
        for k in JIJI_PA:
            if set(k) == pair_set: log['etc'].append(f"[{loc}] 파살: {k} (파괴/분리)")

    # 3. 삼합/방합 (전체 지지 대상)
    ji_str = "".join(jis)
    for k, v in JIJI_SAMHAP.items():
        cnt = sum([1 for char in k if char in ji_str])
        if cnt == 3: log['hap'].append(f"[국] 지지삼합: {k} → {v} (강력한 합)")
        elif cnt == 2: log['hap'].append(f"[반합] 지지반합: {k} 중 2자 ({v} 기운)")
        
    for k, v in JIJI_BANGHAP.items():
        cnt = sum([1 for char in k if char in ji_str])
        if cnt == 3: log['hap'].append(f"[국] 지지방합: {k} → {v} (가족/동료의 합)")

    return log

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🔮 사주 정보 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("태어난 시간", datetime.time(6, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    btn = st.button("분석하기", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gj, m_gj, d_gj = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        t_j, s_min = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_pillar_gan(d_g, t_j)
        day_master = d_g
        
        st.header(f"📜 {name}님의 정밀 사주풀이")
        st.caption(f"양력 {d.year}.{d.month}.{d.day} / 진태양시 {int(s_min//60):02d}:{int(s_min%60):02d}")

        # --- [1] 한눈에 보는 도표 (메인 카드) ---
        pillars = [
            {"name":"시주", "g":t_g, "j":t_j, "role":"말년/자식"}, 
            {"name":"일주", "g":d_g, "j":d_j, "role":"본인/배우자"},
            {"name":"월주", "g":m_g, "j":m_j, "role":"사회/부모"}, 
            {"name":"연주", "g":y_g, "j":y_j, "role":"초년/조상"}
        ]
        
        cols = st.columns(4)
        for i, col in enumerate(cols):
            p = pillars[i]
            ten_g = "일간" if i==1 else get_sibseong(day_master, p['g'])
            ten_j = get_sibseong(day_master, p['j'])
            unseong = get_unseong(day_master, p['j'])
            shinsal = get_shinsal(d_j, p['j'])
            jijang = JIJANGGAN.get(p['j'], "")
            
            with col:
                st.markdown(f"""
                <div class="pillar-card">
                    <div class="card-header">{p['name']} ({p['role']})</div>
                    <div class="ten-god-top">{ten_g}</div>
                    <div class="hanja-area">
                        <div class="hanja {OHAENG_MAP[p['g']]}">{p['g']}</div>
                        <div class="hanja {OHAENG_MAP[p['j']]}">{p['j']}</div>
                    </div>
                    <div class="ten-god-bottom">{ten_j}</div>
                    <div class="bottom-info">
                        <div class="jijanggan">{jijang}</div>
                        <span class="unseong">{unseong}</span>
                        <span class="shinsal">{shinsal if shinsal else "-"}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.write("") 
        
        # --- [2] 상세 분석 (탭 메뉴) ---
        st.subheader("🔍 상세 분석 (클릭해서 확인)")
        tab1, tab2, tab3, tab4 = st.tabs(["🏛️ 궁성(자리)", "💞 합(Combination)", "⚡ 충(Clash)", "🌫️ 기타/공망"])
        
        log = analyze_interactions(pillars)
        gm = get_gongmang(d_g, d_j)
        
        with tab1:
            st.info(f"**일주 ({d_g}{d_j})**: 나의 본원(Identity)입니다. {OHAENG_KR[OHAENG_MAP[d_g]]}의 성향을 띠며, 12운성 '{get_unseong(day_master, d_j)}'지에 앉아 있습니다.")
            st.write(f"**월주 ({m_g}{m_j})**: 내가 살아가는 사회적 환경입니다. 격국과 직업적성을 볼 때 가장 중요합니다.")
            
        with tab2:
            if log['hap']:
                for item in log['hap']:
                    st.markdown(f"<div class='interaction-box box-hap'><b>{item}</b><br>두 기운이 만나 새로운 에너지를 만들거나 묶이는 관계입니다.</div>", unsafe_allow_html=True)
            else:
                st.write("원국 내에 뚜렷한 합이 없습니다.")
                
        with tab3:
            if log['chung']:
                for item in log['chung']:
                    st.markdown(f"<div class='interaction-box box-chung'><b>{item}</b><br>서로 반대되는 기운이 부딪혀 변화나 이동, 갈등을 암시합니다.</div>", unsafe_allow_html=True)
            else:
                st.write("원국 내에 뚜렷한 충이 없습니다.")
                
        with tab4:
            st.markdown(f"<div class='interaction-box box-gongmang'><b>🌫️ 공망 (Void): {gm[0]}, {gm[1]}</b><br>채워지지 않는 빈 자리입니다. 해당 글자가 사주에 있으면 그 역할이 반감되거나 헛수고가 되기 쉽습니다.</div>", unsafe_allow_html=True)
            
            if log['etc']:
                for item in log['etc']:
                    st.markdown(f"<div class='interaction-box box-wonjin'><b>{item}</b></div>", unsafe_allow_html=True)
            elif not log['etc']:
                st.write("원진, 형, 파살 등 기타 신살이 없습니다.")

    else:
        st.error("데이터 조회 실패")

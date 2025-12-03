import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS (앱 디자인) ---
st.set_page_config(page_title="AI 프로 만세력", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f7f8fa; }
    
    /* [1] 사주 원국 카드 */
    .pillar-card {
        background-color: white; border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #eee; padding: 10px 5px; text-align: center;
    }
    .card-header { font-size: 14px; color: #888; font-weight: bold; margin-bottom: 5px; }
    .ten-god-label { font-size: 12px; background: #f1f3f5; color: #495057; padding: 3px 8px; border-radius: 10px; font-weight: bold; display: inline-block; margin: 2px 0;}
    .hanja { font-family: 'Serif'; font-size: 38px; font-weight: 900; line-height: 1.1; margin: 5px 0; }
    
    /* [2] 신살/길성 태그 스타일 */
    .shinsal-box {
        background-color: white; border-radius: 15px; padding: 20px;
        margin-top: 15px; border: 1px solid #e0e0e0;
    }
    .shinsal-tag {
        display: inline-block;
        padding: 6px 14px;
        margin: 4px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: bold;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .tag-good { background-color: #e6fcf5; color: #0ca678; border: 1px solid #c3fae8; } /* 길성 (초록) */
    .tag-bad { background-color: #fff5f5; color: #fa5252; border: 1px solid #ffc9c9; } /* 흉살 (빨강) */
    .tag-neutral { background-color: #f8f9fa; color: #495057; border: 1px solid #dee2e6; } /* 기타 (회색) */

    /* [3] 오행/십성 분석 박스 */
    .analysis-card {
        background-color: white; border-radius: 15px; padding: 20px;
        margin-top: 10px; border: 1px solid #e0e0e0;
    }
    .stat-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 14px; }
    .stat-label { font-weight: bold; width: 60px; }
    .stat-bar-bg { flex-grow: 1; background-color: #f1f3f5; height: 10px; border-radius: 5px; margin: 0 10px; overflow: hidden; }
    .stat-bar-fill { height: 100%; border-radius: 5px; }
    .stat-value { font-weight: bold; color: #555; width: 40px; text-align: right; }

    /* 오행 색상 */
    .wood { color: #4CAF50; } .fire { color: #E91E63; } .earth { color: #FFC107; } .metal { color: #9E9E9E; } .water { color: #2196F3; }
    .bg-wood { background-color: #4CAF50; } .bg-fire { background-color: #E91E63; } .bg-earth { background-color: #FFC107; } .bg-metal { background-color: #9E9E9E; } .bg-water { background-color: #2196F3; }
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
LOCATIONS = {"서울/경기": 127.0, "강원(강릉)": 128.9, "대전/충남": 127.4, "광주/전남": 126.8, "부산/경남": 129.1, "제주": 126.5}

# --- 3. 핵심 로직 ---

def calculate_time_ji(hour, minute, location_name):
    correction = (LOCATIONS.get(location_name, 127.0) - 135.0) * 4
    total_min = hour * 60 + minute + correction
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    return JI[int((total_min + 60) // 120) % 12]

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

# [NEW] 확장된 신살/길성 로직
def get_comprehensive_shinsal(day_gan, day_ji, pillars):
    shinsals = []
    
    # 1. 지지 글자 수집
    jis = [p['j'] for p in pillars]
    
    # 천을귀인 (길성)
    if day_gan in ['甲', '戊', '庚']: 
        if '丑' in jis or '未' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['乙', '己']: 
        if '子' in jis or '申' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['丙', '丁']: 
        if '亥' in jis or '酉' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['辛']: 
        if '午' in jis or '寅' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['壬', '癸']: 
        if '巳' in jis or '卯' in jis: shinsals.append(("천을귀인", "good"))

    # 백호대살 (흉살/강한힘) - 일주/연주 등 기둥 자체 체크 필요하나 여기선 간략히
    baekho_list = ["甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"]
    for p in pillars:
        ganji = f"{p['g']}{p['j']}"
        if ganji in baekho_list: shinsals.append(("백호대살", "bad")); break

    # 도화살 (지지 기준)
    dohwa_map = {"亥":"子", "卯":"子", "未":"子", "寅":"卯", "午":"卯", "戌":"卯", "巳":"午", "酉":"午", "丑":"午", "申":"酉", "子":"酉", "辰":"酉"}
    target_dohwa = dohwa_map.get(day_ji)
    if target_dohwa and target_dohwa in jis: shinsals.append(("도화살", "neutral"))

    # 역마살
    yeokma_map = {"亥":"巳", "卯":"巳", "未":"巳", "寅":"申", "午":"申", "戌":"申", "巳":"亥", "酉":"亥", "丑":"亥", "申":"寅", "子":"寅", "辰":"寅"}
    target_yeokma = yeokma_map.get(day_ji)
    if target_yeokma and target_yeokma in jis: shinsals.append(("역마살", "neutral"))
    
    # 화개살
    hwagae_map = {"亥":"未", "卯":"未", "未":"未", "寅":"戌", "午":"戌", "戌":"戌", "巳":"丑", "酉":"丑", "丑":"丑", "申":"辰", "子":"辰", "辰":"辰"}
    target_hwagae = hwagae_map.get(day_ji)
    if target_hwagae and target_hwagae in jis: shinsals.append(("화개살", "neutral"))

    # 현침살 (뾰족한 글자)
    sharp_chars = ['甲', '申', '卯', '午', '辛']
    sharp_cnt = 0
    for p in pillars:
        if p['g'] in sharp_chars: sharp_cnt += 1
        if p['j'] in sharp_chars: sharp_cnt += 1
    if sharp_cnt >= 2: shinsals.append(("현침살", "neutral"))

    return list(set(shinsals)) # 중복제거

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
        
        t_j = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_pillar_gan(d_g, t_j)
        day_master = d_g
        
        st.header(f"📜 {name}님의 사주 분석")
        st.caption(f"{d.year}년 {d.month}월 {d.day}일 ({gender})")

        # [1] 메인 사주 원국 (카드 형태)
        pillars = [
            {"name":"시주", "g":t_g, "j":t_j}, {"name":"일주", "g":d_g, "j":d_j},
            {"name":"월주", "g":m_g, "j":m_j}, {"name":"연주", "g":y_g, "j":y_j}
        ]
        
        cols = st.columns(4)
        for i, col in enumerate(cols):
            p = pillars[i]
            ten_g = "일간" if i==1 else get_sibseong(day_master, p['g'])
            ten_j = get_sibseong(day_master, p['j'])
            c_g = OHAENG_MAP[p['g']]
            c_j = OHAENG_MAP[p['j']]
            
            col.markdown(f"""
            <div class="pillar-card">
                <div class="card-header">{p['name']}</div>
                <div class="ten-god-label">{ten_g}</div>
                <div class="hanja {c_g}">{p['g']}</div>
                <div class="hanja {c_j}">{p['j']}</div>
                <div class="ten-god-label">{ten_j}</div>
            </div>
            """, unsafe_allow_html=True)
            
        # [2] 신살과 길성 (태그 형태)
        st.subheader("⭐ 신살과 길성")
        shinsal_list = get_comprehensive_shinsal(d_g, d_j, pillars)
        
        if shinsal_list:
            html_tags = ""
            for name, type_ in shinsal_list:
                cls = "tag-good" if type_ == "good" else "tag-bad" if type_ == "bad" else "tag-neutral"
                html_tags += f'<span class="shinsal-tag {cls}">{name}</span>'
            st.markdown(f'<div class="shinsal-box">{html_tags}</div>', unsafe_allow_html=True)
        else:
            st.info("특이한 신살이 발견되지 않았습니다. 평안한 사주입니다.")

        # [3] 오행과 십성 분석 (그래프 형태)
        st.subheader("📊 오행과 십성 분석")
        
        c1, c2 = st.columns(2)
        
        # 오행 데이터 계산
        all_chars = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        oh_cnt = {"목":0, "화":0, "토":0, "금":0, "수":0}
        for c in all_chars: oh_cnt[OHAENG_KR[OHAENG_MAP[c]]] += 1
        
        # 십성 데이터 계산
        ten_cnt = {"비겁":0, "식상":0, "재성":0, "관성":0, "인성":0}
        sib_map = {"비견":"비겁", "겁재":"비겁", "식신":"식상", "상관":"식상", "편재":"재성", "정재":"재성", "편관":"관성", "정관":"관성", "편인":"인성", "정인":"인성"}
        for c in all_chars:
            if c == d_g: ten_cnt["비겁"] += 1 # 일간은 비겁
            else:
                s = get_sibseong(day_master, c)
                if s: ten_cnt[sib_map[s]] += 1

        with c1:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("**오행 분포 (Five Elements)**")
            for oh, color_cls in [("목", "bg-wood"), ("화", "bg-fire"), ("토", "bg-earth"), ("금", "bg-metal"), ("수", "bg-water")]:
                cnt = oh_cnt[oh]
                pct = (cnt / 8) * 100
                st.markdown(f"""
                <div class="stat-row">
                    <div class="stat-label">{oh}</div>
                    <div class="stat-bar-bg"><div class="stat-bar-fill {color_cls}" style="width: {pct}%;"></div></div>
                    <div class="stat-value">{int(pct)}%</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("**십성 분포 (Ten Gods)**")
            for ten in ["비겁", "식상", "재성", "관성", "인성"]:
                cnt = ten_cnt[ten]
                pct = (cnt / 8) * 100
                st.markdown(f"""
                <div class="stat-row">
                    <div class="stat-label">{ten}</div>
                    <div class="stat-bar-bg"><div class="stat-bar-fill" style="width: {pct}%; background-color: #868e96;"></div></div>
                    <div class="stat-value">{cnt}개</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # 분석 멘트
        st.success(f"당신의 사주는 **{max(oh_cnt, key=oh_cnt.get)}** 기운이 가장 강하며, 사회적으로는 **{max(ten_cnt, key=ten_cnt.get)}**의 성향(능력/관계)을 주로 활용하게 됩니다.")

    else:
        st.error("데이터 조회 실패")

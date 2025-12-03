import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS (이미지 스타일 완벽 구현) ---
st.set_page_config(page_title="AI 프로 만세력 (Master)", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f0f2f5; }
    
    /* [메인 컨테이너] 만세력 원국표 스타일 */
    .saju-container {
        display: flex;
        justify-content: space-between;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #dfe6ed;
    }
    
    /* 개별 기둥 (Pillar) 스타일 */
    .pillar-box {
        flex: 1;
        margin: 0 5px;
        text-align: center;
        border-right: 1px dashed #e1e4e8;
    }
    .pillar-box:last-child { border-right: none; }
    
    /* 헤더 (연주, 월주 등) */
    .pillar-header {
        font-size: 14px; color: #5f6368; font-weight: bold;
        margin-bottom: 10px; background-color: #f8f9fa;
        padding: 5px; border-radius: 5px;
    }
    
    /* 십성 (육친) 라벨 - 위/아래 */
    .ten-god-label {
        font-size: 11px; color: #fff; background-color: #555;
        padding: 2px 6px; border-radius: 4px; display: inline-block;
        margin-bottom: 4px;
    }
    
    /* 한자 영역 (천간/지지) */
    .hanja-box { padding: 5px 0; }
    .hanja-text {
        font-family: 'KoPub Batang', serif;
        font-size: 42px; font-weight: 900; line-height: 1.2;
        text-shadow: 1px 1px 0px rgba(0,0,0,0.05);
    }
    
    /* 지장간 (숨은 글자) */
    .jijanggan-box {
        font-size: 12px; color: #888;
        border-top: 1px solid #eee; border-bottom: 1px solid #eee;
        padding: 6px 0; margin: 8px 0; letter-spacing: 2px;
    }
    
    /* 하단 정보 (12운성, 신살) */
    .bottom-stat { font-size: 13px; font-weight: bold; margin: 3px 0; }
    .stat-unseong { color: #1c7ed6; }
    .stat-shinsal { color: #e03131; font-size: 12px; }
    
    /* 오행 색상 (텍스트) */
    .wood { color: #4CAF50; } .fire { color: #E91E63; } .earth { color: #FFC107; } .metal { color: #9E9E9E; } .water { color: #2196F3; }
    
    /* [섹션] 신살 태그 */
    .shinsal-wrapper { background: white; padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .tag { display: inline-block; padding: 4px 10px; margin: 2px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .tag-good { background: #e6fcf5; color: #0ca678; border: 1px solid #c3fae8; }
    .tag-bad { background: #fff5f5; color: #fa5252; border: 1px solid #ffc9c9; }
    
    /* [섹션] 분석 그래프 */
    .graph-container { background: white; padding: 15px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .bar-row { display: flex; align-items: center; margin-bottom: 5px; font-size: 13px; }
    .bar-bg { flex: 1; background: #eee; height: 8px; border-radius: 4px; margin: 0 10px; }
    .bar-fill { height: 100%; border-radius: 4px; }

    /* [섹션] 달력 정보 */
    .cal-info { background: #495057; color: white; padding: 15px; border-radius: 10px; text-align: center; display: flex; justify-content: space-around; margin-top: 20px;}
    .cal-item span { display: block; }
    .cal-title { font-size: 11px; opacity: 0.8; margin-bottom: 3px; }
    .cal-data { font-size: 15px; font-weight: bold; color: #ffec99; }
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

# --- 로직 함수들 (생략 없이 모두 포함) ---
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

def get_comprehensive_shinsal(day_gan, day_ji, pillars):
    shinsals = []
    jis = [p['j'] for p in pillars]
    # 천을귀인
    if day_gan in ['甲','戊','庚']:
        if '丑' in jis or '未' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['乙','己']:
        if '子' in jis or '申' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['丙','丁']:
        if '亥' in jis or '酉' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['辛']:
        if '午' in jis or '寅' in jis: shinsals.append(("천을귀인", "good"))
    elif day_gan in ['壬','癸']:
        if '巳' in jis or '卯' in jis: shinsals.append(("천을귀인", "good"))
    # 백호대살
    baekho = ["甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"]
    for p in pillars:
        if f"{p['g']}{p['j']}" in baekho: shinsals.append(("백호대살", "bad")); break
    # 기타
    for p in pillars:
        ss = get_shinsal(day_ji, p['j'])
        if ss: shinsals.append((ss, "neutral"))
    return list(set(shinsals))

def analyze_interactions(pillars):
    gans = [p['g'] for p in pillars]
    jis = [p['j'] for p in pillars]
    names = ["시", "일", "월", "연"]
    log = {"hap": [], "chung": []}
    
    # 천간 합/충
    CHEONGAN_HAP = {"甲己":"토", "乙庚":"금", "丙辛":"수", "丁壬":"목", "戊癸":"화"}
    CHEONGAN_CHUNG = ["甲庚", "甲戊", "乙辛", "乙己", "丙壬", "丙庚", "丁癸", "丁辛", "戊壬", "己癸"]
    for i in range(3):
        pair = "".join(sorted([gans[i], gans[i+1]]))
        for k, v in CHEONGAN_HAP.items():
            if "".join(sorted(k)) == pair: log['hap'].append(f"{names[i+1]}-{names[i]} 천간합: {k}→{v}")
        for k in CHEONGAN_CHUNG:
            if "".join(sorted(k)) == pair: log['chung'].append(f"{names[i+1]}-{names[i]} 천간충: {k}")
            
    # 지지 합/충
    JIJI_YUKHAP = {"子丑":"토", "寅亥":"목", "卯戌":"화", "辰酉":"금", "巳申":"수", "午未":"화"}
    JIJI_CHUNG = ["子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"]
    for i in range(3):
        pair_set = {jis[i], jis[i+1]}
        for k, v in JIJI_YUKHAP.items():
            if {k[0], k[1]} == pair_set: log['hap'].append(f"{names[i+1]}-{names[i]} 지지육합: {k}→{v}")
        for k in JIJI_CHUNG:
            if set(k) == pair_set: log['chung'].append(f"{names[i+1]}-{names[i]} 지지충: {k}")
            
    return log

def calculate_daewoon_num(birth_date, is_forward, current_month_ganji):
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
            if row['month_ganji'] != current_month_ganji: target_date = row['date']; break
    else:
        past = df[df['date'] <= birth_ts].sort_values('date', ascending=False)
        for _, row in past.iterrows():
            if row['month_ganji'] != current_month_ganji: target_date = row['date']; break
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
        lst.append({"나이": dw_num + (i-1)*10, "간지": f"{g}{j}"})
    return lst, "순행" if is_forward else "역행", dw_num

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🔮 사주 정보 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("태어난 시간", datetime.time(6, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    btn = st.button("운세 풀이 시작", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms, cd_sol_plan, cd_lun_plan FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gj, m_gj, d_gj, lun_m, lun_d, jeolgi, sol_plan, lun_plan = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        t_j, s_min = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_pillar_gan(d_g, t_j)
        day_master = d_g
        
        dw_list, dw_dir, dw_num = get_daewoon_list(y_g, y_j, m_g, m_j, gender, d)
        
        st.header(f"📜 {name}님의 정밀 만세력")
        st.caption(f"양력 {d.year}.{d.month}.{d.day} / 진태양시 {int(s_min//60):02d}:{int(s_min%60):02d} ({t_j}시)")

        # --- [SECTION 1] 만세력 원국표 (이미지 스타일 구현) ---
        pillars = [
            {"name":"시주", "g":t_g, "j":t_j, "role":"자식"}, 
            {"name":"일주", "g":d_g, "j":d_j, "role":"본인"},
            {"name":"월주", "g":m_g, "j":m_j, "role":"부모"}, 
            {"name":"연주", "g":y_g, "j":y_j, "role":"조상"}
        ]
        
        html = '<div class="saju-container">'
        for idx, p in enumerate(pillars):
            ten_g = "일간" if idx==1 else get_sibseong(day_master, p['g'])
            ten_j = get_sibseong(day_master, p['j'])
            c_g = OHAENG_MAP[p['g']]
            c_j = OHAENG_MAP[p['j']]
            unseong = get_unseong(day_master, p['j'])
            shinsal = get_shinsal(d_j, p['j'])
            jijang = JIJANGGAN.get(p['j'], "")
            
            html += f"""
            <div class="pillar-box">
                <div class="pillar-header">{p['name']} ({p['role']})</div>
                <div class="ten-god-label">{ten_g}</div>
                <div class="hanja-box">
                    <div class="hanja-text {c_g}">{p['g']}</div>
                    <div class="hanja-text {c_j}">{p['j']}</div>
                </div>
                <div class="ten-god-label">{ten_j}</div>
                <div class="jijanggan-box">{jijang}</div>
                <div class="bottom-stat stat-unseong">{unseong}</div>
                <div class="bottom-stat stat-shinsal">{shinsal if shinsal else "-"}</div>
            </div>
            """
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)
        
        # --- [SECTION 2] 분석 그래프 & 신살 태그 ---
        c1, c2 = st.columns(2)
        
        # 오행/십성 통계
        all_chars = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        oh_cnt = {"목":0, "화":0, "토":0, "금":0, "수":0}
        for c in all_chars: oh_cnt[OHAENG_KR[OHAENG_MAP[c]]] += 1
        
        with c1:
            st.markdown('<div class="graph-container">', unsafe_allow_html=True)
            st.write("**📊 오행 분포 (Five Elements)**")
            for oh, bg in [("목","#4CAF50"),("화","#E91E63"),("토","#FFC107"),("금","#9E9E9E"),("수","#2196F3")]:
                pct = (oh_cnt[oh]/8)*100
                st.markdown(f'<div class="bar-row"><span>{oh}</span><div class="bar-bg"><div class="bar-fill" style="width:{pct}%; background:{bg};"></div></div><span>{int(pct)}%</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown('<div class="shinsal-wrapper">', unsafe_allow_html=True)
            st.write("**⭐ 주요 신살 및 길성**")
            s_list = get_comprehensive_shinsal(d_g, d_j, pillars)
            if s_list:
                for n, t in s_list:
                    cls = "tag-good" if t=="good" else "tag-bad" if t=="bad" else "tag"
                    st.markdown(f'<span class="tag {cls}">{n}</span>', unsafe_allow_html=True)
            else:
                st.info("특이 신살 없음")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [SECTION 3] 상세 분석 탭 (합충형파) ---
        tab1, tab2, tab3 = st.tabs(["🏛️ 궁성 풀이", "💞 합(合) 분석", "⚡ 충(冲) 분석"])
        log = analyze_interactions(pillars)
        
        with tab1:
            st.info(f"**일주 ({d_g}{d_j})**: 본원 {OHAENG_KR[OHAENG_MAP[d_g]]}과 12운성 {get_unseong(day_master, d_j)}지")
        with tab2:
            if log['hap']: 
                for l in log['hap']: st.success(l)
            else: st.write("합 없음")
        with tab3:
            if log['chung']: 
                for l in log['chung']: st.error(l)
            else: st.write("충 없음")

        # --- [SECTION 4] 대운표 ---
        st.subheader(f"🌊 대운 흐름 ({dw_num}대운, {dw_dir})")
        dw_df = pd.DataFrame(dw_list)
        st.dataframe(dw_df.set_index("나이").T, use_container_width=True)
        
        # --- [SECTION 5] 상세 달력 정보 (파일 분석 결과 추가) ---
        holiday_info = sol_plan if sol_plan else (lun_plan if lun_plan else "-")
        jeolgi_info = jeolgi if jeolgi else "-"
        
        st.markdown(f"""
        <div class="cal-info">
            <div class="cal-item"><span class="cal-title">음력 날짜</span><span class="cal-data">{lun_m}월 {lun_d}일</span></div>
            <div class="cal-item"><span class="cal-title">절기 (Solar Term)</span><span class="cal-data" style="color:#ff6b6b;">{jeolgi_info}</span></div>
            <div class="cal-item"><span class="cal-title">기념일</span><span class="cal-data">{holiday_info}</span></div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

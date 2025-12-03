import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- 1. 페이지 설정 및 CSS ---
st.set_page_config(page_title="AI 프로 만세력", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f5f7f9; }
    
    /* 메인 사주 카드 디자인 */
    .pillar-card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e1e4e8;
        padding: 0; margin: 2px;
        text-align: center;
        overflow: hidden;
    }
    .card-header {
        background-color: #495057; color: white;
        font-size: 14px; font-weight: bold; padding: 6px 0;
    }
    .ten-god-top { font-size: 12px; font-weight: bold; color: #555; background-color: #f1f3f5; padding: 4px; border-bottom: 1px solid #eee; }
    .hanja-box { padding: 10px 0; }
    .hanja { font-family: 'Serif'; font-size: 34px; font-weight: 900; line-height: 1.1; }
    .ten-god-bottom { font-size: 12px; font-weight: bold; color: #555; background-color: #f8f9fa; padding: 2px; }
    
    .detail-box { font-size: 11px; color: #868e96; padding: 4px; border-top: 1px dashed #eee; }
    .jijanggan { color: #adb5bd; letter-spacing: 1px; margin-bottom: 2px; }
    .unseong { color: #228be6; font-weight: bold; }
    .shinsal { color: #e03131; font-weight: bold; }

    /* 오행 색상 */
    .wood { color: #51cf66; } .fire { color: #ff6b6b; } .earth { color: #fcc419; } .metal { color: #adb5bd; } .water { color: #339af0; }
    
    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: white; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stTabs [aria-selected="true"] { background-color: #e7f5ff; color: #1c7ed6; border-bottom: 2px solid #1c7ed6; }
</style>
""", unsafe_allow_html=True)

# --- 2. 기초 데이터 및 매핑 ---
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

# 지장간
JIJANGGAN = {
    "子": "壬 癸", "丑": "癸 辛 己", "寅": "戊 丙 甲", "卯": "甲 乙",
    "辰": "乙 癸 戊", "巳": "戊 庚 丙", "午": "丙 己 丁", "未": "丁 乙 己",
    "申": "戊 壬 庚", "酉": "庚 辛", "戌": "辛 丁 戊", "亥": "戊 甲 壬"
}
# 12운성
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
LOCATIONS = {"서울/경기": 127.0, "강원(강릉)": 128.9, "강원(춘천)": 127.7, "대전/충남": 127.4, "충북(청주)": 127.5, "광주/전남": 126.8, "전북(전주)": 127.1, "부산/경남": 129.1, "대구/경북": 128.6, "울산": 129.3, "제주": 126.5, "인천": 126.7}

# --- [상세 분석용 데이터] 합/충/형/파/해/공망 ---
CHEONGAN_HAP = {"甲己":"토", "乙庚":"금", "丙辛":"수", "丁壬":"목", "戊癸":"화"}
CHEONGAN_CHUNG = ["甲庚", "甲戊", "乙辛", "乙己", "丙壬", "丙庚", "丁癸", "丁辛", "戊壬", "己癸"] # 대표적 충
JIJI_YUKHAP = {"子丑":"토", "寅亥":"목", "卯戌":"화", "辰酉":"금", "巳申":"수", "午未":"화"}
JIJI_SAMHAP = {"申子辰":"수국", "亥卯未":"목국", "寅午戌":"화국", "巳酉丑":"금국"}
JIJI_BANGHAP = {"寅卯辰":"목국", "巳午未":"화국", "申酉戌":"금국", "亥子丑":"수국"}
JIJI_CHUNG = {"子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥"}
JIJI_WONJIN = {"子未", "丑午", "寅酉", "卯申", "辰亥", "巳戌"}
JIJI_HYEONG = {"寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑", "子卯", "辰辰", "午午", "酉酉", "亥亥"}
JIJI_PA = {"子酉", "丑辰", "寅亥", "卯午", "巳申", "戌未"}

# --- 3. 로직 함수 ---

def calculate_time_ji(hour, minute, location_name):
    correction = (LOCATIONS.get(location_name, 127.0) - 135.0) * 4
    total_min = hour * 60 + minute + correction
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    return JI[int((total_min + 60) // 120) % 12], total_min

def get_time_pillar_gan(day_gan, time_ji):
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
    same_yy = ( (GAN+JI).index(day_gan)%2 ) == ( (GAN+JI).index(target_char)%2 )
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
    """공망 계산 (일주 기준)"""
    gan_idx = GAN.index(day_gan)
    ji_idx = JI.index(day_ji)
    diff = ji_idx - gan_idx
    if diff < 0: diff += 12
    # 공망은 diff 바로 뒤 2글자
    return [JI[diff], JI[(diff+1)%12]]

def check_interactions(pillars):
    """합, 충, 형, 파, 해 분석"""
    results = {"hap":[], "chung":[], "wonjin":[], "hyeong":[], "pa":[]}
    
    # 천간 합/충
    gans = [p['g'] for p in pillars]
    jis = [p['j'] for p in pillars]
    titles = ["시", "일", "월", "연"]
    
    # 2개씩 짝지어 비교 (연-월, 월-일, 일-시)
    for i in range(3):
        pair_gan = "".join(sorted([gans[i], gans[i+1]])) # 정렬해서 키 찾기
        pair_ji = "".join(sorted([jis[i], jis[i+1]])) # 지지 정렬은 주의 필요하나 여기선 집합으로 체크
        loc = f"{titles[i+1]}-{titles[i]}"
        
        # 천간합
        for k, v in CHEONGAN_HAP.items():
            if "".join(sorted(k)) == pair_gan: results['hap'].append(f"[{loc}] 천간합: {k}화{v}")
            
        # 천간충
        for k in CHEONGAN_CHUNG:
            if "".join(sorted(k)) == pair_gan: results['chung'].append(f"[{loc}] 천간충: {k}")

        # 지지육합
        for k, v in JIJI_YUKHAP.items():
            # 육합은 순서 상관없이
            if (jis[i] in k and jis[i+1] in k) and (jis[i] != jis[i+1]): 
                results['hap'].append(f"[{loc}] 지지육합: {k}화{v}")
                
        # 지지충
        curr_ji_set = {jis[i], jis[i+1]}
        for k in JIJI_CHUNG:
            if set(k) == curr_ji_set: results['chung'].append(f"[{loc}] 지지충: {k}")
            
        # 원진
        for k in JIJI_WONJIN:
            if set(k) == curr_ji_set: results['wonjin'].append(f"[{loc}] 원진살: {k}")

        # 형
        for k in JIJI_HYEONG:
             if set(k) == curr_ji_set: results['hyeong'].append(f"[{loc}] 형살: {k}")
             
        # 파
        for k in JIJI_PA:
             if set(k) == curr_ji_set: results['pa'].append(f"[{loc}] 파살: {k}")

    # 삼합/방합 (3글자 이상 체크는 전체 지지에서)
    ji_str = "".join(jis)
    for k, v in JIJI_SAMHAP.items():
        count = sum([1 for char in k if char in ji_str])
        if count == 3: results['hap'].append(f"[전체] 지지삼합: {k} ({v})")
        elif count == 2: results['hap'].append(f"[전체] 삼합반합: {k} 글자 중 2자")
        
    return results

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🔮 사주 정보 입력")
    name = st.text_input("이름", "홍길동")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("태어난 시간", datetime.time(6, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    btn = st.button("사주풀이 시작", type="primary")

if btn:
    conn = sqlite3.connect("saju.db")
    cur = conn.cursor()
    cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
    row = cur.fetchone()
    conn.close()

    if row:
        y_gj, _, m_gj, _, d_gj, _ = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        real_ji, s_min = calculate_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_pillar_gan(d_g, real_ji)
        t_j = real_ji
        day_master = d_g
        
        st.header(f"📜 {name}님의 상세 사주풀이")
        st.caption(f"양력 {d.year}.{d.month}.{d.day} / 진태양시 {int(s_min//60):02d}:{int(s_min%60):02d}")

        # --- [1] 메인 대시보드 (한눈에 보는 도표) ---
        pillars = [
            {"name": "시주", "g": t_g, "j": t_j, "role": "자녀/말년"},
            {"name": "일주", "g": d_g, "j": d_j, "role": "본인/배우자"},
            {"name": "월주", "g": m_g, "j": m_j, "role": "부모/사회"},
            {"name": "연주", "g": y_g, "j": y_j, "role": "조상/초년"},
        ]
        
        cols = st.columns(4)
        for i, col in enumerate(cols):
            p = pillars[i]
            # 계산
            ten_g = "일간(나)" if i == 1 else get_sibseong(day_master, p['g'])
            ten_j = get_sibseong(day_master, p['j'])
            unseong = get_unseong(day_master, p['j'])
            shinsal = get_shinsal(d_j, p['j'])
            jijang = JIJANGGAN.get(p['j'], "")
            
            with col:
                st.markdown(f"""
                <div class="pillar-card">
                    <div class="card-header">{p['name']} ({p['role']})</div>
                    <div class="ten-god-top">{ten_g}</div>
                    <div class="hanja-box">
                        <div class="hanja {OHAENG_MAP[p['g']]}">{p['g']}</div>
                        <div class="hanja {OHAENG_MAP[p['j']]}">{p['j']}</div>
                    </div>
                    <div class="ten-god-bottom">{ten_j}</div>
                    <div class="detail-box">
                        <div class="jijanggan">{jijang}</div>
                        <div class="unseong">{unseong}</div>
                        <div class="shinsal">{shinsal if shinsal else "-"}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.write("")
        st.markdown("---")
        
        # --- [2] 상세 분석 (탭 메뉴) ---
        tab1, tab2, tab3, tab4 = st.tabs(["🏛️ 궁성/성향", "💞 합(合) 분석", "⚡ 충/형/파/해", "⭐ 신살/공망"])

        interactions = check_interactions(pillars)
        gm = get_gongmang(d_g, d_j)

        with tab1:
            st.subheader("궁성론 (Pillar Analysis)")
            st.info(f"**일주({d_g}{d_j})**: 나의 정체성입니다. {OHAENG_KR[OHAENG_MAP[d_g]]}의 기운을 가지고 태어났으며, 배우자 자리에 {ten_j}(이)가 있습니다.")
            st.write(f"**월주({m_g}{m_j})**: 부모와 사회적 환경을 의미합니다. 내가 사회에서 쓰는 무기인 {get_sibseong(day_master, m_g)} 격국에 가깝습니다.")
            
        with tab2:
            st.subheader("합 (Combination)")
            if interactions['hap']:
                for item in interactions['hap']:
                    st.success(item)
            else:
                st.write("사주 원국에 뚜렷한 합이 없습니다.")
                
        with tab3:
            st.subheader("충/형/파/해 (Conflict)")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**충 (Clash)**")
                if interactions['chung']:
                    for item in interactions['chung']: st.error(item)
                else: st.write("충이 없습니다.")
                
                st.write("**원진 (Resentment)**")
                if interactions['wonjin']:
                    for item in interactions['wonjin']: st.warning(item)
                else: st.write("원진이 없습니다.")
            
            with c2:
                st.write("**형/파 (Punishment/Destruction)**")
                if interactions['hyeong']:
                    for item in interactions['hyeong']: st.warning(item)
                if interactions['pa']:
                    for item in interactions['pa']: st.info(item)
                if not interactions['hyeong'] and not interactions['pa']:
                    st.write("형/파가 없습니다.")

        with tab4:
            st.subheader("신살 및 공망")
            st.error(f"🌫️ **공망 (Void)**: {gm[0]}, {gm[1]}")
            st.caption("공망은 '비어있다'는 뜻으로, 해당 글자가 사주에 있다면 그 기능이 약화되거나 헛수고가 될 수 있음을 암시합니다.")
            
            st.write("**주요 신살**")
            # 전체 기둥 신살 체크
            found_shinsal = False
            for p in pillars:
                ss = get_shinsal(d_j, p['j'])
                if ss:
                    st.write(f"- {p['name']}({p['j']}): **{ss}**")
                    found_shinsal = True
            if not found_shinsal: st.write("주요 신살(도화/역마/화개)이 원국에 없습니다.")

    else:
        st.error("데이터 조회 실패")

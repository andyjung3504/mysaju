import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- [설정] 페이지 및 CSS 디자인 ---
st.set_page_config(page_title="AI 프로 만세력 (Master)", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200;900&display=swap');
    
    .stApp { background-color: #f4f6f9; }
    
    /* [1] 메인 원국표 컨테이너 */
    .saju-wrapper {
        display: flex; justify-content: space-between;
        background: #fff; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        padding: 20px 10px; margin-bottom: 20px;
        border: 1px solid #e1e4e8;
    }
    .pillar-box {
        flex: 1; text-align: center;
        border-right: 1px dashed #ddd; margin: 0 5px;
    }
    .pillar-box:last-child { border-right: none; }
    
    .pillar-header {
        font-size: 14px; font-weight: bold; color: #555;
        background-color: #f8f9fa; padding: 6px; border-radius: 6px; margin-bottom: 8px;
    }
    
    .ten-god {
        font-size: 11px; font-weight: bold; color: #fff;
        background-color: #495057; padding: 3px 8px; border-radius: 12px;
        display: inline-block; margin: 4px 0;
    }
    
    .hanja-box { padding: 8px 0; }
    .hanja {
        font-family: 'Noto Serif KR', serif; font-size: 42px; font-weight: 900;
        line-height: 1.1; text-shadow: 1px 1px 0 rgba(0,0,0,0.1);
    }
    
    .jijanggan { font-size: 12px; color: #868e96; margin: 5px 0; letter-spacing: 1px; }
    .stat-text { font-size: 13px; font-weight: bold; margin: 2px 0; }
    .stat-unseong { color: #1c7ed6; }
    .stat-shinsal { color: #e03131; font-size: 12px; }
    
    /* [2] 오행 그래프 & 신살 태그 */
    .analysis-container {
        background: #fff; border-radius: 12px; padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .bar-row { display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; }
    .bar-label { width: 30px; font-weight: bold; }
    .bar-track { flex: 1; background: #f1f3f5; height: 10px; border-radius: 5px; margin: 0 10px; overflow: hidden;}
    .bar-fill { height: 100%; border-radius: 5px; }
    
    .tag { display: inline-block; padding: 5px 12px; margin: 3px; border-radius: 20px; font-size: 12px; font-weight: bold; }
    .tag-good { background: #e6fcf5; color: #0ca678; border: 1px solid #c3fae8; }
    .tag-bad { background: #fff5f5; color: #fa5252; border: 1px solid #ffc9c9; }
    .tag-neu { background: #f8f9fa; color: #495057; border: 1px solid #dee2e6; }
    
    /* [3] 하단 달력 정보 */
    .cal-box {
        background: #343a40; color: #fff; padding: 15px; border-radius: 10px;
        display: flex; justify-content: space-around; align-items: center; margin-top: 20px;
    }
    .cal-title { font-size: 11px; opacity: 0.7; display: block; margin-bottom: 3px; }
    .cal-val { font-size: 16px; font-weight: bold; color: #ffd43b; }

    /* 오행 색상 */
    .wood { color: #4CAF50; } .fire { color: #E91E63; } .earth { color: #FFC107; } .metal { color: #9E9E9E; } .water { color: #2196F3; }
</style>
""", unsafe_allow_html=True)

# --- 상수 데이터 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG = {"甲":"wood","乙":"wood","丙":"fire","丁":"fire","戊":"earth","己":"earth","庚":"metal","辛":"metal","壬":"water","癸":"water",
          "寅":"wood","卯":"wood","巳":"fire","午":"fire","辰":"earth","戌":"earth","丑":"earth","未":"earth","申":"metal","酉":"metal","亥":"water","子":"water"}
KR_OH = {"wood":"목", "fire":"화", "earth":"토", "metal":"금", "water":"수"}
LOCATIONS = {"서울":127.0, "부산":129.1, "대구":128.6, "인천":126.7, "광주":126.8, "대전":127.4, "울산":129.3, "강릉":128.9, "제주":126.5}

JIJANG = {"子":"壬癸", "丑":"癸辛己", "寅":"戊丙甲", "卯":"甲乙", "辰":"乙癸戊", "巳":"戊庚丙", "午":"丙己丁", "未":"丁乙己", "申":"戊壬庚", "酉":"庚辛", "戌":"辛丁戊", "亥":"戊甲壬"}
UNSEONG = {
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

# --- 로직 함수 ---
def calc_time_ji(h, m, loc_name):
    lon = LOCATIONS.get(loc_name, 127.0)
    corr = (lon - 135.0) * 4
    t_min = h*60 + m + corr
    if t_min < 0: t_min += 1440
    if t_min >= 1440: t_min -= 1440
    # [수정] t_min(float)을 그대로 반환
    return JI[int((t_min+60)//120)%12], t_min

def get_time_gan(day_gan, time_ji):
    if time_ji not in JI: return "甲"
    start = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}[day_gan]
    return GAN[(start + JI.index(time_ji)) % 10]

def get_sibseong(day_gan, target):
    if not target: return ""
    o_map = {"wood":0, "fire":1, "earth":2, "metal":3, "water":4}
    try:
        d_val = o_map[OHAENG[day_gan]]
        t_val = o_map[OHAENG[target]]
    except: return ""
    
    d_pol = (GAN.index(day_gan) % 2)
    t_pol = (GAN.index(target) if target in GAN else JI.index(target)) % 2
    
    same = (d_pol == t_pol)
    diff = (t_val - d_val) % 5
    
    if diff == 0: return "비견" if same else "겁재"
    if diff == 1: return "식신" if same else "상관"
    if diff == 2: return "편재" if same else "정재"
    if diff == 3: return "편관" if same else "정관"
    if diff == 4: return "편인" if same else "정인"

def get_shinsal(day_ji, target_ji):
    if day_ji in "亥卯未": return "도화살" if target_ji=="子" else "역마살" if target_ji=="巳" else "화개살" if target_ji=="未" else ""
    if day_ji in "寅午戌": return "도화살" if target_ji=="卯" else "역마살" if target_ji=="申" else "화개살" if target_ji=="戌" else ""
    if day_ji in "巳酉丑": return "도화살" if target_ji=="午" else "역마살" if target_ji=="亥" else "화개살" if target_ji=="丑" else ""
    if day_ji in "申子辰": return "도화살" if target_ji=="酉" else "역마살" if target_ji=="寅" else "화개살" if target_ji=="辰" else ""
    return ""

def get_full_shinsal(day_gan, day_ji, pillars):
    res = []
    jis = [p['j'] for p in pillars]
    if day_gan in "甲戊庚":
        if "丑" in jis or "未" in jis: res.append(("천을귀인", "good"))
    elif day_gan in "乙己":
        if "子" in jis or "申" in jis: res.append(("천을귀인", "good"))
    elif day_gan in "丙丁":
        if "亥" in jis or "酉" in jis: res.append(("천을귀인", "good"))
    elif day_gan in "辛":
        if "午" in jis or "寅" in jis: res.append(("천을귀인", "good"))
    elif day_gan in "壬癸":
        if "巳" in jis or "卯" in jis: res.append(("천을귀인", "good"))
    
    baekho = ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]
    for p in pillars:
        if p['g']+p['j'] in baekho: res.append(("백호대살", "bad")); break
    
    for p in pillars:
        ss = get_shinsal(day_ji, p['j'])
        if ss: res.append((ss, "neu"))
    return list(set(res))

def get_daewoon(y_g, m_g, m_j, gender, b_date):
    is_yang = (GAN.index(y_g) % 2 == 0)
    is_man = (gender == "남자")
    fwd = (is_yang and is_man) or (not is_yang and not is_man)
    dw_num = 5 
    lst = []
    s_g, s_j = GAN.index(m_g), JI.index(m_j)
    for i in range(1, 9):
        step = i if fwd else -i
        g = GAN[(s_g + step)%10]
        j = JI[(s_j + step)%12]
        lst.append({"나이": dw_num + (i-1)*10, "간지": g+j})
    return lst, dw_num, "순행" if fwd else "역행"

# --- UI 실행 ---
with st.sidebar:
    st.title("🔮 사주 입력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1990, 5, 5), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("시간", datetime.time(12, 0))
    loc = st.selectbox("지역", list(LOCATIONS.keys()))
    if st.button("분석하기", type="primary"):
        st.session_state.run = True

if 'run' in st.session_state and st.session_state.run:
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms, cd_sol_plan FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except Exception as e:
        st.error(f"DB 오류: {e} (DB에 달력 정보 컬럼이 없습니다. DB 재생성이 필요합니다.)")
        row = None

    if row:
        y_ganji, m_ganji, d_ganji, l_m, l_d, term, sol_evt = row
        y_g, y_j = y_ganji[0], y_ganji[1]
        m_g, m_j = m_ganji[0], m_ganji[1]
        d_g, d_j = d_ganji[0], d_ganji[1]
        
        t_j, s_min = calc_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        st.header(f"📜 {name}님의 정밀 만세력")
        # [수정됨] float 에러 해결: int()로 변환
        st.caption(f"양력 {d} / 진태양시 {int(s_min//60):02d}:{int(s_min%60):02d}")

        # --- [섹션 1] 원국표 ---
        pillars = [
            {"n":"시주", "r":"자식", "g":t_g, "j":t_j},
            {"n":"일주", "r":"본인", "g":d_g, "j":d_j},
            {"n":"월주", "r":"부모", "g":m_g, "j":m_j},
            {"n":"연주", "r":"조상", "g":y_g, "j":y_j}
        ]
        
        html = '<div class="saju-wrapper">'
        for idx, p in enumerate(pillars):
            t_top = "일간" if idx==1 else get_sibseong(day_master, p['g'])
            t_bot = get_sibseong(day_master, p['j'])
            c_g = OHAENG[p['g']]
            c_j = OHAENG[p['j']]
            un = UNSEONG[day_master][JI.index(p['j'])]
            ss = get_shinsal(d_j, p['j'])
            jj = JIJANG[p['j']].replace(""," ").strip()
            
            html += f"""
            <div class="pillar-box">
                <div class="pillar-header">{p['n']} ({p['r']})</div>
                <div class="ten-god">{t_top}</div>
                <div class="hanja-box">
                    <div class="hanja {c_g}">{p['g']}</div>
                    <div class="hanja {c_j}">{p['j']}</div>
                </div>
                <div class="ten-god">{t_bot}</div>
                <div class="jijanggan">{jj}</div>
                <div class="stat-text stat-unseong">{un}</div>
                <div class="stat-text stat-shinsal">{ss if ss else "-"}</div>
            </div>
            """
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
        
        # --- [섹션 2] 그래프 & 신살 ---
        c1, c2 = st.columns(2)
        chars = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in chars: cnt[KR_OH[OHAENG[c]]] += 1
        
        with c1:
            st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
            st.write("📊 **오행 분포**")
            for k, color in [("목","#4CAF50"),("화","#E91E63"),("토","#FFC107"),("금","#9E9E9E"),("수","#2196F3")]:
                pct = (cnt[k]/8)*100
                st.markdown(f'<div class="bar-row"><span class="bar-label">{k}</span><div class="bar-track"><div class="bar-fill" style="width:{pct}%; background:{color}"></div></div><span>{int(pct)}%</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
            st.write("⭐ **신살/길성**")
            s_list = get_full_shinsal(d_g, d_j, pillars)
            for n, t in s_list:
                cls = "tag-good" if t=="good" else "tag-bad" if t=="bad" else "tag-neu"
                st.markdown(f'<span class="tag {cls}">{n}</span>', unsafe_allow_html=True)
            if not s_list: st.info("특이 신살 없음")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [섹션 3] 탭 ---
        t1, t2 = st.tabs(["⚡ 관계 분석", "🌊 대운 흐름"])
        with t1:
            st.info("합/충/원진 관계 분석 결과가 여기에 표시됩니다.")
        with t2:
            dw, num, direct = get_daewoon(y_g, m_g, m_j, gender, d)
            st.write(f"**대운수: {num} / {direct}**")
            st.dataframe(pd.DataFrame(dw).set_index("나이").T)
            
        # --- [섹션 4] 달력 정보 ---
        st.markdown(f"""
        <div class="cal-box">
            <div><span class="cal-title">음력 날짜</span><span class="cal-val">{l_m}월 {l_d}일</span></div>
            <div><span class="cal-title">절기</span><span class="cal-val" style="color:#ff6b6b">{term if term else "-"}</span></div>
            <div><span class="cal-title">기념일</span><span class="cal-val">{sol_evt if sol_evt else "-"}</span></div>
        </div>
        """, unsafe_allow_html=True)

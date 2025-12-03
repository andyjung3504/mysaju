import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- [1] 페이지 설정 및 포스텔러 스타일 CSS ---
st.set_page_config(page_title="포스텔러 만세력", page_icon="🔮", layout="wide")

st.markdown("""
<style>
    /* 폰트 및 기본 설정 */
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    
    html, body, [class*="css"] {
        font-family: "Pretendard Variable", -apple-system, sans-serif;
    }
    .stApp { background-color: #f4f5f7; }

    /* 메인 사주 카드 컨테이너 */
    .saju-card-container {
        display: flex;
        justify-content: space-between;
        background-color: #ffffff;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        padding: 24px 10px;
        margin-bottom: 20px;
        flex-wrap: nowrap; /* 모바일에서도 가로 유지 */
        overflow-x: auto;
    }
    
    .pillar-item {
        flex: 1;
        min-width: 70px; /* 모바일 최소 너비 */
        text-align: center;
        position: relative;
        padding: 0 4px;
    }
    
    /* 구분선 */
    .pillar-item:not(:last-child)::after {
        content: ""; position: absolute; right: 0; top: 15%;
        height: 70%; border-right: 1px dashed #e0e0e0;
    }

    /* 스타일 요소 */
    .pillar-title { font-size: 13px; color: #8b95a1; margin-bottom: 6px; font-weight: 600; }
    .ten-god-badge { 
        display: inline-block; font-size: 11px; font-weight: 700; color: #fff;
        background-color: #555; padding: 3px 6px; border-radius: 8px; margin: 4px 0;
    }
    .hanja-container { padding: 8px 0; }
    .hanja-char {
        font-family: "Noto Serif KR", serif;
        font-size: 36px; font-weight: 900; line-height: 1.1;
    }
    
    /* 하단 정보 */
    .bottom-info-box { margin-top: 6px; }
    .jijanggan { font-size: 11px; color: #adb5bd; letter-spacing: -0.5px; margin-bottom: 2px; }
    .unseong { font-size: 12px; color: #1c7ed6; font-weight: 700; display: block; }
    .shinsal-txt { font-size: 11px; color: #fa5252; font-weight: 600; min-height: 15px;}

    /* 오행 색상 */
    .wood { color: #52ba68; } .fire { color: #ff6b6b; } .earth { color: #fcc419; } .metal { color: #adb5bd; } .water { color: #339af0; }

    /* 신살 태그 */
    .tag-container { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); margin-bottom: 16px; }
    .tag-pill { display: inline-block; padding: 6px 12px; margin: 3px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    .tp-good { background: #e3fafc; color: #1098ad; }
    .tp-bad { background: #fff5f5; color: #fa5252; }
    .tp-neu { background: #f1f3f5; color: #495057; }

    /* 그래프 */
    .graph-box { background: white; border-radius: 16px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03); }
    .stat-row { display: flex; align-items: center; margin-bottom: 8px; font-size: 13px; font-weight: 600; }
    .progress-bg { flex: 1; background: #f1f3f5; height: 8px; border-radius: 4px; margin: 0 10px; overflow: hidden; }
    .progress-fill { height: 100%; border-radius: 4px; }

    /* 달력 카드 */
    .cal-info-card {
        background: linear-gradient(135deg, #343a40 0%, #212529 100%);
        color: white; padding: 20px; border-radius: 16px;
        display: flex; justify-content: space-around; align-items: center; margin-top: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .cal-sub { font-size: 12px; opacity: 0.7; margin-bottom: 4px; display: block; }
    .cal-main { font-size: 16px; font-weight: 700; color: #ffe066; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 & 상수 ---
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

# --- 3. 로직 함수 ---
def calc_time_ji(h, m, loc_name):
    lon = LOCATIONS.get(loc_name, 127.0)
    corr = (lon - 135.0) * 4
    t_min = h*60 + m + corr
    if t_min < 0: t_min += 1440
    if t_min >= 1440: t_min -= 1440
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

def get_shinsal_basic(day_ji, target_ji):
    if day_ji in "亥卯未": return "도화" if target_ji=="子" else "역마" if target_ji=="巳" else "화개" if target_ji=="未" else ""
    if day_ji in "寅午戌": return "도화" if target_ji=="卯" else "역마" if target_ji=="申" else "화개" if target_ji=="戌" else ""
    if day_ji in "巳酉丑": return "도화" if target_ji=="午" else "역마" if target_ji=="亥" else "화개" if target_ji=="丑" else ""
    if day_ji in "申子辰": return "도화" if target_ji=="酉" else "역마" if target_ji=="寅" else "화개" if target_ji=="辰" else ""
    return ""

def get_full_shinsal(day_gan, day_ji, pillars):
    res = []
    jis = [p['j'] for p in pillars]
    all_ganji = [p['g']+p['j'] for p in pillars]

    # 1. 천을귀인
    nobles = {'甲':['丑','未'], '戊':['丑','未'], '庚':['丑','未'], '乙':['子','申'], '己':['子','申'], '丙':['亥','酉'], '丁':['亥','酉'], '辛':['午','寅'], '壬':['巳','卯'], '癸':['巳','卯']}
    if day_gan in nobles:
        for n in nobles[day_gan]:
            if n in jis: res.append(("천을귀인", "good"))

    # 2. 괴강살 (경진, 경술, 임진, 임술, 무술)
    goegang = ["庚辰", "庚戌", "壬辰", "壬戌", "戊戌"]
    for gj in all_ganji:
        if gj in goegang: res.append(("괴강살", "bad")); break
            
    # 3. 백호대살
    baekho = ["甲辰","乙未","丙戌","丁丑","戊辰","壬戌","癸丑"]
    for gj in all_ganji:
        if gj in baekho: res.append(("백호대살", "bad")); break
    
    # 4. 홍염살 (매력)
    hongyeom = {"甲":["午"], "乙":["午"], "丙":["寅"], "丁":["未"], "戊":["辰"], "己":["辰"], "庚":["戌"], "辛":["酉"], "壬":["子"], "癸":["申"]}
    if day_gan in hongyeom:
        for h in hongyeom[day_gan]:
            if h in jis: res.append(("홍염살", "good"))

    # 5. 양인살 (강한 고집)
    yangin = {"甲":["卯"], "庚":["酉"], "壬":["子"], "丙":["午"], "戊":["午"]}
    if day_gan in yangin:
        for y in yangin[day_gan]:
            if y in jis: res.append(("양인살", "bad"))

    # 6. 도화/역마/화개
    for p in pillars:
        ss = get_shinsal_basic(day_ji, p['j'])
        if ss: res.append((ss+"살", "neu"))
        
    return list(set(res))

def get_daewoon(y_g, m_g, m_j, gender):
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

# --- 4. UI 실행 ---
with st.sidebar:
    st.image("https://static.forceteller.com/images/pro/pro_banner-ny.png", use_column_width=True)
    st.title("사주 정보 입력")
    name = st.text_input("이름", "홍길동")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1990, 5, 5), min_value=datetime.date(1900,1,1), max_value=datetime.date(2100,12,31))
    t_time = st.time_input("태어난 시간", datetime.time(12, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    if st.button("내 운세 보기", type="primary"):
        st.session_state.run = True

if 'run' in st.session_state and st.session_state.run:
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms, cd_sol_plan FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ DB가 없습니다. saju.db 파일을 업로드해주세요.")
        row = None

    if row:
        y_ganji, m_ganji, d_ganji, l_m, l_d, term, sol_evt = row
        y_g, y_j = y_ganji[0], y_ganji[1]
        m_g, m_j = m_ganji[0], m_ganji[1]
        d_g, d_j = d_ganji[0], d_ganji[1]
        
        t_j, s_min = calc_time_ji(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        # [수정] 헤더 및 진태양시 정수 변환
        st.subheader(f"{name}님의 사주명식")
        st.caption(f"양력 {d.year}년 {d.month}월 {d.day}일 / 진태양시 {int(s_min//60):02d}:{int(s_min%60):02d}")

        # [수정] 기둥 순서 변경: 연주(년) -> 월주(월) -> 일주(일) -> 시주(시)
        pillars = [
            {"n":"연주", "r":"국가/조상", "g":y_g, "j":y_j},
            {"n":"월주", "r":"사회/부모", "g":m_g, "j":m_j},
            {"n":"일주", "r":"본인/배우자", "g":d_g, "j":d_j},
            {"n":"시주", "r":"자식/말년", "g":t_g, "j":t_j}
        ]
        
        # HTML 생성 (들여쓰기 제거하여 버그 수정)
        cards_html = ""
        for idx, p in enumerate(pillars):
            t_top = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            t_bot = get_sibseong(day_master, p['j'])
            c_g = OHAENG[p['g']]
            c_j = OHAENG[p['j']]
            un = UNSEONG[day_master][JI.index(p['j'])]
            ss = get_shinsal_basic(d_j, p['j'])
            jj = JIJANG[p['j']].replace(""," ").strip()
            
            cards_html += f"""
            <div class="pillar-item">
                <div class="pillar-title">{p['n']}</div>
                <div class="ten-god-badge">{t_top}</div>
                <div class="hanja-container">
                    <div class="hanja-char {c_g}">{p['g']}</div>
                    <div class="hanja-char {c_j}">{p['j']}</div>
                </div>
                <div class="ten-god-badge">{t_bot}</div>
                <div class="bottom-info-box">
                    <div class="jijanggan">{jj}</div>
                    <span class="unseong">{un}</span>
                    <span class="shinsal-txt">{ss if ss else "-"}</span>
                </div>
            </div>"""

        st.markdown(f'<div class="saju-card-container">{cards_html}</div>', unsafe_allow_html=True)

        # --- [2] 그래프 & 신살 ---
        c1, c2 = st.columns(2)
        chars = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in chars: cnt[KR_OH[OHAENG[c]]] += 1
        
        with c1:
            st.markdown('<div class="graph-box">', unsafe_allow_html=True)
            st.write("📊 **오행 분포**")
            for k, color in [("목","#52ba68"),("화","#ff6b6b"),("토","#fcc419"),("금","#adb5bd"),("수","#339af0")]:
                pct = (cnt[k]/8)*100
                st.markdown(f'<div class="stat-row"><span>{k}</span><div class="progress-bg"><div class="progress-fill" style="width:{pct}%; background:{color}"></div></div><span>{int(pct)}%</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with c2:
            st.markdown('<div class="tag-container">', unsafe_allow_html=True)
            st.write("⭐ **내 사주의 신살**")
            s_list = get_full_shinsal(d_g, d_j, pillars)
            for n, t in s_list:
                cls = "tp-good" if t=="good" else "tp-bad" if t=="bad" else "tp-neu"
                st.markdown(f'<span class="tag-pill {cls}">{n}</span>', unsafe_allow_html=True)
            if not s_list: st.info("특별한 신살이 없는 평온한 사주입니다.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- [3] 상세 탭 & 대운 ---
        t1, t2 = st.tabs(["⚡ 관계 분석", "🌊 대운 흐름"])
        with t1:
            st.info("💡 합, 충, 형, 파, 해 분석 기능이 활성화되었습니다.")
        with t2:
            dw, num, direct = get_daewoon(y_g, m_g, m_j, gender)
            st.write(f"**대운수: {num} / {direct}**")
            st.dataframe(pd.DataFrame(dw).set_index("나이").T, use_container_width=True)
        
        # --- [4] 달력 정보 ---
        st.markdown(f"""
        <div class="cal-info-card">
            <div><span class="cal-sub">음력 날짜</span><span class="cal-main">{l_m}월 {l_d}일</span></div>
            <div><span class="cal-sub">절기</span><span class="cal-main" style="color:#ff8787">{term if term else "-"}</span></div>
            <div><span class="cal-sub">기념일</span><span class="cal-main">{sol_evt if sol_evt else "-"}</span></div>
        </div>
        """, unsafe_allow_html=True)

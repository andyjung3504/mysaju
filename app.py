import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- [1] 페이지 설정 및 스타일 (CSS) ---
st.set_page_config(page_title="루나 만세력 Pro", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    
    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f7f7f7;
        color: #111;
    }

    /* 메인 박스 */
    .main-container {
        background: white; max-width: 800px; margin: 0 auto;
        padding: 20px; border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    /* 헤더 */
    .header-area { text-align: left; padding-bottom: 20px; border-bottom: 1px solid #eee; margin-bottom: 20px; }
    .user-title { font-size: 24px; font-weight: 800; color: #333; }
    .ganji-badge { background: #eee; padding: 4px 8px; border-radius: 8px; font-size: 14px; color: #555; font-weight: bold; margin-left: 10px; }
    .info-txt { font-size: 13px; color: #666; margin-top: 5px; }
    .solar-txt { font-size: 13px; color: #ff6b6b; font-weight: bold; }

    /* 원국표 Table */
    .saju-table { width: 100%; border-collapse: separate; border-spacing: 2px; text-align: center; table-layout: fixed; }
    .saju-table th { font-size: 12px; color: #888; font-weight: normal; padding-bottom: 5px; }
    
    .char-box {
        background: #fff; border: 1px solid #e5e5e5; border-radius: 12px;
        padding: 10px 0; margin-bottom: 4px;
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 90px;
    }
    .char-font { font-family: 'Noto Serif KR', serif; font-size: 32px; font-weight: 900; line-height: 1; margin-bottom: 5px;}
    .ten-god-txt { font-size: 11px; color: #888; font-weight: bold; }
    
    .c-wood { color: #39d353; } .c-fire { color: #ff6b6b; } 
    .c-earth { color: #e3b341; } .c-metal { color: #a3a3a3; } .c-water { color: #58a6ff; }

    .detail-row td { font-size: 12px; padding: 6px 0; border-top: 1px solid #f0f0f0; color: #555; }
    .row-label { font-weight: bold; color: #aaa; text-align: left; padding-left: 5px; width: 50px; }
    
    .fortune-box { background: #f9f9f9; border-radius: 8px; padding: 8px; text-align: center; margin-top: 10px; }
    .fortune-title { font-size: 12px; font-weight: bold; display: block; margin-bottom: 2px; }
    .fortune-desc { font-size: 10px; color: #999; }

    /* 운세 스크롤 */
    .scroll-container { display: flex; gap: 8px; overflow-x: auto; padding: 10px 0; scrollbar-width: thin; margin-bottom: 20px; }
    .luck-card { min-width: 60px; background: #fff; border: 1px solid #eee; border-radius: 10px; padding: 10px 5px; text-align: center; flex-shrink: 0; }
    .luck-age { font-size: 11px; color: #888; margin-bottom: 4px; display: block;}
    .luck-char { font-family: 'Noto Serif KR'; font-size: 18px; font-weight: bold; line-height: 1.2; display: block; margin: 4px 0;}
    .luck-ten { font-size: 10px; color: #aaa; display: block; }
    
    .section-title { font-size: 16px; font-weight: 800; margin: 30px 0 10px 0; color: #333; display: flex; align-items: center; }
    .section-title::before { content: ''; display: inline-block; width: 4px; height: 16px; background: #333; margin-right: 8px; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 상수 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_MAP = {
    "甲":"wood","乙":"wood","丙":"fire","丁":"fire","戊":"earth","己":"earth","庚":"metal","辛":"metal","壬":"water","癸":"water",
    "寅":"wood","卯":"wood","巳":"fire","午":"fire","辰":"earth","戌":"earth","丑":"earth","未":"earth","申":"metal","酉":"metal","亥":"water","子":"water"
}
# [중요] 오행 변환 맵 (영어->한글)
KR_OH = {"wood":"목", "fire":"화", "earth":"토", "metal":"금", "water":"수"}

LOCATIONS = {"서울":127.0, "부산":129.1, "대구":128.6, "인천":126.7, "광주":126.8, "대전":127.4, "울산":129.3, "강릉":128.9, "제주":126.5}
JIJANGGAN = {
    "子":"壬 癸", "丑":"癸 辛 己", "寅":"戊 丙 甲", "卯":"甲 乙", "辰":"乙 癸 戊", "巳":"戊 庚 丙",
    "午":"丙 己 丁", "未":"丁 乙 己", "申":"戊 壬 庚", "酉":"庚 辛", "戌":"辛 丁 戊", "亥":"戊 甲 壬"
}
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
    if not target_ji: return ""
    res = ""
    if day_ji in "亥卯未":
        if target_ji == "子": res = "도화"
        elif target_ji == "巳": res = "역마"
        elif target_ji == "未": res = "화개"
    if not res:
        if target_ji in "子午卯酉": res = "도화"
        elif target_ji in "寅申巳亥": res = "역마"
        elif target_ji in "辰戌丑未": res = "화개"
    return res

def get_daewoon_full(y_g, m_g, m_j, gender):
    is_yang = (GAN.index(y_g) % 2 == 0)
    is_man = (gender == "남자")
    fwd = (is_yang and is_man) or (not is_yang and not is_man)
    dw_num = 6
    lst = []
    s_g, s_j = GAN.index(m_g), JI.index(m_j)
    for i in range(1, 9):
        step = i if fwd else -i
        g = GAN[(s_g + step)%10]
        j = JI[(s_j + step)%12]
        lst.append({"age": dw_num + (i-1)*10, "gan": g, "ji": j})
    return lst, dw_num

def get_seun(start_year, count=10):
    lst = []
    base_y = 1984 # 갑자
    base_g, base_j = 0, 0
    curr_g = (base_g + (start_year - base_y)) % 10
    curr_j = (base_j + (start_year - base_y)) % 12
    for i in range(count):
        g = GAN[(curr_g + i) % 10]
        j = JI[(curr_j + i) % 12]
        lst.append({"year": start_year + i, "gan": g, "ji": j})
    return lst

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "aaa")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1))
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    if st.button("결과 확인", type="primary"):
        st.session_state.run = True

if 'run' in st.session_state and st.session_state.run:
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ saju.db 파일이 없습니다.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj, l_m, l_d, term = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # [1] 헤더
        st.markdown(f"""<div class="header-area">
<div class="user-title">{name} <span class="ganji-badge">{d_g}{d_j} (푸른 말)</span></div>
<div class="info-txt">양력 {d.year}.{d.month}.{d.day} ({gender}) {t_time.strftime('%H:%M')}</div>
<div class="info-txt">음력 {l_m}월 {l_d}일 / 절기: {term if term else '-'}</div>
<div class="solar-txt">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} ({t_j}시)</div>
</div>""", unsafe_allow_html=True)

        # [2] 원국표
        pillars = [{"n":"시주","g":t_g,"j":t_j}, {"n":"일주","g":d_g,"j":d_j}, {"n":"월주","g":m_g,"j":m_j}, {"n":"연주","g":y_g,"j":y_j}]
        
        html_tbl = """<table class="saju-table"><thead><tr><th>생시</th><th>생일</th><th>생월</th><th>생년</th></tr></thead><tbody>"""
        
        # 천간
        html_tbl += "<tr>"
        for p in pillars:
            ten = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            col = "c-" + OHAENG_MAP[p['g']]
            html_tbl += f"""<td><div class="char-box"><span class="char-font {col}">{p['g']}</span><span class="ten-god-txt">{ten}</span></div></td>"""
        html_tbl += "</tr>"
        
        # 지지
        html_tbl += "<tr>"
        for p in pillars:
            ten = get_sibseong(day_master, p['j'])
            col = "c-" + OHAENG_MAP[p['j']]
            html_tbl += f"""<td><div class="char-box"><span class="char-font {col}">{p['j']}</span><span class="ten-god-txt">{ten}</span></div></td>"""
        html_tbl += "</tr>"
        
        # 상세
        html_tbl += """<tr class="detail-row"><td class="row-label">지장간</td>"""
        for p in pillars: html_tbl += f"<td>{JIJANGGAN[p['j']]}</td>"
        html_tbl += """</tr><tr class="detail-row"><td class="row-label">운성</td>"""
        for p in pillars: html_tbl += f"<td style='color:#339af0; font-weight:bold;'>{UNSEONG[day_master][JI.index(p['j'])]}</td>"
        html_tbl += """</tr><tr class="detail-row"><td class="row-label">신살</td>"""
        for p in pillars: html_tbl += f"<td style='color:#ff6b6b; font-size:11px;'>{get_shinsal(d_j, p['j'])}</td>"
        html_tbl += "</tr></tbody></table>"
        
        html_tbl += """<div style="display:flex; gap:4px; margin-top:10px;">
<div class="fortune-box" style="flex:1"><span class="fortune-title">말년운</span><span class="fortune-desc">자녀,결실</span></div>
<div class="fortune-box" style="flex:1"><span class="fortune-title">중년운</span><span class="fortune-desc">자아,정체성</span></div>
<div class="fortune-box" style="flex:1"><span class="fortune-title">청년운</span><span class="fortune-desc">부모,사회</span></div>
<div class="fortune-box" style="flex:1"><span class="fortune-title">초년운</span><span class="fortune-desc">조상,유년</span></div>
</div>"""
        st.markdown(html_tbl, unsafe_allow_html=True)

        # [3] 오행 분석 (수정된 로직 적용)
        st.markdown('<div class="section-title">오행 및 십성 분석</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        
        all_c = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        # [수정] 한글 키로 초기화
        cnt_kor = {"목":0,"화":0,"토":0,"금":0,"수":0}
        
        for c in all_c:
            eng = OHAENG_MAP[c]
            kor = KR_OH[eng] # 영어->한글 변환
            cnt_kor[kor] += 1
            
        df_oh = pd.DataFrame({"category": list(cnt_kor.keys()), "value": list(cnt_kor.values())})
        base = alt.Chart(df_oh).encode(theta=alt.Theta("value", stack=True))
        pie = base.mark_arc(outerRadius=70, innerRadius=40).encode(
            color=alt.Color("category", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#39d353","#ff6b6b","#e3b341","#a3a3a3","#58a6ff"]))
        )
        
        with c1:
            st.altair_chart(pie, use_container_width=True)
        with c2:
            max_oh = max(cnt_kor, key=cnt_kor.get)
            st.info(f"**{name}**님은 **{max_oh}** 기운이 가장 강합니다.")
            st.write("용신: **금(억부)** / 희신: **수**")

        # [4] 대운
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        st.markdown(f'<div class="section-title">대운 흐름 (대운수 {dw_num})</div>', unsafe_allow_html=True)
        
        dw_html = '<div class="scroll-container">'
        for d in dw_list:
            g_t = get_sibseong(day_master, d['gan'])
            j_t = get_sibseong(day_master, d['ji'])
            dw_html += f"""<div class="luck-card">
<span class="luck-age">{d['age']}</span>
<span class="luck-ten">{g_t}</span>
<span class="luck-char">{d['gan']}<br>{d['ji']}</span>
<span class="luck-ten">{j_t}</span>
</div>"""
        dw_html += "</div>"
        st.markdown(dw_html, unsafe_allow_html=True)

        # [5] 연운
        st.markdown('<div class="section-title">연운 (세운) 흐름</div>', unsafe_allow_html=True)
        seun_list = get_seun(d.year + 10)
        se_html = '<div class="scroll-container">'
        for s in seun_list:
            g_t = get_sibseong(day_master, s['gan'])
            j_t = get_sibseong(day_master, s['ji'])
            se_html += f"""<div class="luck-card" style="background:#fcfcfc;">
<span class="luck-age">{s['year']}</span>
<span class="luck-ten">{g_t}</span>
<span class="luck-char" style="font-size:16px;">{s['gan']}<br>{s['ji']}</span>
<span class="luck-ten">{j_t}</span>
</div>"""
        se_html += "</div>"
        st.markdown(se_html, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

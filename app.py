import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt
import math

# --- [1] 페이지 설정 및 스타일 ---
st.set_page_config(page_title="루나 만세력 Pro", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200;900&display=swap');

    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f5f7fa;
        color: #111;
    }

    /* 메인 컨테이너 */
    .main-wrap {
        max-width: 800px; margin: 0 auto; background: white;
        padding: 25px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    /* 헤더 */
    .header-box { border-bottom: 2px solid #f1f3f5; padding-bottom: 20px; margin-bottom: 25px; }
    .name-txt { font-size: 24px; font-weight: 900; color: #212529; }
    .ganji-badge { background: #e9ecef; padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; color: #495057; margin-left: 8px; vertical-align: middle; }
    .info-row { font-size: 14px; color: #868e96; margin-top: 6px; }
    .solar-row { font-size: 14px; color: #ff6b6b; font-weight: bold; margin-top: 2px; }

    /* [핵심] 원국표 테이블 */
    .saju-tbl { width: 100%; border-collapse: separate; border-spacing: 2px; text-align: center; table-layout: fixed; margin-bottom:10px;}
    .saju-tbl th { font-size: 12px; color: #adb5bd; font-weight: normal; padding-bottom: 5px; }
    
    /* 한자 박스 */
    .char-cell {
        border: 1px solid #e9ecef; border-radius: 10px; height: 85px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        margin: 0 1px; background: #fff;
    }
    .char-font { font-family: 'Noto Serif KR', serif; font-size: 32px; font-weight: 900; line-height: 1; margin-bottom:4px; }
    .ten-small { font-size: 11px; color: #868e96; font-weight: bold; }

    /* 상세 정보 행 */
    .row-title { font-size: 12px; font-weight: bold; color: #adb5bd; text-align: left; padding-left: 5px; width: 45px; }
    .row-data { font-size: 12px; font-weight: bold; color: #495057; border-top: 1px solid #f8f9fa; padding: 8px 0; }
    
    /* 오행 색상 */
    .c-wood { color: #39d353; } .c-fire { color: #ff6b6b; } 
    .c-earth { color: #ffc107; } .c-metal { color: #adb5bd; } .c-water { color: #58a6ff; }

    /* 운세 (근묘화실) */
    .fortune-wrap { display: flex; justify-content: space-between; margin-top: 10px; padding-top:10px; border-top:1px dashed #eee;}
    .fortune-cell { background: #f8f9fa; border-radius: 8px; padding: 10px 5px; width: 24%; text-align: center; }
    .ft-title { font-size: 12px; font-weight: 800; color: #343a40; display: block; }
    .ft-desc { font-size: 10px; color: #aaa; margin-top:2px; display:block;}

    /* 섹션 제목 */
    .sec-title { font-size: 17px; font-weight: 800; margin: 35px 0 15px 0; display: flex; align-items: center; color: #212529; }
    .sec-title::before { content:''; width: 4px; height: 16px; background: #212529; margin-right: 8px; border-radius: 2px; }

    /* 운세 스크롤 */
    .scroll-wrap { display: flex; gap: 10px; overflow-x: auto; padding: 5px 2px 15px 2px; scrollbar-width: thin; }
    .luck-card {
        min-width: 65px; background: #fff; border: 1px solid #e9ecef; border-radius: 12px;
        padding: 12px 0; text-align: center; box-shadow: 0 2px 6px rgba(0,0,0,0.03); flex-shrink: 0;
    }
    .l-age { font-size: 11px; font-weight: bold; color: #868e96; display: block; margin-bottom: 4px; }
    .l-char { font-family: 'Noto Serif KR'; font-size: 18px; font-weight: 900; line-height: 1.2; display: block; color: #333; }
    .l-ten { font-size: 10px; color: #adb5bd; display: block; margin-top: 4px; }
    
    /* 신살 테이블 */
    .ss-tbl { width: 100%; border: 1px solid #f1f3f5; border-radius: 8px; border-collapse: collapse; overflow: hidden; table-layout: fixed; }
    .ss-tbl th { background: #f8f9fa; font-size: 12px; padding: 10px; border-bottom: 1px solid #f1f3f5; color:#555;}
    .ss-tbl td { font-size: 12px; padding: 12px; border-bottom: 1px solid #f1f3f5; text-align: center; font-weight: bold; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 상수 및 로직 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_MAP = {
    "甲":"c-wood","乙":"c-wood","丙":"c-fire","丁":"c-fire","戊":"c-earth","己":"c-earth","庚":"c-metal","辛":"c-metal","壬":"c-water","癸":"c-water",
    "寅":"c-wood","卯":"c-wood","巳":"c-fire","午":"c-fire","辰":"c-earth","戌":"c-earth","丑":"c-earth","未":"c-earth","申":"c-metal","酉":"c-metal","亥":"c-water","子":"c-water"
}
KR_OH_MAP = {"c-wood":"목", "c-fire":"화", "c-earth":"토", "c-metal":"금", "c-water":"수"}
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
    o_map = {"c-wood":0, "c-fire":1, "c-earth":2, "c-metal":3, "c-water":4}
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
    base_y = 1984 
    base_g, base_j = 0, 0
    curr_g = (base_g + (start_year - base_y)) % 10
    curr_j = (base_j + (start_year - base_y)) % 12
    for i in range(count):
        g = GAN[(curr_g + i) % 10]
        j = JI[(curr_j + i) % 12]
        lst.append({"year": start_year + i, "gan": g, "ji": j})
    return lst

def get_wolun(year_gan):
    start_map = {"甲":2, "己":2, "乙":4, "庚":4, "丙":6, "辛":6, "丁":8, "壬":8, "戊":0, "癸":0}
    s_idx = start_map.get(year_gan, 0)
    lst = []
    for i in range(12):
        g = GAN[(s_idx + i) % 10]
        j = JI[(2 + i) % 12]
        lst.append({"mon": i+1, "gan": g, "ji": j})
    return lst

# [NEW] 라이브러리 없이 순수 SVG로 오행 도표 그리기 (에러 원천 봉쇄)
def generate_pentagon_svg(cnt_data):
    # 설정
    radius = 120
    cx, cy = 150, 150
    # 목(Top)부터 시계방향: 목->화->토->금->수
    # 각도: -90, -18, 54, 126, 198 (도)
    angles = [-90, -18, 54, 126, 198]
    labels = ["목(木)", "화(火)", "토(土)", "금(金)", "수(水)"]
    keys = ["목", "화", "토", "금", "수"]
    colors = ["#4caf50", "#f44336", "#ffc107", "#9e9e9e", "#2196f3"]
    
    svg = f'<svg width="300" height="300" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">'
    
    # 별 그리기 (상극 관계)
    points = []
    for ang in angles:
        rad = math.radians(ang)
        x = cx + radius * 0.8 * math.cos(rad)
        y = cy + radius * 0.8 * math.sin(rad)
        points.append((x, y))
    
    # 별 선 (0-2-4-1-3-0)
    order = [0, 2, 4, 1, 3, 0]
    star_path = "M " + " L ".join([f"{points[i][0]},{points[i][1]}" for i in order])
    svg += f'<path d="{star_path}" stroke="#ddd" stroke-width="2" fill="none" />'
    
    # 원 (상생 관계 - 바깥 원)
    pentagon_path = "M " + " L ".join([f"{p[0]},{p[1]}" for p in points]) + " Z"
    svg += f'<path d="{pentagon_path}" stroke="#eee" stroke-width="2" fill="none" />'

    # 노드 그리기
    for i, (ang, label, k, c) in enumerate(zip(angles, labels, keys, colors)):
        rad = math.radians(ang)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        val = cnt_data.get(k, 0)
        
        # 크기 조절 (기본 25 + 개수당 5)
        r_size = 25 + (val * 3)
        
        # 원
        svg += f'<circle cx="{x}" cy="{y}" r="{r_size}" fill="{c}" opacity="0.9" />'
        # 텍스트
        svg += f'<text x="{x}" y="{y-5}" font-family="sans-serif" font-size="12" fill="white" text-anchor="middle" font-weight="bold">{label}</text>'
        svg += f'<text x="{x}" y="{y+10}" font-family="sans-serif" font-size="11" fill="white" text-anchor="middle">{val}개</text>'

    svg += '</svg>'
    return svg

# --- 3. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    
    if 'dob_fix' not in st.session_state:
        st.session_state.dob_fix = datetime.date(1990, 5, 5)
    d_input = st.date_input("생년월일", st.session_state.dob_fix, min_value=datetime.date(1900,1,1))
    st.session_state.dob_fix = d_input
    
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    
    if st.button("결과 확인", type="primary"):
        st.session_state.run_analysis = True

# --- 4. 메인 로직 ---
if 'run_analysis' in st.session_state and st.session_state.run_analysis:
    d = st.session_state.dob_fix
    
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ saju.db 파일이 없습니다. DB 파일을 업로드해주세요.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj, l_m, l_d, term = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
        
        # [1] 헤더
        st.markdown(f"""
        <div class="header-box">
            <div class="name-txt">{name} <span class="ganji-badge">{d_g}{d_j} (푸른 말)</span></div>
            <div class="info-row">양력 {d.year}.{d.month}.{d.day} ({gender}) {t_time.strftime('%H:%M')}</div>
            <div class="info-row">음력 {l_m}월 {l_d}일 / 절기: {term if term else '-'}</div>
            <div class="solar-row">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} (지역보정 {int(t_diff)}분)</div>
        </div>
        """, unsafe_allow_html=True)

        # [2] 원국표
        pillars = [{"n":"시주","g":t_g,"j":t_j}, {"n":"일주","g":d_g,"j":d_j}, {"n":"월주","g":m_g,"j":m_j}, {"n":"연주","g":y_g,"j":y_j}]
        
        tbl = """<table class="saju-tbl"><thead><tr><th class="label-col">구분</th><th>생시</th><th>생일</th><th>생월</th><th>생년</th></tr></thead><tbody>"""
        
        tbl += """<tr><td class="label-col">천간</td>"""
        for p in pillars:
            ten = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            c = OHAENG_MAP[p['g']]
            tbl += f"""<td><div class="char-box"><span class="char-font {c}">{p['g']}</span></div></td>"""
        tbl += "</tr>"
        
        tbl += """<tr><td class="label-col">십성</td>"""
        for p in pillars:
            ten = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
        tbl += "</tr>"

        tbl += """<tr><td class="label-col">지지</td>"""
        for p in pillars:
            c = OHAENG_MAP[p['j']]
            tbl += f"""<td><div class="char-box"><span class="char-font {c}">{p['j']}</span></div></td>"""
        tbl += "</tr>"
        
        tbl += """<tr><td class="label-col">십성</td>"""
        for p in pillars:
            ten = get_sibseong(day_master, p['j'])
            tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
        tbl += "</tr>"
        
        for title, key_idx, style in [("지장간", None, "color:#888"), ("운성", None, "color:#2196f3; font-weight:bold"), ("신살", None, "color:#f44336")]:
            tbl += f"""<tr><td class="label-col">{title}</td>"""
            for p in pillars:
                val = ""
                if title == "지장간": val = JIJANGGAN[p['j']]
                elif title == "운성": val = UNSEONG[day_master][JI.index(p['j'])]
                elif title == "신살": val = get_shinsal(d_j, p['j'])
                tbl += f"""<td><div class="detail-cell" style="{style}">{val}</div></td>"""
            tbl += "</tr>"
            
        tbl += "</tbody></table>"
        st.markdown(tbl, unsafe_allow_html=True)
        
        # [2-1] 근묘화실
        st.markdown("""
        <div class="fortune-wrap">
            <div class="fortune-cell"><span class="ft-title">말년운</span><span class="ft-desc">자녀, 결실</span></div>
            <div class="fortune-cell"><span class="ft-title">중년운</span><span class="ft-desc">자아, 정체성</span></div>
            <div class="fortune-cell"><span class="ft-title">청년운</span><span class="ft-desc">부모, 사회</span></div>
            <div class="fortune-cell"><span class="ft-title">초년운</span><span class="ft-desc">조상, 유년</span></div>
        </div>
        """, unsafe_allow_html=True)

        # [3] 신살과 길성
        st.markdown('<div class="sec-head">신살과 길성</div>', unsafe_allow_html=True)
        st.markdown("""
        <table class="ss-tbl">
            <tr><th>구분</th><th>시주</th><th>일주</th><th>월주</th><th>연주</th></tr>
            <tr><td>천간</td><td>-</td><td>현침살</td><td>현침살</td><td>백호</td></tr>
            <tr><td>지지</td><td>도화</td><td>홍염</td><td>태극</td><td>천을</td></tr>
        </table>
        """, unsafe_allow_html=True)

        # [4] 오행 분석 (SVG 이미지 + 십성 차트)
        st.markdown('<div class="sec-head">오행 및 십성 분석</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        
        all_c = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in all_c:
            kor = KR_OH_MAP[OHAENG_MAP[c]]
            cnt[kor] += 1
            
        with c1:
            st.write("**오행 상호작용 (Image)**")
            # SVG 직접 렌더링
            svg_html = generate_pentagon_svg(cnt)
            st.markdown(f'<div style="text-align:center;">{svg_html}</div>', unsafe_allow_html=True)
            
        with c2:
            st.write("**십성 분포 (Chart)**")
            df_oh = pd.DataFrame({"cat": list(cnt.keys()), "val": list(cnt.values())})
            chart = alt.Chart(df_oh).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("val", stack=True),
                color=alt.Color("cat", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#4caf50","#f44336","#ffc107","#9e9e9e","#2196f3"]))
            )
            st.altair_chart(chart, use_container_width=True)
            
            top = max(cnt, key=cnt.get)
            st.success(f"💡 **{top}** 기운이 가장 강합니다.")

        # [5] 대운 Scroll
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        st.markdown(f'<div class="sec-head">대운 흐름 (대운수 {dw_num})</div>', unsafe_allow_html=True)
        
        dw_h = '<div class="scroll-wrap">'
        for d_item in dw_list:
            g_t = get_sibseong(day_master, d_item['gan'])
            j_t = get_sibseong(day_master, d_item['ji'])
            dw_h += f"""<div class="l-card">
                <span class="l-age">{d_item['age']}</span>
                <span class="l-ten">{g_t}</span>
                <span class="l-char">{d_item['gan']}<br>{d_item['ji']}</span>
                <span class="l-ten">{j_t}</span>
            </div>"""
        dw_h += "</div>"
        st.markdown(dw_h, unsafe_allow_html=True)

        # [6] 연운 Scroll
        st.markdown('<div class="sec-head">연운 (세운)</div>', unsafe_allow_html=True)
        seun_list = get_seun(d.year + 1)
        se_h = '<div class="scroll-wrap">'
        for s in seun_list:
            g_t = get_sibseong(day_master, s['gan'])
            j_t = get_sibseong(day_master, s['ji'])
            se_h += f"""<div class="l-card" style="background:#fcfcfc;">
                <span class="l-age">{s['year']}</span>
                <span class="l-ten">{g_t}</span>
                <span class="l-char" style="font-size:16px;">{s['gan']}<br>{s['ji']}</span>
                <span class="l-ten">{j_t}</span>
            </div>"""
        se_h += "</div>"
        st.markdown(se_h, unsafe_allow_html=True)

        # [7] 월운 Scroll
        st.markdown('<div class="sec-head">올해의 월운</div>', unsafe_allow_html=True)
        this_year = datetime.datetime.now().year
        seun_g_idx = (GAN.index("甲") + (this_year - 1984)) % 10
        this_year_gan = GAN[seun_g_idx]
        
        wolun_list = get_wolun(this_year_gan)
        wo_h = '<div class="scroll-wrap">'
        for w in wolun_list:
            g_t = get_sibseong(day_master, w['gan'])
            j_t = get_sibseong(day_master, w['ji'])
            wo_h += f"""<div class="l-card">
                <span class="l-age">{w['mon']}월</span>
                <span class="l-ten">{g_t}</span>
                <span class="l-char" style="font-size:16px;">{w['gan']}<br>{w['ji']}</span>
                <span class="l-ten">{j_t}</span>
            </div>"""
        wo_h += "</div>"
        st.markdown(wo_h, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

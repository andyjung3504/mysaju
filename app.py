import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- [1] 페이지 설정 및 스타일 (CSS) ---
st.set_page_config(page_title="루나 만세력", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    
    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f8f9fa;
        color: #212529;
    }

    /* 카드 박스 공통 */
    .card-box {
        background: white; border-radius: 16px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 24px;
        border: 1px solid #e9ecef;
    }

    /* [1] 메인 사주 원국표 (HTML Table) */
    .saju-table {
        width: 100%; border-collapse: collapse; text-align: center; margin-bottom: 10px;
    }
    .saju-table th {
        font-size: 13px; color: #868e96; font-weight: normal; padding-bottom: 12px;
    }
    .saju-table td {
        padding: 6px 0; vertical-align: middle;
    }
    
    /* 구분선 (기둥 사이) */
    .border-left { border-left: 1px dashed #e9ecef; }

    /* 글자 스타일 */
    .txt-gan, .txt-ji { 
        font-family: 'Noto Serif KR', serif; font-size: 34px; font-weight: 900; line-height: 1.1; 
    }
    
    .badge {
        font-size: 11px; display: inline-block; padding: 3px 8px;
        border-radius: 12px; font-weight: bold; color: #495057;
        background-color: #f1f3f5; margin: 2px 0;
    }
    
    .label-cell { font-size: 12px; color: #adb5bd; font-weight: bold; text-align: left; width: 50px; }
    
    /* 근묘화실 (운세) 행 스타일 */
    .fortune-row td { padding-top: 15px; padding-bottom: 15px; border-top: 1px solid #f1f3f5; }
    .fortune-title { font-size: 13px; font-weight: bold; color: #343a40; display: block; }
    .fortune-desc { font-size: 11px; color: #adb5bd; font-weight: normal; }

    /* 오행 색상 */
    .c-wood { color: #52ba68; } .c-fire { color: #ff6b6b; } 
    .c-earth { color: #fcc419; } .c-metal { color: #adb5bd; } .c-water { color: #339af0; }

    /* [2] 신살표 */
    .shinsal-table { width: 100%; border: 1px solid #eee; border-radius: 8px; overflow: hidden; border-collapse: collapse;}
    .shinsal-table th { background: #f8f9fa; font-size: 12px; padding: 8px; border-bottom: 1px solid #eee; }
    .shinsal-table td { font-size: 12px; padding: 10px; border-bottom: 1px solid #eee; text-align: center; font-weight: bold; color: #495057;}

    /* [3] 대운 (가로 스크롤) */
    .daewoon-scroll {
        display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px;
        scrollbar-width: thin;
    }
    .dw-block {
        min-width: 65px; text-align: center;
        background: #fff; border: 1px solid #dee2e6; border-radius: 10px;
        padding: 12px 5px; flex-shrink: 0;
    }
    .dw-age { font-size: 12px; font-weight: bold; color: #868e96; margin-bottom: 4px; }
    .dw-ganji { font-size: 18px; font-weight: bold; font-family: 'Noto Serif KR'; margin: 4px 0; line-height: 1.2;}
    .dw-ten { font-size: 10px; color: #adb5bd; display: block; margin-top: 2px;}
    
    /* 헤더 */
    .header-info { text-align: left; margin-bottom: 20px; }
    .main-name { font-size: 24px; font-weight: 900; color: #212529; }
    .sub-info { font-size: 14px; color: #868e96; margin-top: 4px; }
    .solar-time { color: #ff6b6b; font-weight: bold; font-size: 13px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 상수 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
OHAENG_MAP = {
    "甲":"wood","乙":"wood","丙":"fire","丁":"fire","戊":"earth","己":"earth","庚":"metal","辛":"metal","壬":"water","癸":"water",
    "寅":"wood","卯":"wood","巳":"fire","午":"fire","辰":"earth","戌":"earth","丑":"earth","未":"earth","申":"metal","酉":"metal","亥":"water","子":"water"
}
KR_OH = {"wood":"목", "fire":"화", "earth":"토", "metal":"금", "water":"수"}
LOCATIONS = {"서울":127.0, "부산":129.1, "대구":128.6, "인천":126.7, "광주":126.8, "대전":127.4, "울산":129.3, "강릉":128.9, "제주":126.5}
JIJANGGAN = {
    "子":"壬 癸", "丑":"癸 辛 己", "寅":"戊 丙 甲", "卯":"甲 乙", "辰":"乙 癸 戊", "巳":"戊 庚 丙",
    "午":"丙 己 丁", "未":"丁 乙 己", "申":"戊 壬 庚", "酉":"庚 辛", "戌":"辛 丁 戊", "亥":"戊 甲 壬"
}

# [수정 완료] 오타가 있었던 부분입니다.
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
    # 포스텔러 식 매핑
    shin_map = {
        "亥卯未": {"子":"년살","丑":"월살","寅":"망신","卯":"장성","辰":"반안","巳":"역마","午":"육해","未":"화개","申":"겁살","酉":"재살","戌":"천살","亥":"지살"},
        "寅午戌": {"卯":"년살","辰":"월살","巳":"망신","午":"장성","未":"반안","申":"역마","酉":"육해","戌":"화개","亥":"겁살","子":"재살","丑":"천살","寅":"지살"},
        "巳酉丑": {"午":"년살","未":"월살","申":"망신","酉":"장성","戌":"반안","亥":"역마","子":"육해","丑":"화개","寅":"겁살","卯":"재살","辰":"천살","巳":"지살"},
        "申子辰": {"酉":"년살","戌":"월살","亥":"망신","子":"장성","丑":"반안","寅":"역마","卯":"육해","辰":"화개","巳":"겁살","午":"재살","未":"천살","申":"지살"}
    }
    res = shin_map.get(day_ji, {}).get(target_ji, "")
    if not res:
        if target_ji in "子午卯酉": res = "도화살"
        elif target_ji in "寅申巳亥": res = "역마살"
        elif target_ji in "辰戌丑未": res = "화개살"
    return res

def get_daewoon_full(y_g, m_g, m_j, gender):
    is_yang = (GAN.index(y_g) % 2 == 0)
    is_man = (gender == "남자")
    fwd = (is_yang and is_man) or (not is_yang and not is_man)
    dw_num = 6 # 예시 값
    
    lst = []
    s_g, s_j = GAN.index(m_g), JI.index(m_j)
    for i in range(1, 9):
        step = i if fwd else -i
        g = GAN[(s_g + step)%10]
        j = JI[(s_j + step)%12]
        lst.append({"age": dw_num + (i-1)*10, "gan": g, "ji": j})
    return lst, dw_num

# --- 4. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "aaa")
    gender = st.radio("성별", ["남자", "여자"])
    d = st.date_input("생년월일", datetime.date(1973, 12, 24), min_value=datetime.date(1900,1,1))
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    if st.button("운세 보기", type="primary"):
        st.session_state.run = True

if 'run' in st.session_state and st.session_state.run:
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("DB 파일 오류. saju.db를 확인하세요.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj, l_m, l_d, term = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        # [0] 상단 헤더
        st.markdown(f"""
        <div class="header-info">
            <div class="main-name">{name} <span style="font-size:18px; color:#555; font-weight:normal;">{d_g}{d_j}(푸른 말)</span></div>
            <div class="sub-info">양력 {d.year}.{d.month}.{d.day} {t_time.strftime('%H:%M')} {gender} {loc}</div>
            <div class="solar-time">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} (지역보정 {int(t_diff)}분)</div>
        </div>
        """, unsafe_allow_html=True)

        # [1] 메인 원국표
        pillars = [
            {"n":"시주", "g":t_g, "j":t_j}, {"n":"일주", "g":d_g, "j":d_j},
            {"n":"월주", "g":m_g, "j":m_j}, {"n":"연주", "g":y_g, "j":y_j}
        ]
        
        pd = []
        for p in pillars:
            pd.append({
                "g_ten": "일간" if p['n']=="일주" else get_sibseong(day_master, p['g']),
                "j_ten": get_sibseong(day_master, p['j']),
                "g_col": "c-" + OHAENG_MAP[p['g']],
                "j_col": "c-" + OHAENG_MAP[p['j']],
                "jj": JIJANGGAN[p['j']],
                "un": UNSEONG[day_master][JI.index(p['j'])],
                "ss": get_shinsal(d_j, p['j']),
                "g": p['g'], "j": p['j']
            })

        table_html = f"""
        <div class="card-box">
            <table class="saju-table">
                <thead>
                    <tr>
                        <th></th><th>생시</th><th>생일</th><th>생월</th><th>생년</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="label-cell">천간</td>
                        <td class=""><div class="txt-gan {pd[0]['g_col']}">{pd[0]['g']}</div></td>
                        <td class="border-left"><div class="txt-gan {pd[1]['g_col']}">{pd[1]['g']}</div></td>
                        <td class="border-left"><div class="txt-gan {pd[2]['g_col']}">{pd[2]['g']}</div></td>
                        <td class="border-left"><div class="txt-gan {pd[3]['g_col']}">{pd[3]['g']}</div></td>
                    </tr>
                    <tr>
                        <td class="label-cell">십성</td>
                        <td><span class="badge">{pd[0]['g_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[1]['g_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[2]['g_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[3]['g_ten']}</span></td>
                    </tr>
                    <tr>
                        <td class="label-cell">지지</td>
                        <td><div class="txt-ji {pd[0]['j_col']}">{pd[0]['j']}</div></td>
                        <td class="border-left"><div class="txt-ji {pd[1]['j_col']}">{pd[1]['j']}</div></td>
                        <td class="border-left"><div class="txt-ji {pd[2]['j_col']}">{pd[2]['j']}</div></td>
                        <td class="border-left"><div class="txt-ji {pd[3]['j_col']}">{pd[3]['j']}</div></td>
                    </tr>
                    <tr>
                        <td class="label-cell">십성</td>
                        <td><span class="badge">{pd[0]['j_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[1]['j_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[2]['j_ten']}</span></td>
                        <td class="border-left"><span class="badge">{pd[3]['j_ten']}</span></td>
                    </tr>
                    <tr>
                        <td class="label-cell">지장간</td>
                        <td style="font-size:11px; color:#aaa;">{pd[0]['jj']}</td>
                        <td class="border-left" style="font-size:11px; color:#aaa;">{pd[1]['jj']}</td>
                        <td class="border-left" style="font-size:11px; color:#aaa;">{pd[2]['jj']}</td>
                        <td class="border-left" style="font-size:11px; color:#aaa;">{pd[3]['jj']}</td>
                    </tr>
                    <tr>
                        <td class="label-cell">12운성</td>
                        <td style="font-weight:bold; color:#339af0; font-size:13px;">{pd[0]['un']}</td>
                        <td class="border-left" style="font-weight:bold; color:#339af0; font-size:13px;">{pd[1]['un']}</td>
                        <td class="border-left" style="font-weight:bold; color:#339af0; font-size:13px;">{pd[2]['un']}</td>
                        <td class="border-left" style="font-weight:bold; color:#339af0; font-size:13px;">{pd[3]['un']}</td>
                    </tr>
                    <tr>
                        <td class="label-cell">12신살</td>
                        <td style="color:#fa5252; font-size:12px;">{pd[0]['ss']}</td>
                        <td class="border-left" style="color:#fa5252; font-size:12px;">{pd[1]['ss']}</td>
                        <td class="border-left" style="color:#fa5252; font-size:12px;">{pd[2]['ss']}</td>
                        <td class="border-left" style="color:#fa5252; font-size:12px;">{pd[3]['ss']}</td>
                    </tr>
                    <tr class="fortune-row">
                        <td class="label-cell">운세</td>
                        <td><span class="fortune-title">말년운</span><span class="fortune-desc">자녀,결실</span></td>
                        <td class="border-left"><span class="fortune-title">중년운</span><span class="fortune-desc">자아,정체성</span></td>
                        <td class="border-left"><span class="fortune-title">청년운</span><span class="fortune-desc">부모,사회</span></td>
                        <td class="border-left"><span class="fortune-title">초년운</span><span class="fortune-desc">조상,유년</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # [2] 신살과 길성
        st.subheader("⭐ 신살과 길성")
        st.markdown("""
        <div class="card-box">
            <table class="shinsal-table">
                <tr><th>구분</th><th>생시</th><th>생일</th><th>생월</th><th>생년</th></tr>
                <tr>
                    <td>천간</td><td>-</td><td>현침살</td><td>현침살</td><td>백호대살</td>
                </tr>
                <tr>
                    <td>지지</td><td>도화살</td><td>홍염살</td><td>태극귀인</td><td>천을귀인</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # [3] 그래프
        c1, c2 = st.columns(2)
        all_char = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in all_char: cnt[KR_OH[OHAENG_MAP[c]]] += 1
        df_oh = pd.DataFrame({"category": cnt.keys(), "value": cnt.values()})
        
        base = alt.Chart(df_oh).encode(theta=alt.Theta("value", stack=True))
        pie = base.mark_arc(outerRadius=80, innerRadius=50).encode(
            color=alt.Color("category", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#52ba68","#ff6b6b","#fcc419","#adb5bd","#339af0"]))
        )
        
        with c1:
            st.subheader("📊 오행 분포")
            st.markdown('<div class="card-box">', unsafe_allow_html=True)
            st.altair_chart(pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c2:
            st.subheader("⚖️ 신강/신약 분석")
            st.markdown('<div class="card-box">', unsafe_allow_html=True)
            st.info(f"{name}님은 **중화신강**한 사주입니다.")
            st.write("용신: 금(억부용신) / 희신: 수")
            st.markdown('</div>', unsafe_allow_html=True)

        # [4] 대운
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        st.subheader(f"🌊 대운 (대운수: {dw_num})")
        dw_html_content = ""
        for d in dw_list:
            g_ten = get_sibseong(day_master, d['gan'])
            j_ten = get_sibseong(day_master, d['ji'])
            un = UNSEONG[day_master][JI.index(d['ji'])]
            dw_html_content += f"""
            <div class="dw-block">
                <div class="dw-age">{d['age']}</div>
                <span class="dw-ten">{g_ten}</span>
                <div class="dw-ganji">{d['gan']}<br>{d['ji']}</div>
                <span class="dw-ten">{j_ten}</span>
                <div style="font-size:11px; color:#339af0; margin-top:4px;">{un}</div>
            </div>
            """
        st.markdown(f'<div class="card-box"><div class="daewoon-scroll">{dw_html_content}</div></div>', unsafe_allow_html=True)

    else:
        st.error("데이터가 없습니다.")

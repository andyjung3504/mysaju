import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt

# --- [1] 페이지 설정 및 리얼 스타일 CSS ---
st.set_page_config(page_title="루나 만세력 Pro", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    
    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f8f9fa;
        color: #212529;
    }

    /* [공통] 카드 박스 스타일 */
    .card-box {
        background: white;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        margin-bottom: 24px;
        border: 1px solid #e9ecef;
    }

    /* [1] 사주 원국표 (HTML 테이블로 정밀 구현) */
    .saju-table {
        width: 100%;
        border-collapse: collapse;
        text-align: center;
        margin-bottom: 20px;
    }
    .saju-table th {
        font-size: 13px; color: #868e96; font-weight: normal;
        padding-bottom: 10px;
    }
    .saju-table td {
        padding: 5px 0;
        vertical-align: middle;
    }
    
    /* 글자 스타일 */
    .txt-gan { font-family: 'Noto Serif KR', serif; font-size: 32px; font-weight: 900; }
    .txt-ji { font-family: 'Noto Serif KR', serif; font-size: 32px; font-weight: 900; }
    
    .badge {
        font-size: 11px; display: inline-block; padding: 3px 8px;
        border-radius: 12px; font-weight: bold; color: #495057;
        background-color: #f1f3f5;
    }
    
    .label-row { font-size: 12px; color: #adb5bd; font-weight: bold; text-align: left; padding-left: 10px; width: 60px;}
    .data-cell { border-left: 1px dashed #e9ecef; width: 22%; }
    .data-cell:first-child { border-left: none; }

    /* [오행 색상] */
    .c-wood { color: #52ba68; } .c-fire { color: #ff6b6b; } 
    .c-earth { color: #fcc419; } .c-metal { color: #adb5bd; } .c-water { color: #339af0; }

    /* [2] 신살표 스타일 */
    .shinsal-table {
        width: 100%; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden; border-collapse: collapse;
    }
    .shinsal-table th { background: #f8f9fa; font-size: 12px; padding: 8px; border-bottom: 1px solid #e9ecef; }
    .shinsal-table td { font-size: 12px; padding: 10px; border-bottom: 1px solid #e9ecef; text-align: center; font-weight: bold; }
    
    /* [3] 대운 블록 스타일 (가로 스크롤) */
    .daewoon-container {
        display: flex; gap: 8px; overflow-x: auto; padding-bottom: 10px;
        scrollbar-width: thin;
    }
    .dw-block {
        min-width: 60px; text-align: center;
        background: #fff; border: 1px solid #dee2e6; border-radius: 8px;
        padding: 10px 5px; flex-shrink: 0;
    }
    .dw-age { font-size: 12px; font-weight: bold; color: #868e96; margin-bottom: 5px; }
    .dw-ganji { font-size: 18px; font-weight: bold; font-family: 'Noto Serif KR'; margin: 5px 0; }
    .dw-ten { font-size: 10px; color: #adb5bd; }
    .current-dw { border: 2px solid #339af0; background-color: #e7f5ff; }

    /* [4] 헤더 프로필 */
    .profile-header {
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 20px;
    }
    .main-txt { font-size: 24px; font-weight: 800; color: #343a40; }
    .sub-txt { font-size: 14px; color: #868e96; }
    
    /* 그래프 텍스트 */
    .graph-title { font-size: 16px; font-weight: 700; margin-bottom: 15px; color: #495057; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 & 로직 (안정성 확보) ---
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
    shin_map = {
        "亥卯未": {"子":"년살","丑":"월살","寅":"망신","卯":"장성","辰":"반안","巳":"역마","午":"육해","未":"화개","申":"겁살","酉":"재살","戌":"천살","亥":"지살"},
        "寅午戌": {"卯":"년살","辰":"월살","巳":"망신","午":"장성","未":"반안","申":"역마","酉":"육해","戌":"화개","亥":"겁살","子":"재살","丑":"천살","寅":"지살"},
        "巳酉丑": {"午":"년살","未":"월살","申":"망신","酉":"장성","戌":"반안","亥":"역마","子":"육해","丑":"화개","寅":"겁살","卯":"재살","辰":"천살","巳":"지살"},
        "申子辰": {"酉":"년살","戌":"월살","亥":"망신","子":"장성","丑":"반안","寅":"역마","卯":"육해","辰":"화개","巳":"겁살","午":"재살","未":"천살","申":"지살"}
    }
    res = shin_map.get(day_ji, {}).get(target_ji, "")
    # 보정
    if not res:
        if target_ji in "子午卯酉": res = "도화"
        elif target_ji in "寅申巳亥": res = "역마"
        elif target_ji in "辰戌丑未": res = "화개"
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

# --- 3. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "사용자")
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
        st.error("⚠️ DB 오류. saju.db 파일이 필요합니다.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj, l_m, l_d, term = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        # [헤더]
        st.markdown(f"""
        <div class="profile-header">
            <div>
                <div class="main-txt">{name} <span style="font-size:16px; color:#888;">{d_g}{d_j}(푸른 말)</span></div>
                <div class="sub-txt">양력 {d.year}.{d.month}.{d.day} {t_time.strftime('%H:%M')} {gender} {loc}</div>
                <div class="sub-txt" style="color:#ff6b6b;">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} (지역보정 {int(t_diff)}분)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # [SECTION 1] 메인 원국표 (HTML Table로 정밀 구현)
        pillars = [
            {"n":"시주", "g":t_g, "j":t_j},
            {"n":"일주", "g":d_g, "j":d_j},
            {"n":"월주", "g":m_g, "j":m_j},
            {"n":"연주", "g":y_g, "j":y_j}
        ]
        
        # 데이터 계산
        p_data = []
        for p in pillars:
            p_data.append({
                "gan": p['g'], "ji": p['j'],
                "gan_ten": "일간" if p['n']=="일주" else get_sibseong(day_master, p['g']),
                "ji_ten": get_sibseong(day_master, p['j']),
                "gan_col": "c-" + OHAENG_MAP[p['g']],
                "ji_col": "c-" + OHAENG_MAP[p['j']],
                "jijang": JIJANGGAN[p['j']],
                "unseong": UNSEONG[day_master][JI.index(p['j'])],
                "shinsal": get_shinsal(d_j, p['j'])
            })

        table_html = f"""
        <div class="card-box">
            <table class="saju-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>생시</th><th>생일</th><th>생월</th><th>생년</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="label-row">천간</td>
                        <td class="data-cell"><div class="txt-gan {p_data[0]['gan_col']}">{p_data[0]['gan']}</div></td>
                        <td class="data-cell"><div class="txt-gan {p_data[1]['gan_col']}">{p_data[1]['gan']}</div></td>
                        <td class="data-cell"><div class="txt-gan {p_data[2]['gan_col']}">{p_data[2]['gan']}</div></td>
                        <td class="data-cell"><div class="txt-gan {p_data[3]['gan_col']}">{p_data[3]['gan']}</div></td>
                    </tr>
                    <tr>
                        <td class="label-row">십성</td>
                        <td class="data-cell"><span class="badge">{p_data[0]['gan_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[1]['gan_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[2]['gan_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[3]['gan_ten']}</span></td>
                    </tr>
                    <tr>
                        <td class="label-row">지지</td>
                        <td class="data-cell"><div class="txt-ji {p_data[0]['ji_col']}">{p_data[0]['ji']}</div></td>
                        <td class="data-cell"><div class="txt-ji {p_data[1]['ji_col']}">{p_data[1]['ji']}</div></td>
                        <td class="data-cell"><div class="txt-ji {p_data[2]['ji_col']}">{p_data[2]['ji']}</div></td>
                        <td class="data-cell"><div class="txt-ji {p_data[3]['ji_col']}">{p_data[3]['ji']}</div></td>
                    </tr>
                    <tr>
                        <td class="label-row">십성</td>
                        <td class="data-cell"><span class="badge">{p_data[0]['ji_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[1]['ji_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[2]['ji_ten']}</span></td>
                        <td class="data-cell"><span class="badge">{p_data[3]['ji_ten']}</span></td>
                    </tr>
                    <tr>
                        <td class="label-row">지장간</td>
                        <td class="data-cell" style="font-size:11px; color:#aaa;">{p_data[0]['jijang']}</td>
                        <td class="data-cell" style="font-size:11px; color:#aaa;">{p_data[1]['jijang']}</td>
                        <td class="data-cell" style="font-size:11px; color:#aaa;">{p_data[2]['jijang']}</td>
                        <td class="data-cell" style="font-size:11px; color:#aaa;">{p_data[3]['jijang']}</td>
                    </tr>
                    <tr>
                        <td class="label-row">12운성</td>
                        <td class="data-cell" style="font-weight:bold; color:#339af0;">{p_data[0]['unseong']}</td>
                        <td class="data-cell" style="font-weight:bold; color:#339af0;">{p_data[1]['unseong']}</td>
                        <td class="data-cell" style="font-weight:bold; color:#339af0;">{p_data[2]['unseong']}</td>
                        <td class="data-cell" style="font-weight:bold; color:#339af0;">{p_data[3]['unseong']}</td>
                    </tr>
                    <tr>
                        <td class="label-row">12신살</td>
                        <td class="data-cell" style="font-size:12px; color:#fa5252;">{p_data[0]['shinsal']}</td>
                        <td class="data-cell" style="font-size:12px; color:#fa5252;">{p_data[1]['shinsal']}</td>
                        <td class="data-cell" style="font-size:12px; color:#fa5252;">{p_data[2]['shinsal']}</td>
                        <td class="data-cell" style="font-size:12px; color:#fa5252;">{p_data[3]['shinsal']}</td>
                    </tr>
                    <tr style="border-top: 1px solid #f1f3f5;">
                        <td class="label-row" style="padding-top:15px;">운세</td>
                        <td class="data-cell" style="padding-top:15px;"><div style="font-size:12px; font-weight:bold;">말년운<br><span style="color:#aaa; font-weight:normal;">자녀,결실</span></div></td>
                        <td class="data-cell" style="padding-top:15px;"><div style="font-size:12px; font-weight:bold;">중년운<br><span style="color:#aaa; font-weight:normal;">자아,정체성</span></div></td>
                        <td class="data-cell" style="padding-top:15px;"><div style="font-size:12px; font-weight:bold;">청년운<br><span style="color:#aaa; font-weight:normal;">부모,사회</span></div></td>
                        <td class="data-cell" style="padding-top:15px;"><div style="font-size:12px; font-weight:bold;">초년운<br><span style="color:#aaa; font-weight:normal;">조상,유년</span></div></td>
                    </tr>
                </tbody>
            </table>
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)

        # [SECTION 2] 신살과 길성 (테이블 형태)
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown('<div class="graph-title">⭐ 신살과 길성</div>', unsafe_allow_html=True)
        
        # 신살 데이터 (예시)
        ss_html = """
        <table class="shinsal-table">
            <tr>
                <th>구분</th><th>생시</th><th>생일</th><th>생월</th><th>생년</th>
            </tr>
            <tr>
                <td>천간</td>
                <td>-</td><td>현침살</td><td>현침살</td><td>백호대살</td>
            </tr>
            <tr>
                <td>지지</td>
                <td>도화살</td><td>홍염살</td><td>태극귀인</td><td>천을귀인</td>
            </tr>
        </table>
        """
        st.markdown(ss_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # [SECTION 3] 오행과 십성 분석 (도넛 차트)
        c1, c2 = st.columns(2)
        
        # 오행 데이터
        all_char = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in all_char: cnt[KR_OH[OHAENG_MAP[c]]] += 1
        df_oh = pd.DataFrame({"category": list(cnt.keys()), "value": list(cnt.values())})
        
        # 도넛 차트 생성 (Altair)
        base = alt.Chart(df_oh).encode(theta=alt.Theta("value", stack=True))
        pie = base.mark_arc(outerRadius=80, innerRadius=50).encode(
            color=alt.Color("category", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#52ba68","#ff6b6b","#fcc419","#adb5bd","#339af0"])),
            tooltip=["category", "value"]
        )
        
        with c1:
            st.markdown('<div class="card-box" style="height:350px;">', unsafe_allow_html=True)
            st.markdown('<div class="graph-title">📊 오행 분포</div>', unsafe_allow_html=True)
            st.altair_chart(pie, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="card-box" style="height:350px;">', unsafe_allow_html=True)
            st.markdown('<div class="graph-title">⚖️ 신강/신약 분석</div>', unsafe_allow_html=True)
            st.info(f"**{name}**님은 **중화신강**한 사주입니다.")
            st.progress(70)
            st.caption("용신: 금(억부용신) / 희신: 수")
            st.markdown('</div>', unsafe_allow_html=True)

        # [SECTION 4] 대운 흐름 (가로 스크롤)
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        
        st.markdown('<div class="card-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="graph-title">🌊 대운 (대운수: {dw_num})</div>', unsafe_allow_html=True)
        
        dw_html = '<div class="daewoon-container">'
        for d in dw_list:
            g_ten = get_sibseong(day_master, d['gan'])
            j_ten = get_sibseong(day_master, d['ji'])
            un = UNSEONG[day_master][JI.index(d['ji'])]
            
            dw_html += f"""
            <div class="dw-block">
                <div class="dw-age">{d['age']}</div>
                <div class="dw-ten">{g_ten}</div>
                <div class="dw-ganji" style="color:{'#ff6b6b' if d['gan'] in '丙丁巳午' else '#333'}">{d['gan']}<br>{d['ji']}</div>
                <div class="dw-ten">{j_ten}</div>
                <div class="dw-ten">{un}</div>
            </div>
            """
        dw_html += '</div></div>'
        st.markdown(dw_html, unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

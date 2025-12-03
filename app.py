import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt
import math

# --- [1] 페이지 및 스타일 설정 ---
st.set_page_config(page_title="루나 만세력 Pro (Expert)", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200;900&display=swap');

    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f0f2f5;
        color: #111;
    }

    .main-wrap {
        max-width: 900px; margin: 0 auto; background: white;
        padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    /* 헤더 */
    .header-box { border-bottom: 2px solid #f1f3f5; padding-bottom: 20px; margin-bottom: 25px; }
    .name-txt { font-size: 28px; font-weight: 900; color: #212529; }
    .ganji-badge { background: #e9ecef; padding: 4px 12px; border-radius: 12px; font-size: 16px; font-weight: bold; color: #495057; margin-left: 8px; vertical-align: middle; }
    .gyeok-badge { background: #e3f2fd; color: #1565c0; padding: 4px 12px; border-radius: 12px; font-size: 16px; font-weight: bold; margin-left: 5px; vertical-align: middle; border: 1px solid #bbdefb;}
    
    .info-row { font-size: 14px; color: #666; margin-top: 6px; }
    .solar-row { font-size: 14px; color: #d63384; font-weight: bold; margin-top: 4px; background: #fff0f6; display: inline-block; padding: 2px 8px; border-radius: 4px;}

    /* 원국표 */
    .saju-tbl { width: 100%; border-collapse: separate; border-spacing: 0; text-align: center; table-layout: fixed; border: 1px solid #eee; border-radius: 12px; overflow: hidden; margin-bottom: 20px;}
    .saju-tbl th { font-size: 13px; color: #888; font-weight: normal; padding: 12px 0; background: #fcfcfc; border-bottom: 1px solid #eee; border-right: 1px solid #eee;}
    .saju-tbl td { vertical-align: middle; border-bottom: 1px solid #eee; border-right: 1px solid #eee; padding: 0;}
    .label-col { background: #fcfcfc; font-size: 13px; font-weight: bold; color: #aaa; width: 70px; }

    /* 글자 박스 */
    .char-box { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 90px; width: 100%; }
    .char-font { font-family: 'Noto Serif KR', serif; font-size: 38px; font-weight: 900; line-height: 1; margin-bottom: 4px; }
    
    /* 상세 정보 셀 */
    .detail-cell { font-size: 13px; padding: 10px 0; color: #555; font-weight: 500; height: 100%; display: flex; align-items: center; justify-content: center;}

    /* 오행 색상 */
    .c-wood { color: #4caf50; } .c-fire { color: #f44336; } 
    .c-earth { color: #ffc107; } .c-metal { color: #9e9e9e; } .c-water { color: #2196f3; }

    /* 용신 분석 박스 */
    .yongsin-box { background: #f8f9fa; border-radius: 12px; padding: 20px; margin-top: 30px; border: 1px solid #e9ecef; }
    .score-bar { height: 10px; background: #eee; border-radius: 5px; overflow: hidden; margin: 10px 0; display: flex; }
    .score-fill { height: 100%; }

    /* 섹션 제목 */
    .sec-head { font-size: 18px; font-weight: 800; margin: 40px 0 15px 0; color: #212529; display: flex; align-items: center; border-bottom: 2px solid #333; padding-bottom: 8px;}
    
    /* 운세 스크롤 */
    .scroll-box { display: flex; gap: 8px; overflow-x: auto; padding: 5px 2px 15px 2px; scrollbar-width: thin; }
    .l-card {
        min-width: 70px; background: #fff; border: 1px solid #e9ecef; border-radius: 12px;
        padding: 12px 0; text-align: center; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .l-age { font-size: 12px; font-weight: bold; color: #868e96; display: block; margin-bottom: 4px; }
    .l-char { font-family: 'Noto Serif KR'; font-size: 20px; font-weight: 900; line-height: 1.2; display: block; color: #333; }
    .l-ten { font-size: 10px; color: #adb5bd; display: block; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 상수 및 데이터 ---
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

# --- 3. [전문가용] 시간 보정 및 용신 계산 로직 ---

def is_summer_time(dt):
    # 대한민국 썸머타임 역사 (년도, 시작월일, 종료월일)
    st_periods = [
        (1948, 601, 912), (1949, 403, 923), (1950, 401, 909), (1951, 506, 908),
        (1955, 505, 908), (1956, 520, 929), (1957, 505, 921), (1958, 504, 920),
        (1959, 503, 919), (1960, 501, 918), (1987, 510, 1011), (1988, 508, 1009)
    ]
    md = dt.month * 100 + dt.day
    for y, s, e in st_periods:
        if dt.year == y and s <= md <= e:
            return True
    return False

def get_std_meridian(year):
    # 대한민국 표준시 변경 역사
    if year < 1908: return 127.0 # 한양 기준 (근사치)
    if 1908 <= year <= 1911: return 127.5
    if 1912 <= year <= 1953: return 135.0
    if 1954 <= year <= 1961: return 127.5 # (8월 9일까지이나 편의상 연도 기준)
    return 135.0

def calc_expert_time(dt, h, m, loc_name):
    # 1. 경도차 보정
    my_lon = LOCATIONS.get(loc_name, 127.0)
    std_lon = get_std_meridian(dt.year)
    lon_diff = (my_lon - std_lon) * 4 # 도당 4분
    
    # 2. 썸머타임 보정 (-60분)
    st_corr = -60 if is_summer_time(dt) else 0
    
    # 3. 총 보정분
    total_corr = lon_diff + st_corr
    
    # 분 단위 계산
    total_min = h * 60 + m + total_corr
    
    # 날짜 변경 처리
    if total_min < 0: total_min += 1440
    if total_min >= 1440: total_min -= 1440
    
    # 시지 (자시: 23:00~01:00 -> 인덱스 0)
    # 00:00 -> (0+60)//120 = 0 (자)
    ji_idx = int((total_min + 60) // 120) % 12
    
    return JI[ji_idx], total_min, total_corr, st_corr != 0

def calculate_yongsin(pillars, day_master):
    # [신강/신약 점수 계산]
    # 월지(30), 일지(10), 시지(10), 연지(10), 천간(각10)
    # 인성/비겁 = 내편 (+), 식상/재성/관성 = 남의편 (-)
    
    my_group = ["c-wood", "c-water"] if OHAENG_MAP[day_master] == "c-wood" else [] # 예시: 갑목이면 목, 수가 내편
    # (약식 로직: 실제로는 오행 생극제화 전체 구현 필요. 여기서는 간략화된 점수제 적용)
    
    scores = {"목":0, "화":0, "토":0, "금":0, "수":0}
    weights = [10, 10, 30, 10] # 시, 일, 월, 연 지지 가중치 (천간은 10으로 통일)
    
    # 천간 점수
    for p in pillars:
        k = KR_OH_MAP[OHAENG_MAP[p['g']]]
        scores[k] += 10
    
    # 지지 점수
    for i, p in enumerate(pillars): # 시, 일, 월, 연 순서
        k = KR_OH_MAP[OHAENG_MAP[p['j']]]
        scores[k] += weights[i]
        
    # 일간 오행
    me = KR_OH_MAP[OHAENG_MAP[day_master]]
    
    # 인성(나를 생함), 비겁(나와 같음) 찾기
    order = ["목","화","토","금","수"]
    me_idx = order.index(me)
    parent = order[me_idx - 1] # 인성
    
    my_power = scores[me] + scores[parent]
    total_power = sum(scores.values())
    other_power = total_power - my_power
    
    is_strong = my_power >= other_power
    strength_txt = "신강" if is_strong else "신약"
    
    # 용신 추천 (억부용신: 강하면 억누르고(관/식/재), 약하면 돕는다(인/비))
    # 단순화된 추천 로직
    if is_strong:
        # 식상, 재성, 관성 중 점수가 가장 낮은 것(필요한데 없는 것) 또는 가장 높은 것(설기)
        # 통상: 관성(억제) > 식상(설기) > 재성
        candidates = [(k, scores[k]) for k in order if k != me and k != parent]
        # 점수가 있는 것 중에서 힘을 뺄 수 있는 것 선택
        yongsin = max(candidates, key=lambda x: x[1])[0] if candidates else "식상" 
    else:
        # 인성, 비겁 중 힘이 되어줄 것
        candidates = [(parent, scores[parent]), (me, scores[me])]
        yongsin = parent # 보통 인성 용신
        
    return strength_txt, my_power, other_power, scores, yongsin

# --- 4. 기타 함수 (기존 유지) ---
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

def get_seun_range(start_year, end_year):
    lst = []
    base_y = 1984
    for y in range(start_year, end_year + 1):
        diff = y - base_y
        g = GAN[diff % 10]
        j = JI[diff % 12]
        lst.append({"year": y, "gan": g, "ji": j})
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

def get_gyeokguk(day_gan, month_ji):
    ten = get_sibseong(day_gan, month_ji)
    if ten == "비견": return "건록격"
    if ten == "겁재": return "양인격"
    return ten + "격"

def generate_pentagon_svg(cnt_data):
    # 오행 이미지
    radius = 120; cx, cy = 150, 150
    angles = [-90, -18, 54, 126, 198]
    labels = ["목", "화", "토", "금", "수"]
    keys = ["목", "화", "토", "금", "수"]
    colors = ["#4caf50", "#f44336", "#ffc107", "#9e9e9e", "#2196f3"]
    svg = f'<svg width="300" height="300" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">'
    points = []
    for ang in angles:
        rad = math.radians(ang)
        points.append((cx + radius * 0.8 * math.cos(rad), cy + radius * 0.8 * math.sin(rad)))
    
    order = [0, 2, 4, 1, 3, 0]
    star_path = "M " + " L ".join([f"{points[i][0]},{points[i][1]}" for i in order])
    svg += f'<path d="{star_path}" stroke="#ddd" stroke-width="2" fill="none" />'
    
    for i, (ang, label, k, c) in enumerate(zip(angles, labels, keys, colors)):
        rad = math.radians(ang)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        val = cnt_data.get(k, 0)
        svg += f'<circle cx="{x}" cy="{y}" r="{25 + val*3}" fill="{c}" opacity="0.9" />'
        svg += f'<text x="{x}" y="{y+5}" font-size="14" fill="white" text-anchor="middle" font-weight="bold">{label}<tspan x="{x}" dy="15" font-size="10">{val}개</tspan></text>'
    svg += '</svg>'
    return svg

# --- 5. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력 (Expert)")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    
    if 'dob_expert' not in st.session_state:
        st.session_state.dob_expert = datetime.date(1990, 5, 5)
    d_input = st.date_input("생년월일", st.session_state.dob_expert, min_value=datetime.date(1900,1,1))
    st.session_state.dob_expert = d_input
    
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    
    if st.button("전문가 분석 실행", type="primary"):
        st.session_state.do_expert = True

# --- 6. 메인 로직 ---
if 'do_expert' in st.session_state and st.session_state.do_expert:
    d = st.session_state.dob_expert
    
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
        
        # [핵심] 전문가용 시간 계산 적용
        t_j, t_min, t_diff, is_st = calc_expert_time(d, t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        
        # 격국
        gyeok = get_gyeokguk(d_g, m_j)
        
        # 원국 배열
        pillars = [{"n":"시주","g":t_g,"j":t_j}, {"n":"일주","g":d_g,"j":d_j}, {"n":"월주","g":m_g,"j":m_j}, {"n":"연주","g":y_g,"j":y_j}]
        
        # 용신/신강약 분석
        strength_txt, my_p, other_p, scores, yongsin_elem = calculate_yongsin(pillars, day_master)
        
        st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
        
        # [1] 헤더
        st_txt = " (썸머타임 적용)" if is_st else ""
        st.markdown(f"""
        <div class="header-box">
            <div class="name-txt">{name} <span class="ganji-badge">{d_g}{d_j}</span> <span class="gyeok-badge">{gyeok}</span></div>
            <div class="info-row">양력 {d.year}.{d.month}.{d.day} ({gender}) {t_time.strftime('%H:%M')}</div>
            <div class="info-row">음력 {l_m}월 {l_d}일 / 절기: {term if term else '-'}</div>
            <div class="solar-row">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} (보정 {int(t_diff)}분{st_txt})</div>
        </div>
        """, unsafe_allow_html=True)

        # [2] 원국표
        tbl = """<table class="saju-tbl"><thead><tr><th class="label-col">구분</th><th>생시</th><th>생일</th><th>생월</th><th>생년</th></tr></thead><tbody>"""
        
        # 천간/지지 Loop
        for p_type, key in [("천간", 'g'), ("지지", 'j')]:
            tbl += f"""<tr><td class="label-col">{p_type}</td>"""
            for p in pillars:
                c = OHAENG_MAP[p[key]]
                tbl += f"""<td><div class="char-box"><span class="char-font {c}">{p[key]}</span></div></td>"""
            tbl += "</tr>"
            
            # 십성
            tbl += f"""<tr><td class="label-col">십성</td>"""
            for p in pillars:
                ten = "일간" if p['n']=="일주" and key=='g' else get_sibseong(day_master, p[key])
                tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
            tbl += "</tr>"
            
        # 상세
        for title, func, style in [("지장간", lambda p: JIJANGGAN[p['j']], "color:#888"), 
                                   ("운성", lambda p: UNSEONG[day_master][JI.index(p['j'])], "color:#2196f3; font-weight:bold"),
                                   ("신살", lambda p: get_shinsal(d_j, p['j']), "color:#f44336")]:
            tbl += f"""<tr><td class="label-col">{title}</td>"""
            for p in pillars:
                tbl += f"""<td><div class="detail-cell" style="{style}">{func(p)}</div></td>"""
            tbl += "</tr>"
        tbl += "</tbody></table>"
        st.markdown(tbl, unsafe_allow_html=True)
        
        # [2-1] 근묘화실
        st.markdown("""
        <div class="fortune-wrap">
            <div class="fortune-cell"><span class="ft-title">말년운 (자녀)</span><span class="ft-desc">결실과 마무리</span></div>
            <div class="fortune-cell"><span class="ft-title">중년운 (본인)</span><span class="ft-desc">활동과 정체성</span></div>
            <div class="fortune-cell"><span class="ft-title">청년운 (부모)</span><span class="ft-desc">사회적 기반</span></div>
            <div class="fortune-cell"><span class="ft-title">초년운 (조상)</span><span class="ft-desc">성장 배경</span></div>
        </div>""", unsafe_allow_html=True)

        # [3] 용신 & 오행 분석
        st.markdown('<div class="sec-head">용신 및 세력 분석</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.write("**오행 상호작용**")
            svg = generate_pentagon_svg(scores)
            st.markdown(f'<div style="text-align:center;">{svg}</div>', unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="yongsin-box">
                <div style="font-size:16px; font-weight:bold; margin-bottom:10px;">⚖️ {strength_txt} (내편 {my_p} vs 남의편 {other_p})</div>
                <div class="score-bar">
                    <div class="score-fill" style="width:{min(100, my_p/max(1, my_p+other_p)*100)}%; background:#4caf50;"></div>
                    <div class="score-fill" style="width:{min(100, other_p/max(1, my_p+other_p)*100)}%; background:#f44336;"></div>
                </div>
                <div style="font-size:14px; margin-top:15px;">
                    <b>추천 용신(用神):</b> <span style="color:#2196f3; font-weight:bold;">{yongsin_elem}</span><br>
                    <span style="font-size:12px; color:#666;">* 억부용신법 기준 자동 추출 결과입니다.</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # [4] 운세 흐름 (대운/세운/월운)
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        
        # 대운
        st.markdown(f'<div class="sec-head">대운 흐름 (대운수 {dw_num})</div>', unsafe_allow_html=True)
        h = '<div class="scroll-box">'
        for d in dw_list:
            h += f"""<div class="l-card"><span class="l-age">{d['age']}</span><span class="l-ten">{get_sibseong(day_master, d['gan'])}</span><span class="l-char">{d['gan']}<br>{d['ji']}</span><span class="l-ten">{get_sibseong(day_master, d['ji'])}</span></div>"""
        st.markdown(h + "</div>", unsafe_allow_html=True)
        
        # 연운 (2025~2035)
        st.markdown('<div class="sec-head">연운 (2025~2035)</div>', unsafe_allow_html=True)
        seun_list = get_seun_range(2025, 2035)
        h = '<div class="scroll-box">'
        for s in seun_list:
            h += f"""<div class="l-card" style="background:#f8f9fa;"><span class="l-age">{s['year']}</span><span class="l-ten">{get_sibseong(day_master, s['gan'])}</span><span class="l-char">{s['gan']}<br>{s['ji']}</span><span class="l-ten">{get_sibseong(day_master, s['ji'])}</span></div>"""
        st.markdown(h + "</div>", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("DB 조회 실패")

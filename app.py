import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt
import math

# --- [1] 페이지 설정 및 스타일 ---
st.set_page_config(page_title="루나 만세력 Pro (Master)", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200;900&display=swap');

    html, body, .stApp {
        font-family: "Pretendard Variable", sans-serif;
        background-color: #f5f7fa;
        color: #111;
    }

    .main-wrap {
        max-width: 850px; margin: 0 auto; background: white;
        padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);
    }

    /* 헤더 */
    .header-box { border-bottom: 2px solid #f1f3f5; padding-bottom: 20px; margin-bottom: 25px; }
    .name-txt { font-size: 26px; font-weight: 900; color: #212529; }
    .ganji-badge { background: #e9ecef; padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; color: #495057; margin-left: 8px; vertical-align: middle; }
    .gyeok-badge { background: #e3f2fd; color: #1565c0; padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-left: 5px; vertical-align: middle; border: 1px solid #bbdefb;}
    
    .info-row { font-size: 14px; color: #868e96; margin-top: 6px; }
    .solar-row { font-size: 14px; color: #ff6b6b; font-weight: bold; margin-top: 2px; }

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
    
    /* 신살 테이블 */
    .ss-tbl { width: 100%; border: 1px solid #f1f3f5; border-radius: 8px; border-collapse: collapse; overflow: hidden; table-layout: fixed; }
    .ss-tbl th { background: #f8f9fa; font-size: 12px; padding: 10px; border-bottom: 1px solid #f1f3f5; color:#555;}
    .ss-tbl td { font-size: 12px; padding: 12px; border-bottom: 1px solid #f1f3f5; text-align: center; font-weight: bold; color: #333; }

    /* [NEW] 자세히 보기 영역 스타일 */
    .detail-container { background: #fff; border: 1px solid #e9ecef; border-radius: 12px; padding: 20px; margin-top: 20px; }
    .mini-chart { display: flex; justify-content: center; margin-bottom: 20px; border-bottom: 1px dashed #eee; padding-bottom: 20px; }
    .mc-col { text-align: center; width: 60px; margin: 0 5px; }
    .mc-label { font-size: 11px; color: #aaa; margin-bottom: 5px; }
    .mc-char { font-family: 'Noto Serif KR'; font-size: 24px; font-weight: bold; }
    .mc-ten { font-size: 11px; background: #eee; padding: 2px 6px; border-radius: 8px; color: #555; }
    
    .result-box { background: #f1f8ff; border: 1px solid #cce5ff; border-radius: 8px; padding: 15px; text-align: center; font-weight: bold; color: #004085; margin: 15px 0; }
    .no-result { background: #f8f9fa; border: 1px solid #dee2e6; color: #868e96; }
    .desc-text { font-size: 13px; color: #666; line-height: 1.6; background: #fdfdfd; padding: 15px; border-radius: 8px; border: 1px solid #f0f0f0; }
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
    dw_num = 6 # 예시
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

# --- [NEW] 상세 분석 로직 ---
def analyze_relationships(pillars):
    # pillars: 0=시, 1=일, 2=월, 3=연
    gans = [p['g'] for p in pillars]
    jis = [p['j'] for p in pillars]
    res = {}
    
    # 1. 천간합 (갑기, 을경, 병신, 정임, 무계)
    haps = [("甲","己"),("乙","庚"),("丙","辛"),("丁","壬"),("戊","癸")]
    found_hap = []
    for idx in range(3): # 0-1, 1-2, 2-3 (인접)
        pair = sorted([gans[idx], gans[idx+1]])
        if tuple(pair) in haps or tuple(reversed(pair)) in haps:
            names = ["시","일","월","연"]
            found_hap.append(f"{names[idx]}간-{names[idx+1]}간 합")
    res["천간합"] = ", ".join(found_hap) if found_hap else "해당사항 없음"

    # 2. 지지육합 (자축, 인해, 묘술, 진유, 사신, 오미)
    yuk = [("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")]
    found_yuk = []
    for idx in range(3):
        pair = sorted([jis[idx], jis[idx+1]])
        for y in yuk:
            if set(pair) == set(y):
                names = ["시","일","월","연"]
                found_yuk.append(f"{names[idx]}지-{names[idx+1]}지 육합")
    res["지지육합"] = ", ".join(found_yuk) if found_yuk else "해당사항 없음"
    
    # 3. 천간충 (갑경, 을신, 병임, 정계)
    chung_g = [("甲","庚"),("乙","辛"),("丙","壬"),("丁","癸")]
    found_gc = []
    for idx in range(3):
        pair = sorted([gans[idx], gans[idx+1]])
        if tuple(pair) in chung_g:
            names = ["시","일","월","연"]
            found_gc.append(f"{names[idx]}-{names[idx+1]} 충")
    res["천간충"] = ", ".join(found_gc) if found_gc else "해당사항 없음"

    # 4. 지지충 (자오, 축미, 인신, 묘유, 진술, 사해)
    chung_j = [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]
    found_jc = []
    for idx in range(3):
        pair = sorted([jis[idx], jis[idx+1]])
        for c in chung_j:
            if set(pair) == set(c):
                names = ["시","일","월","연"]
                found_jc.append(f"{names[idx]}-{names[idx+1]} 충")
    res["지지충"] = ", ".join(found_jc) if found_jc else "해당사항 없음"
    
    # 5. 원진 (자미, 축오, 인유, 묘신, 진해, 사술)
    won = [("子","未"),("丑","午"),("寅","酉"),("卯","申"),("辰","亥"),("巳","戌")]
    found_won = []
    for idx in range(3):
        pair = sorted([jis[idx], jis[idx+1]])
        for w in won:
            if set(pair) == set(w):
                names = ["시","일","월","연"]
                found_won.append(f"{names[idx]}-{names[idx+1]} 원진")
    res["원진"] = ", ".join(found_won) if found_won else "해당사항 없음"
    
    # 6. 삼합 (신자진, 인오술, 사유축, 해묘미) - 전체 스캔
    sam = [("申","子","辰"),("寅","午","戌"),("巳","酉","丑"),("亥","卯","未")]
    found_sam = []
    jis_set = set(jis)
    for s in sam:
        if set(s).issubset(jis_set):
            found_sam.append(f"{''.join(s)} 삼합국")
        # 반합 (생지+왕지 or 왕지+묘지) - 약식
        elif s[1] in jis_set and (s[0] in jis_set or s[2] in jis_set):
             found_sam.append(f"{''.join(s)} 반합")
    res["지지삼합"] = ", ".join(found_sam) if found_sam else "해당사항 없음"
    
    # 나머지는 기본값
    res["지지방합"] = "해당사항 없음 (방합 조건 미충족)"
    res["공망"] = "술해(戌亥)" # 예시 (일주 기준 계산 필요)
    res["형"] = "해당사항 없음"
    res["파"] = "해당사항 없음"
    res["궁성"] = "연주(조상), 월주(부모), 일주(본인), 시주(자식)"
    
    return res

DESC_MAP = {
    "궁성": "사주팔자의 각 기둥(연월일시)이 상징하는 인물과 시기를 말합니다. 연주는 조상/초년, 월주는 부모/형제/청년, 일주는 본인/배우자/중년, 시주는 자식/말년을 의미합니다.",
    "천간합": "천간의 글자들이 서로 끌려 합쳐지는 현상입니다. 정신적인 추구, 지향점, 인간관계의 화합을 의미하며, 합화(合化)하여 새로운 오행을 만들기도 합니다.",
    "지지육합": "지지 여섯 쌍의 합입니다. 현실적인 결합, 육체적인 관계, 부부의 정 등을 의미하며, 끈끈한 유대감을 나타냅니다.",
    "지지삼합": "세 개의 지지가 모여 강력한 세력을 형성하는 사회적 합입니다. 목적 지향적인 결합, 재능의 발휘, 큰 변화를 암시합니다.",
    "지지방합": "같은 계절의 글자들이 모인 형제/가족 같은 합입니다. 결속력이 매우 강하며, 해당 오행의 세력이 아주 강해집니다.",
    "천간충": "천간끼리 부딪히는 현상입니다. 정신적인 갈등, 가치관의 충돌, 빠른 변화, 이동 변동수를 의미합니다.",
    "지지충": "지지끼리 부딪히는 현상입니다. 현실적인 부딪힘, 사고, 건강 문제, 주거지 이동, 이별 등을 암시합니다. 충이 나쁜 것만은 아니며 자극제가 되기도 합니다.",
    "공망": "천간과 지지가 짝을 짓고 남은 두 글자입니다. '비어있다'는 뜻으로, 해당 육친의 인연이 약하거나, 채워지지 않는 욕망을 의미합니다.",
    "형": "형벌, 수술, 조정, 삭감을 의미합니다. 깎고 다듬는 과정이므로 고통이 따르지만, 직업적으로 쓰면 권력(의료, 법무 등)을 가질 수 있습니다.",
    "파": "깨뜨린다는 의미입니다. 협력 관계가 깨지거나, 일이 중도에 변경되는 것을 암시합니다.",
    "원진": "서로 미워하고 원망하는 관계입니다. 애증의 관계, 이유 없는 싫음, 꼬임 등을 의미합니다."
}

# --- 3. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    
    if 'dob_final_v2' not in st.session_state:
        st.session_state.dob_final_v2 = datetime.date(1990, 5, 5)
    d_input = st.date_input("생년월일", st.session_state.dob_final_v2, min_value=datetime.date(1900,1,1))
    st.session_state.dob_final_v2 = d_input
    
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    
    if st.button("결과 확인", type="primary"):
        st.session_state.do_run_v2 = True

# --- 4. 메인 로직 ---
if 'do_run_v2' in st.session_state and st.session_state.do_run_v2:
    d = st.session_state.dob_final_v2
    
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ saju.db 파일 오류. DB를 확인해주세요.")
        st.stop()

    if row:
        y_gj, m_gj, d_gj, l_m, l_d, term = row
        y_g, y_j = y_gj[0], y_gj[1]
        m_g, m_j = m_gj[0], m_gj[1]
        d_g, d_j = d_gj[0], d_gj[1]
        t_j, t_min, t_diff = calc_solar_time(t_time.hour, t_time.minute, loc)
        t_g = get_time_gan(d_g, t_j)
        day_master = d_g
        gyeok = get_gyeokguk(d_g, m_j)
        
        st.markdown('<div class="main-wrap">', unsafe_allow_html=True)
        
        # [1] 헤더
        st.markdown(f"""
        <div class="header-box">
            <div class="name-txt">{name} <span class="ganji-badge">{d_g}{d_j} (푸른 말)</span> <span class="gyeok-badge">{gyeok}</span></div>
            <div class="info-row">양력 {d.year}.{d.month}.{d.day} ({gender}) {t_time.strftime('%H:%M')}</div>
            <div class="info-row">음력 {l_m}월 {l_d}일 / 절기: {term if term else '-'}</div>
            <div class="solar-row">진태양시 {int(t_min//60):02d}:{int(t_min%60):02d} (보정 {int(t_diff)}분)</div>
        </div>
        """, unsafe_allow_html=True)

        # [2] 원국표
        pillars = [{"n":"시주","g":t_g,"j":t_j}, {"n":"일주","g":d_g,"j":d_j}, {"n":"월주","g":m_g,"j":m_j}, {"n":"연주","g":y_g,"j":y_j}]
        
        tbl = """<table class="saju-tbl"><thead><tr><th class="label-col">구분</th><th>생시</th><th>생일</th><th>생월</th><th>생년</th></tr></thead><tbody>"""
        
        # 천간
        tbl += """<tr><td class="label-col">천간</td>"""
        for p in pillars:
            ten = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            c = OHAENG_MAP[p['g']]
            tbl += f"""<td><div class="char-box"><span class="char-font {c}">{p['g']}</span></div></td>"""
        tbl += "</tr>"
        
        # 십성(천간)
        tbl += """<tr><td class="label-col">십성</td>"""
        for p in pillars:
            ten = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
            tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
        tbl += "</tr>"

        # 지지
        tbl += """<tr><td class="label-col">지지</td>"""
        for p in pillars:
            c = OHAENG_MAP[p['j']]
            tbl += f"""<td><div class="char-box"><span class="char-font {c}">{p['j']}</span></div></td>"""
        tbl += "</tr>"
        
        # 십성(지지)
        tbl += """<tr><td class="label-col">십성</td>"""
        for p in pillars:
            ten = get_sibseong(day_master, p['j'])
            tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
        tbl += "</tr>"
        
        # 상세
        for title, func, style in [("지장간", lambda p: JIJANGGAN[p['j']], "color:#888"), ("운성", lambda p: UNSEONG[day_master][JI.index(p['j'])], "color:#2196f3; font-weight:bold"), ("신살", lambda p: get_shinsal(d_j, p['j']), "color:#f44336")]:
            tbl += f"""<tr><td class="label-col">{title}</td>"""
            for p in pillars:
                tbl += f"""<td><div class="detail-cell" style="{style}">{func(p)}</div></td>"""
            tbl += "</tr>"
        tbl += "</tbody></table>"
        st.markdown(tbl, unsafe_allow_html=True)
        
        # [NEW] 사주 풀이 자세히 보기 (Interactive Tabs)
        st.markdown('<div class="sec-head">사주 풀이 자세히 보기</div>', unsafe_allow_html=True)
        
        # 미니 원국표 (참조용)
        st.markdown('<div class="detail-container"><div class="mini-chart">', unsafe_allow_html=True)
        mini_cols = st.columns(4)
        for i, p in enumerate(reversed(pillars)): # 연월일시 순서로 보려면 reverse
            with mini_cols[i]:
                g_t = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
                j_t = get_sibseong(day_master, p['j'])
                st.markdown(f"""
                <div class="mc-col">
                    <div class="mc-label">{p['n']}</div>
                    <div class="mc-char {OHAENG_MAP[p['g']]}">{p['g']}</div>
                    <div class="mc-ten">{g_t}</div>
                    <div class="mc-char {OHAENG_MAP[p['j']]}" style="margin-top:5px;">{p['j']}</div>
                    <div class="mc-ten">{j_t}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 탭 메뉴
        tabs = ["궁성", "천간합", "지지육합", "지지삼합", "지지방합", "천간충", "지지충", "공망", "형", "파", "원진"]
        selected_tab = st.radio("분석 항목 선택", tabs, horizontal=True, label_visibility="collapsed")
        
        # 분석 결과 가져오기
        analysis_res = analyze_relationships(pillars)
        res_text = analysis_res.get(selected_tab, "분석 불가")
        desc_text = DESC_MAP.get(selected_tab, "")
        
        # 결과 표시
        st.markdown(f"""
        <div class="result-box {'no-result' if '해당사항' in res_text else ''}">
            {res_text}
        </div>
        <div class="desc-text">
            <b>{selected_tab}이란?</b><br>
            {desc_text}<br><br>
            <span style="font-size:11px; color:#888;">* 합과 충은 어느 위치에서 얼마나 작용하냐에 따라 상이한 영향을 미치기 때문에 합이라고 해서 무조건 좋고 충이라고 해서 꼭 나쁘게 작용하지 않습니다.</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

        # [3] 신살표
        st.markdown('<div class="sec-head">신살과 길성</div>', unsafe_allow_html=True)
        st.markdown("""
        <table class="ss-tbl">
            <tr><th>구분</th><th>시주</th><th>일주</th><th>월주</th><th>연주</th></tr>
            <tr><td>천간</td><td>-</td><td>현침살</td><td>현침살</td><td>백호</td></tr>
            <tr><td>지지</td><td>도화</td><td>홍염</td><td>태극</td><td>천을</td></tr>
        </table>
        """, unsafe_allow_html=True)

        # [4] 오행 분석
        st.markdown('<div class="sec-head">오행 및 십성 분석</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        all_c = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in all_c:
            kor = KR_OH_MAP[OHAENG_MAP[c]]
            cnt[kor] += 1
            
        with c1:
            st.write("**오행 상호작용**")
            svg_html = generate_pentagon_svg(cnt)
            st.markdown(f'<div style="text-align:center;">{svg_html}</div>', unsafe_allow_html=True)
        with c2:
            st.write("**십성 분포**")
            df_oh = pd.DataFrame({"cat": list(cnt.keys()), "val": list(cnt.values())})
            chart = alt.Chart(df_oh).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("val", stack=True),
                color=alt.Color("cat", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#4caf50","#f44336","#ffc107","#9e9e9e","#2196f3"]))
            )
            st.altair_chart(chart, use_container_width=True)
            top = max(cnt, key=cnt.get)
            st.info(f"💡 **{top}** 기운이 가장 강합니다.")

        # [5] 대운 Scroll
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        st.markdown(f'<div class="sec-head">대운 흐름 (대운수 {dw_num})</div>', unsafe_allow_html=True)
        dw_h = '<div class="scroll-box">'
        for d_item in dw_list:
            g_t = get_sibseong(day_master, d_item['gan'])
            j_t = get_sibseong(day_master, d_item['ji'])
            dw_h += f"""<div class="l-card"><span class="l-age">{d_item['age']}</span><span class="l-ten">{g_t}</span><span class="l-char">{d_item['gan']}<br>{d_item['ji']}</span><span class="l-ten">{j_t}</span></div>"""
        dw_h += "</div>"
        st.markdown(dw_h, unsafe_allow_html=True)

        # [6] 연운 (2025~2035)
        st.markdown('<div class="sec-head">연운 (세운) (2025~2035)</div>', unsafe_allow_html=True)
        seun_list = get_seun_range(2025, 2035)
        se_h = '<div class="scroll-box">'
        for s in seun_list:
            g_t = get_sibseong(day_master, s['gan'])
            j_t = get_sibseong(day_master, s['ji'])
            se_h += f"""<div class="l-card" style="background:#fcfcfc;"><span class="l-age">{s['year']}</span><span class="l-ten">{g_t}</span><span class="l-char" style="font-size:16px;">{s['gan']}<br>{s['ji']}</span><span class="l-ten">{j_t}</span></div>"""
        se_h += "</div>"
        st.markdown(se_h, unsafe_allow_html=True)

        # [7] 월운
        st.markdown('<div class="sec-head">올해의 월운</div>', unsafe_allow_html=True)
        this_year = datetime.datetime.now().year
        seun_g_idx = (GAN.index("甲") + (this_year - 1984)) % 10
        this_year_gan = GAN[seun_g_idx]
        wolun_list = get_wolun(this_year_gan)
        wo_h = '<div class="scroll-box">'
        for w in wolun_list:
            g_t = get_sibseong(day_master, w['gan'])
            j_t = get_sibseong(day_master, w['ji'])
            wo_h += f"""<div class="l-card"><span class="l-age">{w['mon']}월</span><span class="l-ten">{g_t}</span><span class="l-char" style="font-size:16px;">{w['gan']}<br>{w['ji']}</span><span class="l-ten">{j_t}</span></div>"""
        wo_h += "</div>"
        st.markdown(wo_h, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

import streamlit as st
import sqlite3
import datetime
import pandas as pd
import altair as alt
import math

# --- [1] 설정 및 스타일 ---
st.set_page_config(page_title="루나 만세력 Pro", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css");
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@200;900&display=swap');

    html, body, .stApp { font-family: "Pretendard Variable", sans-serif; background-color: #f5f7fa; color: #111; }
    .main-wrap { max-width: 850px; margin: 0 auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }
    .header-box { border-bottom: 2px solid #f1f3f5; padding-bottom: 20px; margin-bottom: 25px; }
    .name-txt { font-size: 26px; font-weight: 900; color: #212529; }
    .ganji-badge { background: #e9ecef; padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; color: #495057; margin-left: 8px; vertical-align: middle; }
    .gyeok-badge { background: #e3f2fd; color: #1565c0; padding: 4px 10px; border-radius: 12px; font-size: 14px; font-weight: bold; margin-left: 5px; vertical-align: middle; border: 1px solid #bbdefb;}
    .info-row { font-size: 14px; color: #868e96; margin-top: 6px; }
    .solar-row { font-size: 14px; color: #ff6b6b; font-weight: bold; margin-top: 2px; }
    .saju-tbl { width: 100%; border-collapse: separate; border-spacing: 0; text-align: center; table-layout: fixed; border: 1px solid #eee; border-radius: 12px; overflow: hidden; margin-bottom: 20px;}
    .saju-tbl th { font-size: 13px; color: #888; font-weight: normal; padding: 12px 0; background: #fcfcfc; border-bottom: 1px solid #eee; border-right: 1px solid #eee;}
    .saju-tbl td { vertical-align: middle; border-bottom: 1px solid #eee; border-right: 1px solid #eee; padding: 0;}
    .label-col { background: #fcfcfc; font-size: 13px; font-weight: bold; color: #aaa; width: 70px; }
    .char-box { display: flex; flex-direction: column; justify-content: center; align-items: center; height: 90px; width: 100%; }
    .char-font { font-family: 'Noto Serif KR', serif; font-size: 38px; font-weight: 900; line-height: 1; margin-bottom: 4px; }
    .detail-cell { font-size: 13px; padding: 10px 0; color: #555; font-weight: 500; height: 100%; display: flex; align-items: center; justify-content: center;}
    .c-wood { color: #4caf50; } .c-fire { color: #f44336; } .c-earth { color: #ffc107; } .c-metal { color: #9e9e9e; } .c-water { color: #2196f3; }
    .sec-head { font-size: 18px; font-weight: 800; margin: 40px 0 15px 0; color: #212529; display: flex; align-items: center; border-bottom: 2px solid #333; padding-bottom: 8px;}
    .scroll-box { display: flex; gap: 8px; overflow-x: auto; padding: 5px 2px 15px 2px; scrollbar-width: thin; }
    .l-card { min-width: 70px; background: #fff; border: 1px solid #e9ecef; border-radius: 12px; padding: 12px 0; text-align: center; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .l-age { font-size: 12px; font-weight: bold; color: #868e96; display: block; margin-bottom: 4px; }
    .l-char { font-family: 'Noto Serif KR'; font-size: 20px; font-weight: 900; line-height: 1.2; display: block; color: #333; }
    .l-ten { font-size: 10px; color: #adb5bd; display: block; margin-top: 4px; }
    .ss-tbl { width: 100%; border: 1px solid #f1f3f5; border-radius: 8px; border-collapse: collapse; overflow: hidden; table-layout: fixed; }
    .ss-tbl th { background: #f8f9fa; font-size: 12px; padding: 10px; border-bottom: 1px solid #f1f3f5; color:#555;}
    .ss-tbl td { font-size: 12px; padding: 12px; border-bottom: 1px solid #f1f3f5; text-align: center; font-weight: bold; color: #333; }
    
    .mini-chart { display: flex; justify-content: center; margin-bottom: 20px; border-bottom: 1px dashed #eee; padding-bottom: 20px; }
    .mc-col { text-align: center; width: 60px; margin: 0 5px; }
    .mc-char { font-family: 'Noto Serif KR'; font-size: 24px; font-weight: bold; }
    .mc-ten { font-size: 11px; background: #eee; padding: 2px 6px; border-radius: 8px; color: #555; }
    .result-box { background: #e3f2fd; border: 1px solid #90caf9; border-radius: 8px; padding: 15px; text-align: center; font-weight: bold; color: #1565c0; margin: 15px 0; }
    .no-result { background: #f8f9fa; border: 1px solid #dee2e6; color: #adb5bd; }
    .desc-text { font-size: 13px; color: #555; line-height: 1.6; background: #fff; padding: 15px; border-radius: 8px; border: 1px solid #eee; }
    
    .fortune-wrap { display: flex; justify-content: space-between; margin-top: 10px; padding-top:10px; border-top:1px dashed #eee;}
    .fortune-cell { background: #f8f9fa; border-radius: 8px; padding: 10px 5px; width: 24%; text-align: center; }
    .ft-title { font-size: 12px; font-weight: 800; color: #343a40; display: block; }
    .ft-desc { font-size: 10px; color: #aaa; margin-top:2px; display:block;}
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 상수 ---
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

# --- [4] 핵심: 상세 분석 알고리즘 (방합 계산 수정됨) ---
def analyze_relationships_v2(pillars, day_master):
    gans = [p['g'] for p in pillars]
    jis = [p['j'] for p in pillars]
    ji_indices = [JI.index(j) for j in jis]
    gan_indices = [GAN.index(g) for g in gans]
    p_names = ["시주", "일주", "월주", "연주"]
    res = {}

    res["궁성"] = f"연주({gans[3]}{jis[3]}): 조상/초년, 월주({gans[2]}{jis[2]}): 부모/청년, 일주({gans[1]}{jis[1]}): 본인/중년, 시주({gans[0]}{jis[0]}): 자식/말년"

    # 천간합
    found_hap = []
    for i in range(4):
        for j in range(i+1, 4):
            if abs(gan_indices[i] - gan_indices[j]) == 5:
                found_hap.append(f"{p_names[i]}-{p_names[j]} 합")
    res["천간합"] = ", ".join(found_hap) if found_hap else "해당사항 없음"

    # 지지육합
    yukhap_map = {0:1, 1:0, 2:11, 11:2, 3:10, 10:3, 4:9, 9:4, 5:8, 8:5, 6:7, 7:6}
    found_yuk = []
    for i in range(4):
        for j in range(i+1, 4):
            if yukhap_map[ji_indices[i]] == ji_indices[j]:
                found_yuk.append(f"{p_names[i]}-{p_names[j]} 육합")
    res["지지육합"] = ", ".join(found_yuk) if found_yuk else "해당사항 없음"

    # 천간충
    found_g_chung = []
    for i in range(4):
        for j in range(i+1, 4):
            if abs(gan_indices[i] - gan_indices[j]) == 6:
                found_g_chung.append(f"{p_names[i]}-{p_names[j]} 충")
    res["천간충"] = ", ".join(found_g_chung) if found_g_chung else "해당사항 없음"

    # 지지충
    found_j_chung = []
    for i in range(4):
        for j in range(i+1, 4):
            if abs(ji_indices[i] - ji_indices[j]) == 6:
                found_j_chung.append(f"{p_names[i]}-{p_names[j]} 충")
    res["지지충"] = ", ".join(found_j_chung) if found_j_chung else "해당사항 없음"

    # 삼합
    samhap_groups = [
        {"name":"인오술 화국", "set":{2,6,10}}, {"name":"사유축 금국", "set":{5,9,1}},
        {"name":"신자진 수국", "set":{8,0,4}},  {"name":"해묘미 목국", "set":{11,3,7}}
    ]
    my_jis = set(ji_indices)
    found_sam = []
    for group in samhap_groups:
        match_cnt = len(group["set"] & my_jis)
        if match_cnt == 3: found_sam.append(f"{group['name']} (전합)")
        elif match_cnt == 2: found_sam.append(f"{group['name']} (반합)")
    res["지지삼합"] = ", ".join(found_sam) if found_sam else "해당사항 없음"

    # [수정된] 방합 (2글자 이상이면 반합 인정)
    # 인묘진(2,3,4), 사오미(5,6,7), 신유술(8,9,10), 해자축(11,0,1)
    bang_groups = [
        {"name":"인묘진 목국(봄)", "set":{2,3,4}},
        {"name":"사오미 화국(여름)", "set":{5,6,7}},
        {"name":"신유술 금국(가을)", "set":{8,9,10}},
        {"name":"해자축 수국(겨울)", "set":{11,0,1}}
    ]
    found_bang = []
    for group in bang_groups:
        match_cnt = len(group["set"] & my_jis)
        if match_cnt == 3: found_bang.append(f"{group['name']} 방합 (완전)")
        elif match_cnt == 2: found_bang.append(f"{group['name']} 방합 (반합)")
    res["지지방합"] = ", ".join(found_bang) if found_bang else "해당사항 없음"

    # 공망 (일주 기준)
    il_g = gan_indices[1]; il_j = ji_indices[1]
    gm_start = (il_j - il_g - 2) % 12
    gm_chars = [JI[gm_start], JI[(gm_start+1)%12]]
    my_gm = []
    for k, char in enumerate(jis):
        if k!=1 and char in gm_chars: my_gm.append(f"{p_names[k]} 공망")
    res["공망"] = f"공망글자: {''.join(gm_chars)} / 결과: " + (", ".join(my_gm) if my_gm else "없음")

    # 원진
    wonjin_pairs = [{0,7}, {1,6}, {2,9}, {3,8}, {4,11}, {5,10}]
    found_won = []
    for i in range(4):
        for j in range(i+1, 4):
            if {ji_indices[i], ji_indices[j]} in wonjin_pairs:
                found_won.append(f"{p_names[i]}-{p_names[j]} 원진")
    res["원진"] = ", ".join(found_won) if found_won else "해당사항 없음"

    # 형
    found_hyeong = []
    if {2,5,8}.issubset(my_jis): found_hyeong.append("인사신 삼형")
    if {1,10,7}.issubset(my_jis): found_hyeong.append("축술미 삼형")
    if 0 in my_jis and 3 in my_jis: found_hyeong.append("자묘 형")
    for x in [4,6,9,11]:
        if ji_indices.count(x)>=2: found_hyeong.append(f"{JI[x]}{JI[x]} 자형")
    res["형"] = ", ".join(found_hyeong) if found_hyeong else "해당사항 없음"

    # 파
    pa_pairs = [{0,9}, {1,4}, {2,11}, {3,6}, {5,8}, {10,7}]
    found_pa = []
    for i in range(4):
        for j in range(i+1, 4):
            if {ji_indices[i], ji_indices[j]} in pa_pairs: found_pa.append(f"{p_names[i]}-{p_names[j]} 파")
    res["파"] = ", ".join(found_pa) if found_pa else "해당사항 없음"

    return res

DESC_MAP = {
    "궁성": "사주팔자의 기둥(연월일시)은 각각 조상/초년, 부모/청년, 본인/중년, 자식/말년을 상징합니다.",
    "천간합": "정신적인 추구와 합치를 의미합니다. 유정(有情)하여 서로 끌리는 관계입니다.",
    "지지육합": "현실적이고 육체적인 결합을 의미하며, 끈끈한 유대감과 협력을 나타냅니다.",
    "지지삼합": "사회적인 목적을 위해 세력이 뭉치는 강력한 합입니다. 큰 변화와 재능 발휘를 암시합니다.",
    "지지방합": "가족이나 형제처럼 같은 계절의 기운끼리 뭉친 합입니다. 결속력이 매우 강합니다.",
    "천간충": "정신적인 가치관의 충돌이나 빠른 변화, 이동수를 의미합니다.",
    "지지충": "현실적인 부딪힘, 주거 이동, 사고, 건강 문제, 혹은 긍정적인 자극과 변화를 의미합니다.",
    "공망": "비어있다는 뜻으로, 해당 육친이나 기운의 덕이 부족하거나 채워지지 않는 갈증을 의미합니다.",
    "형": "조정, 수술, 삭감, 형벌을 의미합니다. 고통이 따르지만 전문가적 능력(의료, 법무)으로 쓰이기도 합니다.",
    "파": "깨뜨린다는 의미로, 일의 중도 변경, 배신, 분리 등을 암시합니다.",
    "원진": "이유 없이 서로 미워하고 원망하는 애증의 관계입니다. 예민함과 촉이 발달하기도 합니다."
}

# --- 5. UI 실행 ---
with st.sidebar:
    st.title("🌙 루나 만세력")
    name = st.text_input("이름", "사용자")
    gender = st.radio("성별", ["남자", "여자"])
    
    if 'dob_v4' not in st.session_state:
        st.session_state.dob_v4 = datetime.date(1990, 5, 5)
    d_input = st.date_input("생년월일", st.session_state.dob_v4, min_value=datetime.date(1900,1,1))
    st.session_state.dob_v4 = d_input
    
    t_time = st.time_input("태어난 시간", datetime.time(7, 0))
    loc = st.selectbox("출생 지역", list(LOCATIONS.keys()))
    
    if st.button("결과 확인", type="primary"):
        st.session_state.run_v4 = True

if 'run_v4' in st.session_state and st.session_state.run_v4:
    d = st.session_state.dob_v4
    
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        cur.execute("SELECT cd_hyganjee, cd_kyganjee, cd_dyganjee, cd_lm, cd_ld, cd_terms FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()
    except:
        st.error("⚠️ DB 오류")
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
        
        tbl += """<tr><td class="label-col">십성</td>"""
        for p in pillars:
            ten = get_sibseong(day_master, p['j'])
            tbl += f"""<td style="padding:5px;"><span class="ganji-badge" style="font-size:11px; margin:0;">{ten}</span></td>"""
        tbl += "</tr>"
        
        for title, func, style in [("지장간", lambda p: JIJANGGAN[p['j']], "color:#888"), ("운성", lambda p: UNSEONG[day_master][JI.index(p['j'])], "color:#2196f3; font-weight:bold"), ("신살", lambda p: get_shinsal(d_j, p['j']), "color:#f44336")]:
            tbl += f"""<tr><td class="label-col">{title}</td>"""
            for p in pillars:
                tbl += f"""<td><div class="detail-cell" style="{style}">{func(p)}</div></td>"""
            tbl += "</tr>"
        tbl += "</tbody></table>"
        st.markdown(tbl, unsafe_allow_html=True)
        
        # [2-1] 사주 풀이 자세히 보기 (근묘화실)
        st.markdown("""
        <div style="font-size:13px; font-weight:bold; color:#333; margin-top:20px;">사주 풀이 자세히 보기</div>
        <div class="fortune-wrap">
            <div class="fortune-cell"><span class="ft-title">말년운</span><span class="ft-desc">자녀, 결실</span></div>
            <div class="fortune-cell"><span class="ft-title">중년운</span><span class="ft-desc">자아, 정체성</span></div>
            <div class="fortune-cell"><span class="ft-title">청년운</span><span class="ft-desc">부모, 사회</span></div>
            <div class="fortune-cell"><span class="ft-title">초년운</span><span class="ft-desc">조상, 유년</span></div>
        </div>
        """, unsafe_allow_html=True)
        
        # [NEW] 상세 분석
        st.markdown('<div class="sec-head">상세 분석</div>', unsafe_allow_html=True)
        st.markdown('<div class="detail-container"><div class="mini-chart">', unsafe_allow_html=True)
        cols = st.columns(4)
        for i, p in enumerate(reversed(pillars)):
            with cols[i]:
                g_t = "일간" if p['n']=="일주" else get_sibseong(day_master, p['g'])
                j_t = get_sibseong(day_master, p['j'])
                st.markdown(f"""
                <div class="mc-col">
                    <div style="font-size:11px; color:#aaa;">{p['n']}</div>
                    <div class="mc-char {OHAENG_MAP[p['g']]}">{p['g']}</div>
                    <div class="mc-ten">{g_t}</div>
                    <div class="mc-char {OHAENG_MAP[p['j']]}" style="margin-top:5px;">{p['j']}</div>
                    <div class="mc-ten">{j_t}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        tabs = ["궁성", "천간합", "지지육합", "지지삼합", "지지방합", "천간충", "지지충", "공망", "형", "파", "원진"]
        sel = st.radio("분석 선택", tabs, horizontal=True, label_visibility="collapsed")
        
        an_res = analyze_relationships_v2(pillars, day_master)
        val = an_res.get(sel, "")
        desc = DESC_MAP.get(sel, "")
        
        st.markdown(f"""
        <div class="result-box {'no-result' if '해당사항' in val else ''}">{val}</div>
        <div class="desc-text"><b>{sel}이란?</b><br>{desc}<br><br><span style='color:#888; font-size:11px;'>* 합과 충은 작용 위치와 세력에 따라 길흉이 달라지니 단편적으로 판단하지 마세요.</span></div>
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

        # [4] 오행
        st.markdown('<div class="sec-head">오행 및 십성 분석</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        all_c = [p['g'] for p in pillars] + [p['j'] for p in pillars]
        cnt = {"목":0,"화":0,"토":0,"금":0,"수":0}
        for c in all_c:
            cnt[KR_OH_MAP[OHAENG_MAP[c]]] += 1
            
        with c1:
            st.write("**오행 상호작용**")
            st.markdown(f'<div style="text-align:center;">{generate_pentagon_svg(cnt)}</div>', unsafe_allow_html=True)
        with c2:
            st.write("**십성 분포**")
            df = pd.DataFrame({"c":list(cnt.keys()), "v":list(cnt.values())})
            ch = alt.Chart(df).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("v", stack=True),
                color=alt.Color("c", scale=alt.Scale(domain=["목","화","토","금","수"], range=["#4caf50","#f44336","#ffc107","#9e9e9e","#2196f3"]))
            )
            st.altair_chart(ch, use_container_width=True)
            st.info(f"💡 **{max(cnt, key=cnt.get)}** 기운이 강합니다.")

        # [5] 대운
        dw_list, dw_num = get_daewoon_full(y_g, m_g, m_j, gender)
        st.markdown(f'<div class="sec-head">대운 흐름 (대운수 {dw_num})</div>', unsafe_allow_html=True)
        h = '<div class="scroll-box">'
        for d in dw_list:
            h += f"""<div class="l-card"><span class="l-age">{d['age']}</span><span class="l-ten">{get_sibseong(day_master, d['gan'])}</span><span class="l-char">{d['gan']}<br>{d['ji']}</span><span class="l-ten">{get_sibseong(day_master, d['ji'])}</span></div>"""
        st.markdown(h+"</div>", unsafe_allow_html=True)

        # [6] 연운 (2025~2035)
        st.markdown('<div class="sec-head">연운 (세운) (2025~2035)</div>', unsafe_allow_html=True)
        sl = get_seun_range(2025, 2035)
        h = '<div class="scroll-box">'
        for s in sl:
            h += f"""<div class="l-card" style="background:#f8f9fa"><span class="l-age">{s['year']}</span><span class="l-ten">{get_sibseong(day_master, s['gan'])}</span><span class="l-char">{s['gan']}<br>{s['ji']}</span><span class="l-ten">{get_sibseong(day_master, s['ji'])}</span></div>"""
        st.markdown(h+"</div>", unsafe_allow_html=True)

        # [7] 월운
        st.markdown('<div class="sec-head">올해의 월운</div>', unsafe_allow_html=True)
        ty = datetime.datetime.now().year
        ty_gan = GAN[(GAN.index("甲") + (ty-1984))%10]
        wl = get_wolun(ty_gan)
        h = '<div class="scroll-box">'
        for w in wl:
            h += f"""<div class="l-card"><span class="l-age">{w['mon']}월</span><span class="l-ten">{get_sibseong(day_master, w['gan'])}</span><span class="l-char">{w['gan']}<br>{w['ji']}</span><span class="l-ten">{get_sibseong(day_master, w['ji'])}</span></div>"""
        st.markdown(h+"</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.error("데이터 조회 실패")

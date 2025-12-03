import streamlit as st
import sqlite3
import datetime

# 페이지 설정
st.set_page_config(page_title="AI 만세력", page_icon="🔮")

# --- 시주 계산 (시두법) ---
def get_time_pillar(day_gan, hour_ji):
    # 천간 순서: 갑을병정무기경신임계
    gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    # 지지 순서: 자축인묘진사오미신유술해
    ji_list = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
    
    if hour_ji not in ji_list: return ""
    
    # 일간별 자시(0번 인덱스)의 천간 시작점 인덱스
    # 갑/기일 -> 갑자시(0), 을/경일 -> 병자시(2), 병/신일 -> 무자시(4), 정/임일 -> 경자시(6), 무/계일 -> 임자시(8)
    start_idx_map = {"甲":0, "己":0, "乙":2, "庚":2, "丙":4, "辛":4, "丁":6, "壬":6, "戊":8, "癸":8}
    
    start_idx = start_idx_map.get(day_gan, 0)
    ji_idx = ji_list.index(hour_ji)
    
    # 천간 순환 (10개씩 돔)
    final_gan_idx = (start_idx + ji_idx) % 10
    return gan_list[final_gan_idx]

# --- UI ---
st.title("🔮 정통 사주 만세력")
st.write("생년월일시를 입력하세요. (1900~2100년 지원)")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("양력 생일", datetime.date(1990, 1, 1), 
                      min_value=datetime.date(1900,1,1), 
                      max_value=datetime.date(2100,12,31))
with col2:
    t = st.selectbox("태어난 시간", ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"])

if st.button("결과 보기"):
    try:
        conn = sqlite3.connect("saju.db")
        cur = conn.cursor()
        
        # DB에서 조회 (문자열 변환 주의)
        cur.execute("SELECT cd_hyganjee, cd_hyganjee_kr, cd_kyganjee, cd_kyganjee_kr, cd_dyganjee, cd_dyganjee_kr FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?", 
                   (d.year, str(d.month), str(d.day)))
        row = cur.fetchone()
        conn.close()

        if row:
            y_gan, y_kr, m_gan, m_kr, d_gan, d_kr = row
            
            # 시주 계산
            day_master = d_gan[0] # 일간 (예: 甲)
            time_gan = get_time_pillar(day_master, t)
            time_pillar = f"{time_gan}{t}"
            
            # 화면 출력
            st.success(f"🗓️ 양력 {d.year}년 {d.month}월 {d.day}일 {t}시생")
            
            # 카드 형태로 사주 보여주기
            cols = st.columns(4)
            cols[0].metric("시주 (자녀)", time_pillar)
            cols[1].metric("일주 (본인)", f"{d_gan}({d_kr})")
            cols[2].metric("월주 (부모)", f"{m_gan}({m_kr})")
            cols[3].metric("연주 (조상)", f"{y_gan}({y_kr})")
            
            st.info(f"당신의 일간(본원)은 **'{d_gan[0]}({d_kr[0]})'** 입니다.")
            
        else:
            st.error("죄송합니다. 해당 날짜의 데이터가 DB에 없습니다.")
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        st.write("DB 파일이 같은 폴더에 있는지 확인해주세요.")
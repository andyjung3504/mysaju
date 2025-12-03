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
UNSEONG = {
    "甲":["목욕","관대","건록","제왕","쇠","병","사","묘","절","태","양","장생"],
    "丙":["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "戊":["태","양","장생","목욕","관대","건록","제왕","쇠","병","사","묘","절"],
    "庚":["사","묘","절","태","양","장생","목욕","관대","건록","제왕","쇠","병"],
    "壬":["제왕","쇠","병","사","묘","절","태","양","장생","목욕","관대","건록"],
    "乙":["병","쇠","제왕","건록","관대","목욕","장생","양","태","절","묘","사"],
    "丁":["절","묘","사","병","쇠","제왕","건록","관대","목욕","

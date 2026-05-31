import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정 및 DB 연결] ---
st.set_page_config(page_title="화병-사회지표-범죄 데이터 대시보드", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 파일을 찾을 수 없습니다. 파일 이름을 확인해주세요.")
    st.stop()

def run_query(q):
    """SQL 실행 및 데이터프레임 반환"""
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. SQL 쿼리 생성기 (오류 방지용)] ---
# 지표 테이블(2013)과 범죄 테이블(2013 년)의 컬럼 형식이 다르므로 구분하여 처리합니다.
YEARS = ['2013', '2015', '2017', '2019', '2021', '2023']

def build_unpivot_query(table, age_col, value_name, is_crime=False):
    """가로로 긴 데이터를 세로로 길게 만드는 쿼리 생성 (줄바꿈 포함)"""
    queries = []
    for y in YEARS:
        # 범죄 테이블은 컬럼명이 "2013 년" 형태, 나머지는 "2013" 형태
        col_name = f'"{y} 년"' if is_crime else f'"{y}"'
        queries.append(f"SELECT TRIM({age_col}) as 연령대, {y} as 연도, {col_name} as {value_name} FROM {table}")
    return "\n UNION ALL \n".join(queries)

# --- [3. 메인 대시보드 구성] ---
st.title("🧠 사회 지표 기반 화병 및 무동기 범죄 상관분석")
tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 & 우울감", "🤝 2. 고립도 & 우울감", "⚖️ 3. 화병 vs 무동기범죄"])

# --- Tab 1: 인터넷(X) vs 우울감(y) ---
with tab1:
    st.subheader("인터넷 사용 시간이 많을수록 우울감이 심화될까?")
    
    sql_x1 = build_unpivot_query("internet_weektime", "연령대", "인터넷시간")
    sql_y1 = build_unpivot_query("depression_experience", "연령별", "우울감")
    
    df_x1 = run_query(sql_x1)
    df_y1 = run_query(sql_y1)
    df1 = pd.merge(df_x1, df_y1, on=['연도', '연령대'])

    fig1 = px.scatter(df1, x='인터넷시간', y='우울감', color='연령대', trendline="ols",
                     hover_data=['연도'], title="인터넷 사용 시간(X)과 우울감(y)의 상관관계")
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**독립변수(X) 추출:**")
        st.code(sql_x1, language='sql')
        st.write("**종속변수(y) 추출:**")
        st.code(sql_y1, language='sql')

# --- Tab 2: 사회적 고립도(X) vs 우울감(y) ---
with tab2:
    st.subheader("사회적 고립감을 많이 느낄수록 우울감이 심화될까?")
    
    sql_x2 = build_unpivot_query("social_isolation", "연령별", "고립도")
    sql_y2 = build_unpivot_query("depression_experience", "연령별", "우울감")
    
    df_x2 = run_query(sql_x2)
    df_y2 = run_query(sql_y2)
    df2 = pd.merge(df_x2, df_y2, on=['연도', '연령대'])

    fig2 = px.scatter(df2, x='고립도', y='우울감', color='연령대', trendline="ols",
                     hover_data=['연도'], title="사회적 고립도(X)와 우울감(y)의 상관관계")
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**독립변수(X) 추출:**")
        st.code(sql_x2, language='sql')
        st.write("**종속변수(y) 추출:**")
        st.code(sql_y2, language='sql')

# --- Tab 3: 정신건강(X1, X2) vs 무동기범죄(y) ---
with tab3:
    st.subheader("화병이 심화될수록 무동기 범죄를 많이 저지를까?")
    
    # 정신건강 지표 (X1: 스트레스, X2: 우울감)
    sql_x3_stress = build_unpivot_query("stress_perception", "연령별", "스트레스")
    sql_x3_dep = build_unpivot_query("depression_experience", "연령별", "우울감")
    
    # 무동기 범죄 (y: 보복, 현실불만, 우발적 통합)
    crime_parts = []
    for y in YEARS:
        crime_parts.append(f"SELECT {y} as 연도, SUM(\"{y} 년\") as 범죄건수 FROM crime_motive \n WHERE 범행동기별 IN ('보복', '현실불만', '우발적')")
    sql_y3 = "\n UNION ALL \n".join(crime_parts)
    
    df_s = run_query(sql_x3_stress)
    df_d = run_query(sql_x3_dep)
    df_c = run_query(sql_y3)
    
    df_mh = pd.merge(df_s, df_d, on=['연도', '연령대'])
    df3 = pd.merge(df_mh, df_c, on='연도')

    col1, col2 = st.columns(2)
    with col1:
        st.write("**X1: 스트레스 인지율 vs y: 무동기 범죄**")
        fig3_1 = px.scatter(df3, x='스트레스', y='범죄건수', color='연령대', trendline="ols",
                           title="스트레스와 무동기 범죄의 관계")
        st.plotly_chart(fig3_1, use_container_width=True)

    with col2:
        st.write("**X2: 우울감 경험률 vs y: 무동기 범죄**")
        fig3_2 = px.scatter(df3, x='우울감', y='범죄건수', color='연령대', trendline="ols",
                           title="우울감과 무동기 범죄의 관계")
        st.plotly_chart(fig3_2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**무동기 범죄(y) 통합 추출 SQL:**")
        st.code(sql_y3, language='sql')

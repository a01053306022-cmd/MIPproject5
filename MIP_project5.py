import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [설정 및 DB 체크] ---
st.set_page_config(page_title="화병 및 무동기 범죄 분석", layout="wide")

DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 누락되었습니다.")
    st.stop()

# --- [공통: 홀수년도 Wide -> Long 변환 SQL 생성기] ---
def get_long_sql(table_name, id_col, value_name):
    """SQLite에서 Unpivot을 수행하는 전체 SQL 쿼리를 생성합니다."""
    years = ['2013', '2015', '2017', '2019', '2021', '2023']
    union_queries = []
    for yr in years:
        # DB 컬럼명이 '2013 년' 형태이므로 큰따옴표로 감싸줍니다.
        union_queries.append(f"SELECT {id_col}, {yr} AS 연도, \"{yr} 년\" AS {value_name} FROM {table_name}")
    return " UNION ALL ".join(union_queries)

# DB 연결 함수
def run_query(q):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(q, conn)
    conn.close()
    return df

# --- [메인 화면] ---
st.title("🧠 사회 지표 기반 화병 및 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 인터넷 & 우울감", "🤝 사회적 고립도", "⚖️ 정신건강 & 무동기 범죄"])

# --- Tab 1: 인터넷 시간 (홀수년도 고정) ---
with tab1:
    st.subheader("1. 연도별 인터넷 사용 시간과 우울감 추이")
    
    sql_internet = get_long_sql("internet_weektime", "연령대", "인터넷시간")
    sql_depression = get_long_sql("depression_experience", "연령별", "우울감")
    
    df_i = run_query(sql_internet)
    df_d = run_query(sql_depression)
    df1 = pd.merge(df_i, df_d, left_on=['연도', '연령대'], right_on=['연도', '연령별'])

    fig1 = px.line(df1, x='연도', y='우울감', color='연령대', markers=True, title="홀수년도별 우울감 변화")
    # 가로축을 홀수년도만 표시하도록 설정
    fig1.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 전체 SQL 쿼리 보기"):
        st.info("Wide 형태의 데이터를 분석용 Long 형태로 바꾸기 위해 UNION ALL을 사용했습니다.")
        st.code(sql_internet, language='sql')

# --- Tab 2: 사회적 고립도 (연도별 나열) ---
with tab2:
    st.subheader("2. 연도별 사회적 고립도와 우울감의 변화")
    
    sql_isolation = get_long_sql("social_isolation", "연령별", "고립도")
    df2 = run_query(sql_isolation)
    
    # 산점도 애니메이션 또는 연도별 시각화
    fig2 = px.line(df2, x='연도', y='고립도', color='연령별', markers=True, title="연도별 사회적 고립도 추이")
    fig2.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 전체 SQL 쿼리 보기"):
        st.code(sql_isolation, language='sql')

# --- Tab 3: 스트레스/우울감 vs 무동기 범죄 (개별 표시) ---
with tab3:
    st.subheader("3. 정신건강 지표와 범죄 동기별 상관분석")
    
    # 1. 정신건강 데이터 (스트레스, 우울감 각각)
    sql_stress = get_long_sql("stress_perception", "연령별", "스트레스인지율")
    sql_dep = get_long_sql("depression_experience", "연령별", "우울감경험률")
    df_stress = run_query(sql_stress)
    df_dep = run_query(sql_dep)
    
    # 2. 범죄 데이터 (보복, 현실불만, 우발적 각각)
    # 범행동기별 컬럼이 있고 연도별로 인원수가 나열된 구조를 Long으로 변환
    years = ['2013', '2015', '2017', '2019', '2021', '2023']
    crime_parts = []
    for yr in years:
        crime_parts.append(f"SELECT 범행동기별, {yr} AS 연도, \"{yr} 년\" AS 인원수 FROM crime_motive WHERE 범행동기별 IN ('보복', '현실불만', '우발적')")
    sql_crime = " UNION ALL ".join(crime_parts)
    df_crime = run_query(sql_crime)

    # 화면 분할
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**[정신건강 지표]**")
        df_mh = pd.merge(df_stress, df_dep, on=['연도', '연령별'])
        # 스트레스와 우울감을 동시에 보기 위해 데이터 재구조화
        df_mh_melted = df_mh.melt(id_vars=['연도', '연령별'], value_vars=['스트레스인지율', '우울감경험률'], var_name='지표', value_name='비율')
        fig_mh = px.line(df_mh_melted, x='연도', y='비율', color='지표', facet_col='연령별', title="연령별 스트레스 및 우울감")
        fig_mh.update_xaxes(tickvals=[2013, 2017, 2021]) # 가독성을 위해 간격 조정
        st.plotly_chart(fig_mh, use_container_width=True)

    with col2:
        st.write("**[무동기 범죄 동기별 현황]**")
        # 요청하신 3분할 막대그래프 (Grouped Bar Chart)
        fig_crime = px.bar(df_crime, x='연도', y='인원수', color='범행동기별', barmode='group', title="연도별 무동기 범죄 세부 동기")
        fig_crime.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
        st.plotly_chart(fig_crime, use_container_width=True)

    with st.expander("📄 사용된 전체 SQL 쿼리 보기 (범죄 데이터 예시)"):
        st.write("범죄 동기별 데이터를 필터링하고 연도별로 통합하는 쿼리입니다.")
        st.code(sql_crime, language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 스트레스와 우울감 지표를 개별적으로 나열했을 때, 특정 연령대에서 특정 지표가 범죄 증감과 더 밀접한지 확인 가능합니다.")
        st.write("- 무동기 범죄 중 '우발적' 범죄의 비중이 타 동기에 비해 압도적으로 높은지 등을 시각적으로 즉시 파악할 수 있습니다.")

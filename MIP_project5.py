import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정] ---
st.set_page_config(page_title="화병-사회지표 상관분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 파일이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# 홀수 연도 리스트
YEARS = ['2013', '2015', '2017', '2019', '2021', '2023']

# --- [2. 공통 SQL 생성 함수 (줄바꿈 포함)] ---
def get_sql(table, age_col, val_name, is_crime=False):
    parts = []
    for y in YEARS:
        col = f'"{y} 년"' if is_crime else f'"{y}"'
        parts.append(f"SELECT TRIM({age_col}) as 연령대, {y} as 연도, {col} as {val_name} FROM {table}")
    return "\n UNION ALL \n".join(parts)

# --- [3. 메인 화면] ---
st.title("🧠 사회 지표 변화에 따른 화병 및 범죄 추이 분석")
tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 & 우울감", "🤝 2. 고립도 & 우울감", "⚖️ 3. 화병 vs 무동기 범죄"])

# --- Tab 1: 인터넷(X) & 우울감(y) ---
with tab1:
    st.subheader("연도별 인터넷 사용 시간(X)과 우울감(y)의 동반 추이")
    
    sql_i = get_sql("internet_weektime", "연령대", "수치")
    sql_d = get_sql("depression_experience", "연령별", "수치")
    
    df_i = run_query(sql_i); df_i['지표'] = '인터넷시간(X)'
    df_d = run_query(sql_d); df_d['지표'] = '우울감경험률(y)'
    df1 = pd.concat([df_i, df_d]) # 두 데이터를 위아래로 합침

    # 가로축(x)을 '연도'로 설정하여 시계열 분석
    fig1 = px.line(df1, x='연도', y='수치', color='지표', facet_col='연령대', markers=True,
                  title="연령대별 인터넷 시간과 우울감의 상관관계 (X축: 연도)")
    fig1.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql_i, language='sql')

# --- Tab 2: 사회적 고립도(X) & 우울감(y) ---
with tab2:
    st.subheader("연도별 사회적 고립도(X)와 우울감(y)의 동반 추이")
    
    sql_s = get_sql("social_isolation", "연령별", "수치")
    df_s = run_query(sql_s); df_s['지표'] = '사회적고립도(X)'
    df_d2 = run_query(sql_d); df_d2['지표'] = '우울감경험률(y)'
    df2 = pd.concat([df_s, df_d2])

    fig2 = px.line(df2, x='연도', y='수치', color='지표', facet_col='연령대', markers=True,
                  title="연령대별 사회적 고립도와 우울감의 상관관계 (X축: 연도)")
    fig2.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql_s, language='sql')

# --- Tab 3: 정신건강(X) & 무동기 범죄(y) ---
with tab3:
    st.subheader("화병(스트레스, 우울감) 심화에 따른 무동기 범죄 발생 현황")
    
    # X변수들
    sql_st = get_sql("stress_perception", "연령별", "수치")
    df_st = run_query(sql_st); df_st['지표'] = 'X1:스트레스'
    df_de = run_query(sql_d); df_de['지표'] = 'X2:우울감'
    df_x3 = pd.concat([df_st, df_de])

    # y변수 (무동기 범죄 세부 동기별)
    crime_parts = []
    for y in YEARS:
        crime_parts.append(f"SELECT {y} as 연도, 범행동기별, \"{y} 년\" as 건수 FROM crime_motive \n WHERE 범행동기별 IN ('보복', '현실불만', '우발적')")
    sql_y3 = "\n UNION ALL \n".join(crime_parts)
    df_y3 = run_query(sql_y3)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("**[X] 정신건강 지표 추이 (연령대별)**")
        fig3_x = px.line(df_x3, x='연도', y='수치', color='지표', facet_row='연령대', markers=True)
        fig3_x.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
        st.plotly_chart(fig3_x, use_container_width=True)

    with col2:
        st.write("**[y] 무동기 범죄 동기별 건수 (3분할 막대)**")
        fig3_y = px.bar(df_y3, x='연도', y='건수', color='범행동기별', barmode='group',
                       title="연도별 무동기 범죄 발생 (보복/현실불만/우발적)")
        fig3_y.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
        st.plotly_chart(fig3_y, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**정신건강(X) 추출:**")
        st.code(sql_st, language='sql')
        st.write("**무동기 범죄(y) 세부 추출:**")
        st.code(sql_y3, language='sql')

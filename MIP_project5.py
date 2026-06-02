import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-사회지표 분석 대시보드", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 데이터베이스 파일이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 공통 SQL 생성 함수 (2013/2023 전용)] ---
def get_metrics_sql(table, age_col, val_name):
    """지표 테이블(internet, depression, stress, isolation) 전용 쿼리"""
    return f"""
SELECT TRIM({age_col}) as 연령대, \n
       '2013' as 연도, \n
       CAST("2013" AS FLOAT) as {val_name} \n
FROM {table} \n
UNION ALL \n
SELECT TRIM({age_col}) as 연령대, \n
       '2023' as 연도, \n
       CAST("2023" AS FLOAT) as {val_name} \n
FROM {table}
"""

def get_crime_age_sql():
    """연령별 전체 범죄 건수 추출 쿼리"""
    return """
SELECT TRIM(범행연령별) as 연령대, \n
       '2013' as 연도, \n
       CAST("2013 년" AS INTEGER) as 전체건수 \n
FROM crime_age \n
UNION ALL \n
SELECT TRIM(범행연령별) as 연령대, \n
       '2023' as 연도, \n
       CAST("2023 년" AS INTEGER) as 전체건수 \n
FROM crime_age
"""

# --- [3. 메인 화면] ---
st.title("📊 데이터 기반 사회현상 및 무동기 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 사용 집단별 분석", "🤝 2. 고립도-정신건강 궤적", "⚖️ 3. 연령별 범죄 및 화병 지표"])

# --- [Tab 1] ---
with tab1:
    st.header("1. 인터넷 사용량 집단(상/중/하)에 따른 정신건강 수준")
    
    sql_x = get_metrics_sql("internet_weektime", "연령대", "인터넷시간")
    sql_y_dep = get_metrics_sql("depression_experience", "연령별", "우울감")
    sql_y_str = get_metrics_sql("stress_perception", "연령별", "스트레스")
    
    df_x = run_query(sql_x)
    df_y_dep = run_query(sql_y_dep)
    df_y_str = run_query(sql_y_str)
    
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대'])
    df1['집단'] = pd.qcut(df1['인터넷시간'], q=3, labels=['하', '중', '상'])
    df1_grouped = df1.groupby(['집단', '연도'])[['우울감', '스트레스']].mean().reset_index()

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df1_grouped, x='집단', y='우울감', color='연도', barmode='group', title="집단별 평균 우울감"), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df1_grouped, x='집단', y='스트레스', color='연도', barmode='group', title="집단별 평균 스트레스"), use_container_width=True)

    with st.expander("📄 사용된 SQL 쿼리 보기"):
        st.write("**1. 인터넷 사용 시간(독립변수 X):**")
        st.code(sql_x, language='sql')
        st.write("**2. 우울감 및 스트레스(종속변수 y):**")
        st.code(sql_y_dep, language='sql')
        st.code(sql_y_str, language='sql')

# --- [Tab 2] ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강의 10년 변화 궤적")
    
    sql_iso = get_metrics_sql("social_isolation", "연령별", "고립도")
    df_iso = run_query(sql_iso)
    df2 = pd.merge(df_iso, df_y_dep, on=['연도', '연령대'])
    
    fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도', title="연령대별 고립도-우울감 변화")
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 쿼리 보기"):
        st.write("**1. 사회적 고립도 추출:**")
        st.code(sql_iso, language='sql')
        st.write("**2. 우울감 데이터 추출 (1탭과 동일):**")
        st.code(sql_y_dep, language='sql')

# --- [Tab 3] ---
with tab3:
    st.header("3. 연령별 범죄 동기 및 정신건강 지표 중첩 분석")

    sql_age = get_crime_age_sql()
    sql_m = """
SELECT '2013' as 연도, '현실불만' as 동기, CAST("2013 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n
UNION ALL \n
SELECT '2013', '우발적', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n
UNION ALL \n
SELECT '2023' as 연도, '현실불만' as 동기, CAST("2023 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n
UNION ALL \n
SELECT '2023', '우발적', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'
"""
    df_age = run_query(sql_age)
    df_m = run_query(sql_m)

    for year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {year}년 분석")
        
        c_age = df_age[df_age['연도'] == year]
        c_mot = df_m[df_m['연도'] == year]
        m_dep = df_y_dep[df_y_dep['연도'] == year]
        m_str = df_y_str[df_y_str['연도'] == year]
        
        ratio = c_mot.set_index('동기')['건수'] / c_mot['건수'].sum()
        bar_list = []
        for _, row in c_age.iterrows():
            bar_list.append({'연령대': row['연령대'], '동기': '우발적', '건수': row['전체건수'] * ratio['우발적']})
            bar_list.append({'연령대': row['연령대'], '동기': '현실불만', '건수': row['전체건수'] * ratio['현실불만']})
        df_stack = pd.DataFrame(bar_list)
        df_stack['동기'] = pd.Categorical(df_stack['동기'], categories=['우발적', '현실불만'], ordered=True)
        df_stack = df_stack.sort_values('동기')

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        for motive in ['우발적', '현실불만']:
            sub_df = df_stack[df_stack['동기'] == motive]
            fig3.add_trace(go.Bar(name=motive, x=sub_df['연령대'], y=sub_df['건수']), secondary_y=False)

        fig3.add_trace(go.Scatter(name='우울감(%)', x=m_dep['연령대'], y=m_dep['우울감'], mode='lines+markers', line=dict(color='red', width=3)), secondary_y=True)
        fig3.add_trace(go.Scatter(name='스트레스(%)', x=m_str['연령대'], y=m_str['스트레스'], mode='lines+markers', line=dict(color='orange', width=3)), secondary_y=True)

        fig3.update_layout(title_text=f"{year}년 복합 분석", barmode='stack')
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📄 사용된 SQL 쿼리 보기"):
        st.write("**1. 연령별 전체 범죄 건수:**")
        st.code(sql_age, language='sql')
        st.write("**2. 범죄 동기 비중 추출:**")
        st.code(sql_m, language='sql')

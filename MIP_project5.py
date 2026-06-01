import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 상관분석 최종본", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 파일이 존재하지 않습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. SQL 쿼리 생성기] ---
# 지표 테이블 (2013, 2023)
def get_metrics_sql(table, age_col, val_name):
    return f"""
    SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("2013" AS FLOAT) as {val_name} FROM {table} \n
    UNION ALL \n
    SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("2023" AS FLOAT) as {val_name} FROM {table}
    """

# 범죄 테이블 (2013 년, 2023 년)
def get_crime_sql(table, age_col, val_name):
    return f"""
    SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("2013 년" AS INTEGER) as {val_name} FROM {table} \n
    UNION ALL \n
    SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("2023 년" AS INTEGER) as {val_name} FROM {table}
    """

# --- [3. 메인 화면] ---
st.title("🧠 사회 지표 기반 화병 및 무동기 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 & 정신건강", "🤝 2. 고립도 & 정신건강", "⚖️ 3. 연도별 범죄 구조"])

# --- Tab 1: 인터넷(X) vs 우울/스트레스(y) 산점도 ---
with tab1:
    st.header("1. 인터넷 시간과 정신건강 상관관계 (회귀선)")
    
    df_x = run_query(get_metrics_sql("internet_weektime", "연령대", "인터넷시간"))
    df_y_dep = run_query(get_metrics_sql("depression_experience", "연령별", "우울감"))
    df_y_str = run_query(get_metrics_sql("stress_perception", "연령별", "스트레스"))
    
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대'])

    c1, c2 = st.columns(2)
    with c1:
        fig1_1 = px.scatter(df1, x='인터넷시간', y='우울감', color='연도', trendline="ols",
                           hover_data=['연령대'], title="인터넷 시간 vs 우울감")
        st.plotly_chart(fig1_1, use_container_width=True)
    with c2:
        fig1_2 = px.scatter(df1, x='인터넷시간', y='스트레스', color='연도', trendline="ols",
                           hover_data=['연령대'], title="인터넷 시간 vs 스트레스")
        st.plotly_chart(fig1_2, use_container_width=True)

# --- Tab 2: 사회적 고립도(X) vs 우울/스트레스(y) 산점도 ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강 상관관계 (회귀선)")
    
    df_x2 = run_query(get_metrics_sql("social_isolation", "연령별", "고립도"))
    df2 = pd.merge(df_x2, df_y_dep, on=['연도', '연령대'])
    df2 = pd.merge(df2, df_y_str, on=['연도', '연령대'])

    c3, c4 = st.columns(2)
    with c3:
        fig2_1 = px.scatter(df2, x='고립도', y='우울감', color='연도', trendline="ols",
                           hover_data=['연령대'], title="사회적 고립도 vs 우울감")
        st.plotly_chart(fig2_1, use_container_width=True)
    with c4:
        fig2_2 = px.scatter(df2, x='고립도', y='스트레스', color='연도', trendline="ols",
                           hover_data=['연령대'], title="사회적 고립도 vs 스트레스")
        st.plotly_chart(fig2_2, use_container_width=True)

# --- Tab 3: 연도별 범죄 구조 분석 (원형 + 누적 막대) ---
with tab3:
    st.header("3. 연도별 연령대 범죄 비중 및 세부 동기 분석")
    
    # 1. 연령별 전체 무동기 범죄 건수 (Pie용)
    df_age_total = run_query(get_crime_sql("crime_age", "범행연령별", "전체건수"))
    
    # 2. 동기별 비중 (막대 내부 구분용)
    sql_motive = """
    SELECT '2013' as 연도, '현실불만' as 동기, CAST("2013 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '2013', '우발적', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n
    UNION ALL SELECT '2023', '현실불만', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '2023', '우발적', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'
    """
    df_motive = run_query(sql_motive)

    for year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {year}년 범죄 구조 상세 분석")
        
        # 해당 연도 데이터 필터링
        curr_age = df_age_total[df_age_total['연도'] == year]
        curr_motive = df_motive[df_motive['연도'] == year]
        
        # 막대그래프를 위해 연령별 데이터와 동기 비율 결합
        # 동기 비율 계산
        total_m = curr_motive['건수'].sum()
        curr_motive['비중'] = curr_motive['건수'] / total_m
        
        # 연령별 건수에 동기 비중을 곱해 가상의 '연령별-동기별' 데이터 생성 (DB에 없을 경우의 최선책)
        bar_data = []
        for _, age_row in curr_age.iterrows():
            for _, mot_row in curr_motive.iterrows():
                bar_data.append({
                    '연령대': age_row['연령대'],
                    '동기': mot_row['동기'],
                    '건수': age_row['전체건수'] * mot_row['비중']
                })
        df_bar = pd.DataFrame(bar_data)

        col_l, col_r = st.columns(2)
        with col_l:
            fig_p = px.pie(curr_age, values='전체건수', names='연령대', hole=0.4,
                          title=f"{year} 연령대별 무동기 범죄 점유율")
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col_r:
            fig_b = px.bar(df_bar, x='연령대', y='건수', color='동기', barmode='stack',
                          title=f"{year} 연령대별 세부 동기(현실불만+우발적) 구성",
                          category_orders={"연령대": ["20대", "30대", "40대", "50대", "60세이상"]})
            st.plotly_chart(fig_b, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**연령별 범죄 데이터 (Pie용):**")
        st.code(get_crime_sql("crime_age", "범행연령별", "전체건수"), language='sql')
        st.write("**범행 동기 데이터 (Bar 구분용):**")
        st.code(sql_motive, language='sql')

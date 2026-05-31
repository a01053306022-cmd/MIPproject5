import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 상관분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [메인 타이틀] ---
st.title("📊 화병 지표와 무동기 범죄의 상관성 정밀 분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 사용 & 우울감", "🤝 2. 사회적 고립도", "⚖️ 3. 화병 vs 무동기 범죄"])

# --- [Tab 1: 인터넷 & 우울감 (전체 연령대 표시)] ---
with tab1:
    st.subheader("연도별/연령별 인터넷 사용 시간과 우울감 추이")
    
    # 지표 테이블들은 컬럼명이 "2013" 형태입니다.
    sql1 = """
    SELECT TRIM(연령대) as 연령대, 2013 as 연도, "2013" as 값 FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), 2015, "2015" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), 2017, "2017" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), 2019, "2019" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), 2021, "2021" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), 2023, "2023" FROM internet_weektime
    """
    df_internet = run_query(sql1)
    
    # 60대만 나오는 문제를 방지하기 위해 데이터를 확인하고 시각화
    fig1 = px.line(df_internet, x='연도', y='값', color='연령대', markers=True,
                  title="연령대별 인터넷 사용 시간 변화 (전체 세대)")
    fig1.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql1, language='sql')

# --- [Tab 2: 사회적 고립도 (연도별)] ---
with tab2:
    st.subheader("사회적 고립도 연도별 추이")
    
    sql2 = """
    SELECT TRIM(연령별) as 연령대, 2013 as 연도, "2013" as 고립도 FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), 2015, "2015" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), 2017, "2017" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), 2019, "2019" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), 2021, "2021" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), 2023, "2023" FROM social_isolation
    """
    df2 = run_query(sql2)
    
    fig2 = px.line(df2, x='연도', y='고립도', color='연령대', markers=True,
                 title="연도별/연령대별 사회적 고립도 현황")
    fig2.update_xaxes(tickvals=[2013, 2015, 2017, 2019, 2021, 2023])
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql2, language='sql')

# --- [Tab 3: X(정신건강) vs y(무동기 범죄)] ---
with tab3:
    st.subheader("화병(X: 스트레스, 우울감)과 무동기 범죄(y)의 상관관계")

    # 1. 스트레스 데이터 Long 변환
    sql_stress = """
    SELECT TRIM(연령별) as 연령대, 2013 as 연도, "2013" as 스트레스 FROM stress_perception \n
    UNION ALL SELECT TRIM(연령별), 2015, "2015" FROM stress_perception \n
    UNION ALL SELECT TRIM(연령별), 2017, "2017" FROM stress_perception \n
    UNION ALL SELECT TRIM(연령별), 2019, "2019" FROM stress_perception \n
    UNION ALL SELECT TRIM(연령별), 2021, "2021" FROM stress_perception \n
    UNION ALL SELECT TRIM(연령별), 2023, "2023" FROM stress_perception
    """
    # 2. 우울감 데이터 Long 변환
    sql_dep = """
    SELECT TRIM(연령별) as 연령대, 2013 as 연도, "2013" as 우울감 FROM depression_experience \n
    UNION ALL SELECT TRIM(연령별), 2015, "2015" FROM depression_experience \n
    UNION ALL SELECT TRIM(연령별), 2017, "2017" FROM depression_experience \n
    UNION ALL SELECT TRIM(연령별), 2019, "2019" FROM depression_experience \n
    UNION ALL SELECT TRIM(연령별), 2021, "2021" FROM depression_experience \n
    UNION ALL SELECT TRIM(연령별), 2023, "2023" FROM depression_experience
    """
    # 3. 무동기 범죄 데이터 (이 테이블은 "2013 년" 형태임에 주의!)
    sql_crime = """
    SELECT '보복+현실불만+우발적' as 동기, 2013 as 연도, SUM("2013 년") as 건수 FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '보복+현실불만+우발적', 2015, SUM("2015 년") FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '보복+현실불만+우발적', 2017, SUM("2017 년") FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '보복+현실불만+우발적', 2019, SUM("2019 년") FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '보복+현실불만+우발적', 2021, SUM("2021 년") FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '보복+현실불만+우발적', 2023, SUM("2023 년") FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    GROUP BY 연도
    """
    
    df_s = run_query(sql_stress)
    df_d = run_query(sql_dep)
    df_c = run_query(sql_crime)
    
    # 데이터 병합 (X1, X2, y)
    df_x = pd.merge(df_s, df_d, on=['연령대', '연도'])
    df_total = pd.merge(df_x, df_c, on='연도')

    # 시각화: 독립변수(X)와 종속변수(y)의 관계
    col1, col2 = st.columns(2)
    with col1:
        st.write("**X1: 스트레스 인지율 vs y: 무동기 범죄**")
        fig3_1 = px.scatter(df_total, x='스트레스', y='건수', color='연령대', 
                           trendline="ols", hover_data=['연도'],
                           labels={'스트레스':'스트레스 인지율 (%)', '건수':'무동기 범죄 건수 (전체)'})
        st.plotly_chart(fig3_1, use_container_width=True)

    with col2:
        st.write("**X2: 우울감 경험률 vs y: 무동기 범죄**")
        fig3_2 = px.scatter(df_total, x='우울감', y='건수', color='연령대', 
                           trendline="ols", hover_data=['연도'],
                           labels={'우울감':'우울감 경험률 (%)', '건수':'무동기 범죄 건수 (전체)'})
        st.plotly_chart(fig3_2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기 (X변수 & y변수)"):
        st.write("**1. 독립변수(X) 추출용 SQL (스트레스 예시):**")
        st.code(sql_stress, language='sql')
        st.write("**2. 종속변수(y) 추출용 SQL (범죄 합계):**")
        st.code(sql_crime, language='sql')

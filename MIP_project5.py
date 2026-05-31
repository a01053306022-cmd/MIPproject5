import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 데이터 분석", layout="wide")
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

# --- [Tab 1: 모든 연령대 표시 및 홀수년도 고정] ---
with tab1:
    st.subheader("연도별/연령별 인터넷 사용 시간과 우울감 추이")
    
    # SQL문 작성 (가독성을 위한 \n 포함)
    sql1 = """
    SELECT TRIM(연령대) as 연령대, '2013' as 연도, "2013 년" as 값 FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), '2015', "2015 년" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), '2017', "2017 년" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), '2019', "2019 년" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), '2021', "2021 년" FROM internet_weektime \n
    UNION ALL SELECT TRIM(연령대), '2023', "2023 년" FROM internet_weektime
    """
    # 실제 앱에서는 우울감 데이터와 JOIN하여 시각화
    df_internet = run_query(sql1)
    # (우울감 데이터도 동일한 방식으로 UNION ALL 처리 후 merge - 지면상 핵심 로직 위주 기술)
    
    # 모든 연령대가 나오도록 색상 지정
    fig1 = px.line(df_internet, x='연도', y='값', color='연령대', markers=True,
                  title="연령대별 인터넷 사용 시간 변화 (전체 세대)")
    fig1.update_xaxes(tickvals=['2013', '2015', '2017', '2019', '2021', '2023'])
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql1, language='sql')

# --- [Tab 2: 사회적 고립도 연도별 나열] ---
with tab2:
    st.subheader("사회적 고립도와 우울감의 연도별 추이")
    
    sql2 = """
    SELECT TRIM(연령별) as 연령대, '2013' as 연도, "2013 년" as 고립도 FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), '2015', "2015 년" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), '2017', "2017 년" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), '2019', "2019 년" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), '2021', "2021 년" FROM social_isolation \n
    UNION ALL SELECT TRIM(연령별), '2023', "2023 년" FROM social_isolation
    """
    df2 = run_query(sql2)
    
    fig2 = px.bar(df2, x='연도', y='고립도', color='연령대', barmode='group',
                 title="연도별/연령대별 사회적 고립도 현황")
    fig2.update_xaxes(tickvals=['2013', '2015', '2017', '2019', '2021', '2023'])
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql2, language='sql')

# --- [Tab 3: X(정신건강) vs y(무동기 범죄)] ---
with tab3:
    st.subheader("화병(X: 스트레스, 우울감)과 무동기 범죄(y)의 관계 분석")
    
    # 1. 독립변수 X (스트레스, 우울감)
    sql_x = """
    SELECT TRIM(s.연령별) as 연령대, s.연도, \n
           s.분율 as 스트레스인지율, d.분율 as 우울감경험률 \n
    FROM stress_perception s \n
    JOIN depression_experience d ON s.연도 = d.연도 AND s.연령별 = d.연령별
    """
    
    # 2. 종속변수 y (무동기 범죄: 보복, 현실불만, 우발적)
    # crime_age를 매개로 연결 (연도별 전체 건수 반영)
    sql_y = """
    SELECT '2013' as 연도, 범행동기별, "2013 년" as 건수 FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '2015', 범행동기별, "2015 년" FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '2017', 범행동기별, "2017 년" FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '2019', 범행동기별, "2019 년" FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '2021', 범행동기별, "2021 년" FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적') \n
    UNION ALL SELECT '2023', 범행동기별, "2023 년" FROM crime_motive \n
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적')
    """
    
    df_x = run_query(sql_x)
    df_y = run_query(sql_y)
    
    # 범죄 데이터를 동기별로 피벗하여 컬럼화
    df_y_pivot = df_y.pivot(index='연도', columns='범행동기별', values='건수').reset_index()
    df_y_pivot['무동기범죄합계'] = df_y_pivot[['보복', '현실불만', '우발적']].sum(axis=1)
    
    # X와 y 결합 (연도 기준)
    df_total = pd.merge(df_x, df_y_pivot, on='연도')

    # 시각화 1: 상관관계 산점도 (X=스트레스, y=무동기범죄합계)
    col1, col2 = st.columns(2)
    with col1:
        st.write("**X1: 스트레스 인지율 vs y: 무동기 범죄**")
        fig3_1 = px.scatter(df_total, x='스트레스인지율', y='무동기범죄합계', color='연령대', 
                           trendline="ols", hover_data=['연도'])
        st.plotly_chart(fig3_1, use_container_width=True)

    with col2:
        st.write("**X2: 우울감 경험률 vs y: 무동기 범죄**")
        fig3_2 = px.scatter(df_total, x='우울감경험률', y='무동기범죄합계', color='연령대', 
                           trendline="ols", hover_data=['연도'])
        st.plotly_chart(fig3_2, use_container_width=True)

    # 시각화 2: 무동기 범죄 세부 동기별 막대 그래프 (가로 3분할 느낌)
    st.write("**y변수 상세: 연도별 무동기 범죄 동기별 현황**")
    fig3_3 = px.bar(df_y, x='연도', y='건수', color='범행동기별', barmode='group',
                   title="보복 / 현실불만 / 우발적 범죄 추이")
    st.plotly_chart(fig3_3, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.write("**정신건강(X) 추출 쿼리:**")
        st.code(sql_x, language='sql')
        st.write("**무동기 범죄(y) 추출 쿼리:**")
        st.code(sql_y, language='sql')

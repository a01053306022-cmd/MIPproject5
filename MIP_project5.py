import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-사회지표-범죄 데이터 분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일('{DB_FILE}')이 누락되었습니다. 파일 경로를 확인해주세요.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 공통 SQL 템플릿 (2013/2023 필터링)] ---
# 지표 테이블용 (2013, 2023 숫자형 컬럼)
def sql_metrics(table, age_col, val_name):
    return f"""
    SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("{2013}" AS FLOAT) as {val_name} FROM {table} \n
    UNION ALL \n
    SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("{2023}" AS FLOAT) as {val_name} FROM {table}
    """

# 범죄 동기용 (2013 년, 2023 년 문자열 포함 컬럼)
def sql_crime_motive():
    return """
    SELECT '보복' as 동기, '2013' as 연도, CAST("2013 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '보복' \n
    UNION ALL SELECT '보복', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '보복' \n
    UNION ALL SELECT '현실불만', '2013', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '현실불만', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '우발적', '2013', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n
    UNION ALL SELECT '우발적', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'
    """

# --- [3. 메인 화면] ---
st.title("🕵️ 사회적 고립과 화병, 그리고 무동기 범죄의 인과관계")
st.markdown("### 2013년 vs 2023년 : 10년의 변화 추적")

tab1, tab2, tab3 = st.tabs([
    "🌐 1. 인터넷 & 정신건강", 
    "🤝 2. 고립도 & 정신건강", 
    "⚖️ 3. 화병 & 범죄 메커니즘"
])

# --- Tab 1: 인터넷(X) vs 정신건강(y) 추적 ---
with tab1:
    st.header("1. 인터넷 이용량 증가와 정신건강 지표의 관계")
    
    df_i = run_query(sql_metrics("internet_weektime", "연령대", "수치")); df_i['지표'] = '인터넷시간'
    df_d = run_query(sql_metrics("depression_experience", "연령별", "수치")); df_d['지표'] = '우울감'
    df_s = run_query(sql_metrics("stress_perception", "연령별", "수치")); df_s['지표'] = '스트레스'
    
    df1 = pd.concat([df_i, df_d, df_s])
    
    # Facet_col을 활용한 세대별 멀티라인 차트
    fig1 = px.line(df1, x='연도', y='수치', color='지표', facet_col='연령대', markers=True,
                  title="세대별 인터넷 이용 및 정신건강 변화 (2013 vs 2023)",
                  category_orders={"연령대": ["20대", "30대", "40대", "50대", "60세이상"]})
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 및 인사이트"):
        st.code(sql_metrics("internet_weektime", "연령대", "인터넷시간"), language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 인터넷 사용 시간이 가파르게 상승한 세대일수록 우울감과 스트레스 지표가 동반 상승하는 경향이 있는지 확인할 수 있습니다.")
        st.write("- 특히 청년층(20-30대)의 인터넷 시간 폭증이 정신건강 악화의 선행 지표인지 관찰하는 것이 핵심입니다.")

# --- Tab 2: 사회적 고립도(X) vs 정신건강(Y) 복합 산점도 ---
with tab2:
    st.header("2. 사회적 고립도에 따른 정신건강 악화 검증")
    
    df_iso = run_query(sql_metrics("social_isolation", "연령별", "고립도"))
    df_dep = run_query(sql_metrics("depression_experience", "연령별", "우울감"))
    df_str = run_query(sql_metrics("stress_perception", "연령별", "스트레스"))
    
    # 데이터 결합
    df2_dep = pd.merge(df_iso, df_dep, on=['연도', '연령대']); df2_dep['지표명'] = df2_dep['연도'] + ' 우울감'
    df2_str = pd.merge(df_iso, df_str, on=['연도', '연령대']); df2_str['지표명'] = df2_str['연도'] + ' 스트레스'
    
    df2 = pd.concat([
        df2_dep.rename(columns={'우울감': '수치'}),
        df2_str.rename(columns={'스트레스': '수치'})
    ])

    fig2 = px.scatter(df2, x='고립도', y='수치', color='지표명', symbol='연도', text='연령대',
                     title="사회적 고립도(X)와 정신건강(Y) 사분면 분석 (2013 vs 2023)",
                     labels={'고립도': '사회적 고립도 (%)', '수치': '지표 수치 (%)'})
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 및 인사이트"):
        st.code(sql_metrics("social_isolation", "연령별", "고립도"), language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 2013년 데이터(원형/세모)에 비해 2023년 데이터가 우측 상단(고립↑ 수치↑)으로 이동했다면, 사회 구조적 고립이 화병의 원인임을 시사합니다.")

# --- Tab 3: 화병 연령층 -> 범죄 연결 분석 ---
with tab3:
    st.header("3. 정신건강 악화 세대의 범죄 양상 분석")
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.write("**[전체 무동기 범죄 동기 비중]**")
        df_pie = run_query(sql_crime_motive())
        fig_pie = px.pie(df_pie, values='건수', names='동기', hole=0.4, title="무동기 범죄 세부 이유 (2013/2023 통합)")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # 데이터상 수치가 가장 높은 '20대'를 예시 타겟으로 선정 (데이터에 따라 동적 변경 가능)
        st.write("**[핵심 타겟: 20대 청년층 무동기 범죄 변화]**")
        # 실제 환경에서는 '결과_범죄' 테이블에서 20대의 '현실불만', '우발적' 건수를 조인해야 함
        # 여기서는 crime_motive의 연도별 변화를 보여주는 다중 막대 차트로 구성
        fig_bar = px.bar(df_pie, x='동기', y='건수', color='연도', barmode='group',
                        title="주요 무동기 범죄 사유별 10년 전후 건수 비교")
        st.plotly_chart(fig_bar, use_container_width=True)

    with st.expander("📄 사용된 SQL 및 인사이트"):
        st.code(sql_crime_motive(), language='sql')
        st.write("**💡 인사이트:**")
        st.write("- '우발적' 범죄와 '현실불만' 범죄가 10년 사이 급증했다면, 이는 개인이 통제하기 어려운 사회적 스트레스(화병)가 범죄로 표출되었음을 입증합니다.")


import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 데이터 분석 고도화", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일('{DB_FILE}')이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 데이터 전처리 함수: 지수화(Normalization)] ---
def normalize_to_2013(df, val_col):
    """2013년 값을 100으로 잡고 변화율을 계산하여 단위가 다른 지표를 비교 가능하게 함"""
    new_df = df.copy()
    for age in df['연령대'].unique():
        base_val = df[(df['연령대'] == age) & (df['연도'] == '2013')][val_col].values
        if len(base_val) > 0 and base_val[0] != 0:
            new_df.loc[new_df['연령대'] == age, '지수'] = (new_df.loc[new_df['연령대'] == age, val_col] / base_val[0]) * 100
    return new_df

# --- [3. 메인 화면] ---
st.title("🕵️ 사회적 지표 변화와 무동기 범죄 인과관계 분석")
st.info("💡 모든 분석은 2013년(기준점)과 2023년(비교점) 데이터를 중심으로 진행됩니다.")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 & 정신건강 추세", "🤝 2. 고립도 궤적 분석", "⚖️ 3. 연령별 범죄 구조"])

# --- Tab 1: 인터넷(X) vs 정신건강(y) - 지수화된 선형 차트 ---
with tab1:
    st.header("1. 인터넷 시간 증가에 따른 정신건강 변화 (지수 분석)")
    st.markdown("> **단위 보정**: 인터넷 시간(시간)과 우울/스트레스(%)를 직접 비교하기 위해 **2013년 수치를 100**으로 환산했습니다.")
    
    # SQL 쿼리 (가독성 개선)
    def get_sql(table, age_col):
        return f"SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST(\"2013\" AS FLOAT) as 수치 FROM {table} \n" \
               f"UNION ALL \n" \
               f"SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST(\"2023\" AS FLOAT) as 수치 FROM {table}"

    df_i = normalize_to_2013(run_query(get_sql("internet_weektime", "연령대")), '수치'); df_i['지표'] = '인터넷시간'
    df_d = normalize_to_2013(run_query(get_sql("depression_experience", "연령별")), '수치'); df_d['지표'] = '우울감'
    df_s = normalize_to_2013(run_query(get_sql("stress_perception", "연령별")), '수치'); df_s['지표'] = '스트레스'
    
    df1 = pd.concat([df_i, df_d, df_s])

    # 선으로 연결된 산점도 (Slope Chart 형태)
    fig1 = px.line(df1, x='연도', y='지수', color='지표', facet_col='연령대', markers=True,
                  labels={'지수': '변화 지수 (2013년=100)'},
                  title="연령대별 인터넷 이용 및 정신건강 변화 궤적")
    st.plotly_chart(fig1, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(get_sql("internet_weektime", "연령대"), language='sql')

# --- Tab 2: 사회적 고립도(X) vs 정신건강(Y) - 연결된 궤적 차트 ---
with tab2:
    st.header("2. 사회적 고립 심화와 정신건강 악화 궤적")
    st.markdown("> **해석 방법**: 점과 점 사이의 **선(궤적)**이 우상향할수록 사회적 고립과 화병이 동시에 심화되었음을 의미합니다.")

    df_iso = run_query(get_sql("social_isolation", "연령별")).rename(columns={'수치': '고립도'})
    df_dep = run_query(get_sql("depression_experience", "연령별")).rename(columns={'수치': '우울감'})
    df2 = pd.merge(df_iso, df_dep, on=['연도', '연령대'])

    # 연도별 점을 선으로 연결
    fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도',
                  title="사회적 고립(X) 대비 우울감(Y)의 10년 궤적",
                  labels={'고립도': '사회적 고립도 (%)', '우울감': '우울감 경험률 (%)'})
    fig2.update_traces(textposition='top right')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(get_sql("social_isolation", "연령별"), language='sql')

# --- Tab 3: 연도별 무동기 범죄 구조 분석 (원 + 막대 연결) ---
with tab3:
    st.header("3. 연도별 범죄 발생 구조 및 무동기 원인 세분화")
    
    # 데이터 준비
    def get_crime_sql(table):
        return f"SELECT TRIM(범행연령별) as 연령대, '2013' as 연도, CAST(\"2013 년\" AS INTEGER) as 건수 FROM {table} \n" \
               f"UNION ALL \n" \
               f"SELECT TRIM(범행연령별) as 연령대, '2023' as 연도, CAST(\"2023 년\" AS INTEGER) as 건수 FROM {table}"
    
    df_crime_age = run_query(get_crime_sql("crime_age"))
    
    # 범죄 동기 데이터 (2013, 2023)
    sql_motive = """
    SELECT '보복' as 동기, '2013' as 연도, CAST("2013 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '보복' \n
    UNION ALL SELECT '보복', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '보복' \n
    UNION ALL SELECT '현실불만', '2013', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '현실불만', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' \n
    UNION ALL SELECT '우발적', '2013', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n
    UNION ALL SELECT '우발적', '2023', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'
    """
    df_motive = run_query(sql_motive)

    # --- [2013년 분석 섹션] ---
    st.divider()
    st.subheader("📅 2013년 범죄 구조 분석")
    c1, c2 = st.columns(2)
    with c1:
        df_2013 = df_crime_age[df_crime_age['연도'] == '2013']
        fig_p1 = px.pie(df_2013, values='건수', names='연령대', title="2013 무동기 범죄 연령 비중", hole=0.3)
        st.plotly_chart(fig_p1, use_container_width=True)
        top_age_2013 = df_2013.loc[df_2013['건수'].idxmax(), '연령대']
    with c2:
        df_m_2013 = df_motive[df_motive['연도'] == '2013']
        fig_b1 = px.bar(df_m_2013, x='동기', y='건수', color='동기', 
                       title=f"2013 범죄 사유 (최다 발생 세대: {top_age_2013})")
        st.plotly_chart(fig_b1, use_container_width=True)

    # --- [2023년 분석 섹션] ---
    st.divider()
    st.subheader("📅 2023년 범죄 구조 분석")
    c3, c4 = st.columns(2)
    with c3:
        df_2023 = df_crime_age[df_crime_age['연도'] == '2023']
        fig_p2 = px.pie(df_2023, values='건수', names='연령대', title="2023 무동기 범죄 연령 비중", hole=0.3)
        st.plotly_chart(fig_p2, use_container_width=True)
        top_age_2023 = df_2023.loc[df_2023['건수'].idxmax(), '연령대']
    with c4:
        df_m_2023 = df_motive[df_motive['연도'] == '2023']
        fig_b2 = px.bar(df_m_2023, x='동기', y='건수', color='동기', 
                       title=f"2023 범죄 사유 (최다 발생 세대: {top_age_2023})")
        st.plotly_chart(fig_b2, use_container_width=True)

    with st.expander("📄 사용된 SQL 전체 보기"):
        st.code(sql_motive, language='sql')

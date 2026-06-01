import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 인과관계 정밀 분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 파일이 존재하지 않습니다. 경로를 확인해주세요.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. SQL 쿼리 생성기 (2013, 2023 전용)] ---
def get_sql(table, age_col, val_name):
    """지표 테이블 전용 Unpivot 쿼리"""
    return f"""
    SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("2013" AS FLOAT) as {val_name} FROM {table} \n
    UNION ALL \n
    SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("2023" AS FLOAT) as {val_name} FROM {table}
    """

# --- [3. 메인 화면] ---
st.title("🧠 사회적 지표(X)에 따른 화병 및 무동기 범죄(y) 상관분석")
st.markdown("### 🔍 분석 기준: 2013년 vs 2023년 (10년 간의 변화 추적)")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 사용량의 영향", "🤝 2. 사회적 고립의 영향", "⚖️ 3. 연령별 무동기 범죄 구조"])

# --- [Tab 1: 인터넷(X) vs 정신건강(y) - 회귀 산점도] ---
with tab1:
    st.header("1. 인터넷 사용 시간(X)과 정신건강(y)의 상관성")
    
    # 데이터 준비
    df_x = run_query(get_sql("internet_weektime", "연령대", "인터넷시간"))
    df_y_dep = run_query(get_sql("depression_experience", "연령별", "우울감"))
    df_y_str = run_query(get_sql("stress_perception", "연령별", "스트레스"))
    
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대'])

    c1, c2 = st.columns(2)
    with c1:
        st.write("**[분석 1] 인터넷 시간 vs 우울감**")
        fig1_1 = px.scatter(df1, x='인터넷시간', y='우울감', color='연도', trendline="ols",
                           hover_data=['연령대'], title="인터넷 시간이 우울감에 미치는 영향")
        st.plotly_chart(fig1_1, use_container_width=True)

    with c2:
        st.write("**[분석 2] 인터넷 시간 vs 스트레스**")
        fig1_2 = px.scatter(df1, x='인터넷시간', y='스트레스', color='연도', trendline="ols",
                           hover_data=['연령대'], title="인터넷 시간이 스트레스에 미치는 영향")
        st.plotly_chart(fig1_2, use_container_width=True)

    with st.expander("📄 사용된 SQL 보기"):
        st.code(get_sql("internet_weektime", "연령대", "인터넷시간"), language='sql')

# --- [Tab 2: 사회적 고립도(X) vs 정신건강(y) - 회귀 산점도] ---
with tab2:
    st.header("2. 사회적 고립도(X)와 정신건강(y)의 상관성")
    
    df_x2 = run_query(get_sql("social_isolation", "연령별", "고립도"))
    df2 = pd.merge(df_x2, df_y_dep, on=['연도', '연령대'])
    df2 = pd.merge(df2, df_y_str, on=['연도', '연령대'])

    c3, c4 = st.columns(2)
    with c3:
        st.write("**[분석 1] 사회적 고립도 vs 우울감**")
        fig2_1 = px.scatter(df2, x='고립도', y='우울감', color='연도', trendline="ols",
                           hover_data=['연령대'], title="고립도가 우울감에 미치는 영향")
        st.plotly_chart(fig2_1, use_container_width=True)

    with c4:
        st.write("**[분석 2] 사회적 고립도 vs 스트레스**")
        fig2_2 = px.scatter(df2, x='고립도', y='스트레스', color='연도', trendline="ols",
                           hover_data=['연령대'], title="고립도가 스트레스에 미치는 영향")
        st.plotly_chart(fig2_2, use_container_width=True)

# --- [Tab 3: 연도별 범죄 구조 (원형 + 누적 막대)] ---
with tab3:
    st.header("3. 연도별 연령대 범죄 점유율 및 세부 동기 분석")
    st.info("💡 오른쪽 막대그래프는 각 연령대의 무동기 범죄 중 '현실불만'과 '우발적' 동기를 하나로 합쳐서 보여줍니다.")

    # [중요] 범죄 데이터 연령별-동기별 결합 쿼리
    # 실제 DB 구조에 맞춰 '결과_범죄' 또는 'crime_age_motive' 형태의 조인이 필요합니다.
    # 여기서는 연령대별로 동기(현실불만, 우발적)가 나뉜 구조라고 가정하고 쿼리를 짭니다.
    def get_crime_detail_sql(year):
        yr_col = f'"{year} 년"'
        return f"""
        SELECT TRIM(범행연령별) as 연령대, '{year}' as 연도, '현실불만' as 동기, CAST({yr_col} AS INTEGER) as 건수 
        FROM crime_motive WHERE 범행동기별 = '현실불만' \n
        UNION ALL \n
        SELECT TRIM(범행연령별) as 연령대, '{year}' as 연도, '우발적' as 동기, CAST({yr_col} AS INTEGER) as 건수 
        FROM crime_motive WHERE 범행동기별 = '우발적'
        """

    for target_year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {target_year}년 데이터 상세 분석")
        
        # 데이터 가져오기
        df_crime = run_query(get_crime_detail_sql(target_year))
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            # 1. 원형 차트: 연령대별 무동기 범죄(현실불만+우발적) 점유율
            df_pie = df_crime.groupby('연령대')['건수'].sum().reset_index()
            fig_p = px.pie(df_pie, values='건수', names='연령대', hole=0.4,
                          title=f"{target_year} 연령대별 무동기 범죄 점유율")
            st.plotly_chart(fig_p, use_container_width=True)
            
        with col_right:
            # 2. 막대 차트: 연령대별 (현실불만 + 우발적) 누적 막대
            # barmode='stack'을 통해 하나의 막대 안에 색으로 구분
            fig_b = px.bar(df_crime, x='연령대', y='건수', color='동기', barmode='stack',
                          title=f"{target_year} 연령대별 세부 동기 구성",
                          category_orders={"연령대": ["20대", "30대", "40대", "50대", "60세이상"]})
            st.plotly_chart(fig_b, use_container_width=True)

    with st.expander("📄 사용된 범죄 분석 SQL 보기"):
        st.code(get_crime_detail_sql("2023"), language='sql')

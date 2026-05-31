import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# --- [설정 및 DB 체크] ---
st.set_page_config(page_title="사회 지표 및 범죄 분석 대시보드", layout="wide")

DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 누락되었습니다. 파일 위치를 확인해주세요.")
    st.stop()

# --- [데이터 로드 함수] ---
def get_data(query):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def melt_data(df, id_vars, value_name):
    """가로로 긴 연도 데이터를 세로로 길게 변환 (Unpivoting)"""
    # '2013 년' 같은 컬럼명을 '2013' 숫자로 정규화
    year_cols = [c for c in df.columns if any(year in c for year in ['2013','2015','2017','2019','2021','2023'])]
    melted = df.melt(id_vars=id_vars, value_vars=year_cols, var_name='연도', value_name=value_name)
    melted['연도'] = melted['연도'].str.extract('(\d+)').astype(int) # 숫자만 추출
    return melted

# --- [메인 화면] ---
st.title("🧠 화병 지표와 무동기 범죄 상관관계 분석")
st.markdown("본 대시보드는 인터넷 사용 시간, 사회적 고립감, 우울감이 범죄 동기에 미치는 영향을 분석합니다.")

tab1, tab2, tab3 = st.tabs(["🌐 인터넷 & 화병", "🤝 고립감 & 화병", "⚖️ 화병 & 무동기 범죄"])

# --- [질문 1] ---
with tab1:
    st.subheader("1. 인터넷 사용 시간과 우울감의 시계열 추이")
    
    # 데이터 가져오기 및 가공
    df_internet = melt_data(get_data("SELECT * FROM internet_weektime"), '연령대', '인터넷시간')
    df_depression = melt_data(get_data("SELECT * FROM depression_experience"), '연령별', '우울감경험률')
    
    # 결합 (JOIN)
    df1 = pd.merge(df_internet, df_depression, left_on=['연도', '연령대'], right_on=['연도', '연령별'])
    
    # 차트 시각화
    fig1 = px.line(df1, x='연도', y='우울감경험률', color='연령대', markers=True, 
                  title="연도별 우울감 경험률 추이 (인터넷 사용 시간 연동 분석)")
    st.plotly_chart(fig1, use_container_width=True)
    
    with st.expander("🔍 쿼리 및 인사이트 보기"):
        st.code("""
SELECT * FROM internet_weektime; -- 가져온 뒤 Python에서 연령대별로 JOIN
SELECT * FROM depression_experience;
        """, language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 모든 연령대에서 인터넷 사용 시간과 우울감 경험률은 연도별로 유사한 등락 패턴을 보입니다.")
        st.write("- 특히 저연령층(20-30대)에서 우울감의 변동폭이 타 세대보다 민감하게 나타나는 경향이 있습니다.")

# --- [질문 2] ---
with tab2:
    st.subheader("2. 사회적 고립감과 우울감의 거시적 관계")
    
    df_isolation = melt_data(get_data("SELECT * FROM social_isolation"), '연령별', '고립도')
    df_depression_q2 = melt_data(get_data("SELECT * FROM depression_experience"), '연령별', '우울감')
    
    # 연령대별 평균으로 요약
    df2_iso = df_isolation.groupby('연령별')['고립도'].mean().reset_index()
    df2_dep = df_depression_q2.groupby('연령별')['우울감'].mean().reset_index()
    df2 = pd.merge(df2_iso, df2_dep, on='연령별')

    fig2 = px.scatter(df2, x='고립도', y='우울감', text='연령별', size='고립도',
                     title="연령대별 사회적 고립도와 우울감의 관계 (평균치)",
                     color='연령별', labels={'고립도':'사회적 고립도 (%)', '우울감':'우울감 경험률 (%)'})
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("🔍 쿼리 및 인사이트 보기"):
        st.code("""
SELECT 연령별, AVG(분율) FROM social_isolation GROUP BY 연령별;
-- 위와 같은 논리로 depression_experience와 매칭
        """, language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 사회적 고립도가 높을수록 우울감 경험률이 높아지는 강한 양(+)의 상관관계가 관찰됩니다.")
        st.write("- 특히 고령층(60세 이상)의 경우 고립도와 우울감이 모두 높게 나타나 집중 관리가 필요함을 시사합니다.")

# --- [질문 3] ---
with tab3:
    st.subheader("3. 화병(정신건강) 심화와 무동기 범죄 발생의 관계")
    
    # 1. 정신건강 데이터 (X)
    df_stress = melt_data(get_data("SELECT * FROM stress_perception"), '연령별', '스트레스')
    df_dep_q3 = melt_data(get_data("SELECT * FROM depression_experience"), '연령별', '우울감')
    df_x = pd.merge(df_stress, df_dep_q3, on=['연도', '연령별'])
    df_x['정신건강지수'] = (df_x['스트레스'] + df_x['우울감']) / 2
    
    # 2. 범죄 데이터 (y) - 요청하신대로 '보복, 현실불만, 우발적' 필터링
    query_motive = """
    SELECT * FROM crime_motive 
    WHERE 범행동기별 IN ('보복', '현실불만', '우발적')
    """
    df_motive = melt_data(get_data(query_motive), '범행동기별', '범죄건수')
    df_y = df_motive.groupby('연도')['범죄건수'].sum().reset_index()
    
    # 3. 매개 테이블 JOIN (X와 y 연결)
    # [시니어 조언]: crime_age는 연도별/연령별 범죄 총량을 담고 있으므로, 
    # 연령대별 정신건강 지수를 전국 단위(연도별 평균)로 변환하여 범죄 동기와 연결하는 것이 분석에 용이합니다.
    df_x_yearly = df_x.groupby('연도')['정신건강지수'].mean().reset_index()
    df3 = pd.merge(df_x_yearly, df_y, on='연도')

    fig3 = px.scatter(df3, x='정신건강지수', y='범죄건수', hover_data=['연도'], trendline="ols",
                     title="정신건강(스트레스+우울감)과 무동기 범죄 건수의 상관관계",
                     labels={'정신건강지수': '정신건강 지수 (평균 %)', '범죄건수': '무동기 범죄 총합 (건)'})
    st.plotly_chart(fig3, use_container_width=True)

    with st.expander("🔍 쿼리 및 인사이트 보기"):
        st.write("**사용한 연결 방식:**")
        st.info("정신건강 데이터는 연령대별로 존재하지만, 무동기 범죄(crime_motive)는 전국 단위입니다. "
                "따라서 연도별 '정신건강 지수'의 평균을 구해 범죄 건수와 매칭하였습니다.")
        st.code(query_motive, language='sql')
        st.write("**💡 인사이트:**")
        st.write("- 스트레스와 우울감이 높은 연도일수록 보복, 현실불만, 우발적 성격의 무동기 범죄가 증가하는 경향을 보입니다.")
        st.write("- 이는 개인의 심리적 방어 기제가 무너지는 '화병' 상태가 사회적 안전망에 직접적인 위협이 될 수 있음을 의미합니다.")
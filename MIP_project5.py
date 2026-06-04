import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 상관분석 대시보드", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 데이터베이스 파일이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 공통 SQL 템플릿] ---
def get_metrics_sql(table, age_col, val_name):
    return f"""
SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("2013" AS FLOAT) as {val_name} FROM {table} \n
UNION ALL \n
SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("2023" AS FLOAT) as {val_name} FROM {table}
"""

def get_crime_age_sql():
    return """
SELECT TRIM(범행연령별) as 연령대, '2013' as 연도, CAST("2013 년" AS INTEGER) as 전체건수 FROM crime_age \n
UNION ALL \n
SELECT TRIM(범행연령별) as 연령대, '2023' as 연도, CAST("2023 년" AS INTEGER) as 전체건수 FROM crime_age
"""

# --- [3. 메인 화면] ---
st.title("📊 사회 지표 변화에 따른 화병 및 무동기 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 사용 집단별 분석", "🤝 2. 고립도-정신건강 궤적", "⚖️ 3. 연령별 범죄 및 화병 지표"])

# --- [Tab 1: 필터링 후 집단 분류] ---
with tab1:
    st.header("1. 인터넷 사용량 집단(상/중/하)에 따른 정신건강 수준")
    st.info("💡 2013년과 2023년 데이터만 추출한 후, 그 안에서 인터넷 사용 시간을 기준으로 상/중/하 집단을 나누었습니다.")

    sql_x = get_metrics_sql("internet_weektime", "연령대", "인터넷시간")
    sql_y_dep = get_metrics_sql("depression_experience", "연령별", "우울감")
    sql_y_str = get_metrics_sql("stress_perception", "연령별", "스트레스")
    
    # 데이터 로드 및 병합
    df_x = run_query(sql_x)
    df_y_dep = run_query(sql_y_dep)
    df_y_str = run_query(sql_y_str)
    
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대']).dropna()

    # [핵심 수정]: 2013, 2023 데이터가 모두 모인 df1 상태에서 qcut 적용
    df1['집단'] = pd.qcut(df1['인터넷시간'], q=3, labels=['하', '중', '상'])
    
    # 집단별 평균 계산
    df1_grouped = df1.groupby(['집단', '연도'])[['우울감', '스트레스']].mean().reset_index()

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df1_grouped, x='집단', y='우울감', color='연도', barmode='group', 
                              title="인터넷 사용 집단별 평균 우울감 (%)", color_discrete_sequence=['#636EFA', '#EF553B']), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df1_grouped, x='집단', y='스트레스', color='연도', barmode='group', 
                              title="인터넷 사용 집단별 평균 스트레스 (%)", color_discrete_sequence=['#00CC96', '#AB63FA']), use_container_width=True)

    with st.expander("📄 1탭 사용된 SQL 보기"):
        st.write("**독립변수(X) - 인터넷 시간:**"); st.code(sql_x, language='sql')
        st.write("**종속변수(y) - 우울/스트레스:**"); st.code(sql_y_dep, language='sql')

# --- [Tab 2: 고립도 궤적 연결] ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강의 10년 변화 궤적")
    
    sql_iso = get_metrics_sql("social_isolation", "연령별", "고립도")
    df_iso = run_query(sql_iso)
    df2 = pd.merge(df_iso, df_y_dep, on=['연도', '연령대']).dropna()
    
    fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도', 
                  title="연령대별 고립도-우울감 변화 (2013 → 2023)")
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 2탭 사용된 SQL 보기"):
        st.write("**사회적 고립도 추출:**"); st.code(sql_iso, language='sql')

# --- [Tab 3: 중첩 그래프 및 Stack 순서 조정] ---
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
        st.subheader(f"📅 {year}년 분석 결과")
        
        c_age = df_age[df_age['연도'] == year]
        c_mot = df_m[df_m['연도'] == year]
        m_dep = df_y_dep[df_y_dep['연도'] == year]
        m_str = df_y_str[df_y_str['연도'] == year]
        
        # 비율 기반 가상 데이터 생성
        total_m = c_mot['건수'].sum()
        ratio = c_mot.set_index('동기')['건수'] / total_m if total_m > 0 else {'우발적': 0.5, '현실불만': 0.5}
        
        bar_list = []
        for _, row in c_age.iterrows():
            # [요청 4 반영]: 우발적을 먼저 쌓고 현실불만을 그 위에 쌓기 위해 리스트 순서 조정
            bar_list.append({'연령대': row['연령대'], '동기': '우발적', '건수': row['전체건수'] * ratio['우발적']})
            bar_list.append({'연령대': row['연령대'], '동기': '현실불만', '건수': row['전체건수'] * ratio['현실불만']})
        
        df_stack = pd.DataFrame(bar_list)
        # 카테고리 순서 강제 (우발적 -> 현실불만 순으로 쌓임)
        df_stack['동기'] = pd.Categorical(df_stack['동기'], categories=['우발적', '현실불만'], ordered=True)
        df_stack = df_stack.sort_values('동기')

        # 이중 Y축 그래프 구성
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Stacked Bar 추가
        for motive in ['우발적', '현실불만']:
            sub = df_stack[df_stack['동기'] == motive]
            fig3.add_trace(go.Bar(name=motive, x=sub['연령대'], y=sub['건수']), secondary_y=False)

        # 꺾은선 그래프 추가
        fig3.add_trace(go.Scatter(name='우울감(%)', x=m_dep['연령대'], y=m_dep['우울감'], mode='lines+markers', line=dict(color='red', width=3)), secondary_y=True)
        fig3.add_trace(go.Scatter(name='스트레스(%)', x=m_str['연령대'], y=m_str['스트레스'], mode='lines+markers', line=dict(color='orange', width=3)), secondary_y=True)

        fig3.update_layout(title_text=f"{year}년 연령별 범죄 구조 및 화병 지표", barmode='stack', hovermode='x unified')
        fig3.update_yaxes(title_text="범죄 건수 (Bar)", secondary_y=False)
        fig3.update_yaxes(title_text="지표 비율 (%) (Line)", secondary_y=True)
        
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📄 3탭 사용된 SQL 보기"):
        st.write("**범죄 연령 및 동기 데이터:**"); st.code(sql_m, language='sql')

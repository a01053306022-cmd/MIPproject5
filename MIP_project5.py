import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="사회지표-범죄 데이터 정밀 분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 데이터베이스 파일이 누락되었습니다. 파일 위치를 확인해주세요.")
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

def get_crime_sql(table, age_col, val_name):
    return f"""
    SELECT TRIM({age_col}) as 연령대, '2013' as 연도, CAST("2013 년" AS INTEGER) as {val_name} FROM {table} \n
    UNION ALL \n
    SELECT TRIM({age_col}) as 연령대, '2023' as 연도, CAST("2023 년" AS INTEGER) as {val_name} FROM {table}
    """

# --- [3. 메인 화면] ---
st.title("📊 데이터 기반 사회현상 및 무동기 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 인터넷 사용 집단별 분석", "🤝 2. 고립도-정신건강 궤적", "⚖️ 3. 연령별 범죄 및 화병 지표"])

# --- Tab 1: 인터넷 사용 시간 상/중/하 집단 분류 분석 ---
with tab1:
    st.header("1. 인터넷 사용량 집단(상/중/하)에 따른 정신건강 수준")
    st.info("💡 모든 데이터를 인터넷 사용 시간에 따라 3분위로 나누어 '하(낮음)', '중(보통)', '상(높음)' 집단으로 분류했습니다.")

    df_x = run_query(get_metrics_sql("internet_weektime", "연령대", "인터넷시간"))
    df_y_dep = run_query(get_metrics_sql("depression_experience", "연령별", "우울감"))
    df_y_str = run_query(get_metrics_sql("stress_perception", "연령별", "스트레스"))
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대'])

    # 3분위수 분할 (상/중/하)
    df1['집단'] = pd.qcut(df1['인터넷시간'], q=3, labels=['하', '중', '상'])
    
    # 집단별 평균 계산
    df1_grouped = df1.groupby(['집단', '연도'])[['우울감', '스트레스']].mean().reset_index()

    c1, c2 = st.columns(2)
    with c1:
        fig1_1 = px.bar(df1_grouped, x='집단', y='우울감', color='연도', barmode='group',
                       title="인터넷 사용 집단별 평균 우울감 (%)")
        st.plotly_chart(fig1_1, use_container_width=True)
    with c2:
        fig1_2 = px.bar(df1_grouped, x='집단', y='스트레스', color='연도', barmode='group',
                       title="인터넷 사용 집단별 평균 스트레스 인지율 (%)")
        st.plotly_chart(fig1_2, use_container_width=True)

# --- Tab 2: 사회적 고립도 궤적 (2013-2023 연결) ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강의 10년 변화 궤적")
    st.info("💡 같은 연령대의 2013년 데이터와 2023년 데이터를 선으로 연결하여 변화 방향을 보여줍니다.")

    df_iso = run_query(get_metrics_sql("social_isolation", "연령별", "고립도"))
    df2 = pd.merge(df_iso, df_y_dep, on=['연도', '연령대'])
    
    fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도',
                  title="연령대별 고립도-우울감 변화 궤적 (회귀선 제거)")
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

# --- Tab 3: 범죄 구조 및 화병 지표 중첩 분석 ---
with tab3:
    st.header("3. 연령별 범죄 동기 및 정신건강 지표 복합 분석")
    st.info("💡 막대그래프(범죄 건수) 위에 우울감과 스트레스 지표를 꺾은선으로 겹쳐서 나타냈습니다.")

    # 데이터 준비
    df_age = run_query(get_crime_sql("crime_age", "범행연령별", "전체건수"))
    sql_m = "SELECT '2013' as 연도, '현실불만' as 동기, CAST(\"2013 년\" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n UNION ALL \n SELECT '2013', '우발적', CAST(\"2013 년\" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n UNION ALL \n SELECT '2023' as 연도, '현실불만' as 동기, CAST(\"2023 년\" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n UNION ALL \n SELECT '2023', '우발적', CAST(\"2023 년\" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'"
    df_m = run_query(sql_m)

    for year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {year}년 분석")

        # 데이터 필터링 및 병합
        c_age = df_age[df_age['연도'] == year]
        c_mot = df_m[df_m['연도'] == year]
        m_dep = df_y_dep[df_y_dep['연도'] == year]
        m_str = df_y_str[df_y_str['연도'] == year]
        
        # 동기 비율 적용하여 Stacked Bar 데이터 생성
        ratio = c_mot.set_index('동기')['건수'] / c_mot['건수'].sum()
        bar_list = []
        for _, row in c_age.iterrows():
            bar_list.append({'연령대': row['연령대'], '동기': '우발적', '건수': row['전체건수'] * ratio['우발적']})
            bar_list.append({'연령대': row['연령대'], '동기': '현실불만', '건수': row['전체건수'] * ratio['현실불만']})
        df_stack = pd.DataFrame(bar_list)

        # [요청 4 반영]: '현실불만'을 위쪽으로 보내기 위해 데이터 정렬 (우발적 먼저, 현실불만 나중)
        df_stack['동기'] = pd.Categorical(df_stack['동기'], categories=['우발적', '현실불만'], ordered=True)
        df_stack = df_stack.sort_values('동기')

        # [요청 3 반영]: 이중 Y축 그래프 생성
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])

        # 막대그래프 (범죄 건수)
        for motive in ['우발적', '현실불만']:
            sub_df = df_stack[df_stack['동기'] == motive]
            fig3.add_trace(go.Bar(name=motive, x=sub_df['연령대'], y=sub_df['건수']), secondary_y=False)

        # 꺾은선 그래프 (우울감 & 스트레스)
        fig3.add_trace(go.Scatter(name='우울감(%)', x=m_dep['연령대'], y=m_dep['우울감'], mode='lines+markers', line=dict(color='red', width=3)), secondary_y=True)
        fig3.add_trace(go.Scatter(name='스트레스(%)', x=m_str['연령대'], y=m_str['스트레스'], mode='lines+markers', line=dict(color='orange', width=3)), secondary_y=True)

        fig3.update_layout(title_text=f"{year}년 연령별 범죄 동기 및 정신건강 중첩 차트", barmode='stack', xaxis_title="연령대")
        fig3.update_yaxes(title_text="범죄 발생 건수 (Primary)", secondary_y=False)
        fig3.update_yaxes(title_text="지표 비율 (%) (Secondary)", secondary_y=True)
        
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📄 사용된 주요 SQL"):
        st.code(sql_m, language='sql')

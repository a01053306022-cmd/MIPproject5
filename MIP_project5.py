import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- [1. 기본 설정 및 DB 체크] ---
st.set_page_config(page_title="화병-범죄 연령별 상관분석", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 데이터베이스 파일이 누락되었습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 데이터 전처리: 연령대 명칭 표준화 함수] ---
def standardize_age(df, col='연령대'):
    """DB의 다양한 연령대 명칭을 사용자가 요청한 5개 카테고리로 통일 및 필터링"""
    mapping = {
        '19-29세': '20대', '20대': '20대',
        '30-39세': '30대', '30대': '30대',
        '40-49세': '40대', '40대': '40대',
        '50-59세': '50대', '50대': '50대',
        '60세이상': '60세 이상', '60세 이상': '60세 이상', '70세이상': '60세 이상'
    }
    df[col] = df[col].map(mapping)
    # 요청하신 5개 카테고리만 남기고 삭제 (60대 등 제외)
    target_ages = ["20대", "30대", "40대", "50대", "60세 이상"]
    df = df[df[col].isin(target_ages)]
    return df

# 가로축 순서 정의
AGE_ORDER = ["20대", "30대", "40대", "50대", "60세 이상"]

# --- [3. 공통 SQL 템플릿] ---
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

# --- [4. 메인 화면] ---
st.title("🧠 세대별 사회 지표 및 무동기 범죄 상관분석")
st.markdown("### 🔍 대상: 20대, 30대, 40대, 50대, 60세 이상 (2013 vs 2023)")

# 데이터 미리 로드 및 전처리 (캐싱 효과)
df_x = standardize_age(run_query(get_metrics_sql("internet_weektime", "연령대", "인터넷시간")))
df_y_dep = standardize_age(run_query(get_metrics_sql("depression_experience", "연령별", "우울감")))
df_y_str = standardize_age(run_query(get_metrics_sql("stress_perception", "연령별", "스트레스")))
df_iso = standardize_age(run_query(get_metrics_sql("social_isolation", "연령별", "고립도")))

tab1, tab2, tab3 = st.tabs(["🌐 1. 연령별 인터넷 & 정신건강", "🤝 2. 고립도-정신건강 궤적", "⚖️ 3. 연령별 범죄 및 화병 지표"])

# --- Tab 1 ---
with tab1:
    st.header("1. 연령대별 인터넷 사용량과 정신건강 지표의 변화")
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대'])
    df1 = pd.merge(df1, df_y_str, on=['연도', '연령대']).dropna()
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(df1, x='연령대', y='우울감', color='연도', barmode='group',
                              title="연령대별 우울감 경험률 (%)", category_orders={"연령대": AGE_ORDER}), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(df1, x='연령대', y='스트레스', color='연도', barmode='group',
                              title="연령대별 스트레스 인지율 (%)", category_orders={"연령대": AGE_ORDER}), use_container_width=True)

    with st.expander("📄 1탭 SQL 보기"):
        st.code(get_metrics_sql("internet_weektime", "연령대", "인터넷시간"), language='sql')

# --- Tab 2 ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강의 10년 변화 궤적")
    df2 = pd.merge(df_iso, df_y_dep, on=['연도', '연령대']).dropna()
    fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도',
                  title="연령대별 고립도-우울감 상관 궤적", category_orders={"연령대": AGE_ORDER})
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("📄 2탭 SQL 보기"):
        st.code(get_metrics_sql("social_isolation", "연령별", "고립도"), language='sql')

# --- Tab 3 ---
with tab3:
    st.header("3. 연령별 범죄 동기 및 정신건강 지표 복합 분석")

    df_age_base = standardize_age(run_query(get_crime_age_sql()))
    sql_m = """
SELECT '2013' as 연도, '현실불만' as 동기, CAST("2013 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n
UNION ALL \n
SELECT '2013', '우발적', CAST("2013 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' \n
UNION ALL \n
SELECT '2023' as 연도, '현실불만' as 동기, CAST("2023 년" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' \n
UNION ALL \n
SELECT '2023', '우발적', CAST("2023 년" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'
"""
    df_m = run_query(sql_m) # 동기 데이터는 전연령 합계이므로 매핑 생략

    for year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {year}년 분석 결과")
        
        c_age = df_age_base[df_age_base['연도'] == year]
        c_mot = df_m[df_m['연도'] == year]
        m_dep = df_y_dep[df_y_dep['연도'] == year]
        m_str = df_y_str[df_y_str['연도'] == year]
        
        total_m = c_mot['건수'].sum()
        ratio = c_mot.set_index('동기')['건수'] / total_m if total_m > 0 else {'우발적': 0.5, '현실불만': 0.5}
        
        bar_list = []
        for _, row in c_age.iterrows():
            # [순서 보장]: 우발적을 먼저 넣고 현실불만을 나중에 넣어 현실불만이 위로 가게 함
            bar_list.append({'연령대': row['연령대'], '동기': '우발적', '건수': row['전체건수'] * ratio['우발적']})
            bar_list.append({'연령대': row['연령대'], '동기': '현실불만', '건수': row['전체건수'] * ratio['현실불만']})
        
        df_stack = pd.DataFrame(bar_list)
        df_stack['동기'] = pd.Categorical(df_stack['동기'], categories=['우발적', '현실불만'], ordered=True)
        df_stack = df_stack.sort_values('동기')

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        for motive in ['우발적', '현실불만']:
            sub = df_stack[df_stack['동기'] == motive]
            fig3.add_trace(go.Bar(name=motive, x=sub['연령대'], y=sub['건수']), secondary_y=False)

        fig3.add_trace(go.Scatter(name='우울감(%)', x=m_dep['연령대'], y=m_dep['우울감'], mode='lines+markers', line=dict(color='red', width=3)), secondary_y=True)
        fig3.add_trace(go.Scatter(name='스트레스(%)', x=m_str['연령대'], y=m_str['스트레스'], mode='lines+markers', line=dict(color='orange', width=3)), secondary_y=True)

        fig3.update_layout(title_text=f"{year}년 연령별 범죄 구조 및 화병 지표", barmode='stack', category_orders={"연령대": AGE_ORDER})
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📄 3탭 SQL 보기"):
        st.code(sql_m, language='sql')

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- [1. 기본 설정] ---
st.set_page_config(page_title="화병-범죄 상관분석 최종본", layout="wide")
DB_FILE = 'MIP_project5.db'

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ '{DB_FILE}' 데이터베이스 파일이 없습니다.")
    st.stop()

def run_query(q):
    with sqlite3.connect(DB_FILE) as conn:
        return pd.read_sql(q, conn)

# --- [2. 데이터 전처리 핵심 함수] ---
def standardize_age_final(df, col='연령대'):
    """DB 명칭을 사용자 요청 5개 카테고리로 강제 변환 및 기타 제거"""
    # 공백 제거 및 텍스트 표준화
    df[col] = df[col].astype(str).str.strip()
    
    # 매핑 딕셔너리 (DB에 존재 가능한 모든 패턴 대응)
    mapping = {
        '19-29세': '20대', '20대': '20대', '19~29세': '20대',
        '30-39세': '30대', '30대': '30대', '30~39세': '30대',
        '40-49세': '40대', '40대': '40대', '40~49세': '40대',
        '50-59세': '50대', '50대': '50대', '50~59세': '50대',
        '60세이상': '60세 이상', '60세 이상': '60세 이상', '70세이상': '60세 이상', '60-69세': '60세 이상'
    }
    df[col] = df[col].map(mapping)
    
    # 요청하신 5개 카테고리만 필터링
    target_ages = ["20대", "30대", "40대", "50대", "60세 이상"]
    df = df[df[col].isin(target_ages)].copy()
    
    # 순서 고정
    df[col] = pd.Categorical(df[col], categories=target_ages, ordered=True)
    return df.sort_values(col)

AGE_ORDER = ["20대", "30대", "40대", "50대", "60세 이상"]

# --- [3. SQL 템플릿] ---
def get_metrics_sql(table, age_col, val_name):
    return f"SELECT {age_col} as 연령대, '2013' as 연도, CAST(\"2013\" AS FLOAT) as {val_name} FROM {table} UNION ALL SELECT {age_col} as 연령대, '2023' as 연도, CAST(\"2023\" AS FLOAT) as {val_name} FROM {table}"

def get_crime_age_sql():
    return "SELECT 범행연령별 as 연령대, '2013' as 연도, CAST(\"2013 년\" AS INTEGER) as 전체건수 FROM crime_age UNION ALL SELECT 범행연령별 as 연령대, '2023' as 연도, CAST(\"2023 년\" AS INTEGER) as 전체건수 FROM crime_age"

# --- [4. 데이터 로드 및 초기 정제] ---
try:
    df_x = standardize_age_final(run_query(get_metrics_sql("internet_weektime", "연령대", "인터넷시간")))
    df_y_dep = standardize_age_final(run_query(get_metrics_sql("depression_experience", "연령별", "우울감")))
    df_y_str = standardize_age_final(run_query(get_metrics_sql("stress_perception", "연령별", "스트레스")))
    df_iso = standardize_age_final(run_query(get_metrics_sql("social_isolation", "연령별", "고립도")))
    df_age_base = standardize_age_final(run_query(get_crime_age_sql()))
except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
    st.stop()

# --- [5. 메인 화면 구성] ---
st.title("🧠 세대별 사회 지표 및 무동기 범죄 상관분석")

tab1, tab2, tab3 = st.tabs(["🌐 1. 연령별 인터넷 & 정신건강", "🤝 2. 고립도-정신건강 궤적", "⚖️ 3. 연령별 범죄 및 화병 지표"])

# --- Tab 1 ---
with tab1:
    st.header("1. 연령대별 인터넷 사용량과 정신건강 지표")
    df1 = pd.merge(df_x, df_y_dep, on=['연도', '연령대']).merge(df_y_str, on=['연도', '연령대']).dropna()
    
    if not df1.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.bar(df1, x='연령대', y='우울감', color='연도', barmode='group', title="연령대별 우울감 (%)", category_orders={"연령대": AGE_ORDER}), use_container_width=True)
        c2.plotly_chart(px.bar(df1, x='연령대', y='스트레스', color='연도', barmode='group', title="연령대별 스트레스 (%)", category_orders={"연령대": AGE_ORDER}), use_container_width=True)
    else:
        st.warning("표시할 데이터가 없습니다.")

# --- Tab 2 ---
with tab2:
    st.header("2. 사회적 고립도와 정신건강 변화 궤적")
    df2 = pd.merge(df_iso, df_y_dep, on=['연도', '연령대']).dropna()
    
    if not df2.empty:
        fig2 = px.line(df2, x='고립도', y='우울감', color='연령대', markers=True, text='연도', title="연령대별 고립도-우울감 궤적")
        fig2.update_traces(textposition='top center')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("표시할 데이터가 없습니다.")

# --- Tab 3 ---
with tab3:
    st.header("3. 연령별 범죄 동기 및 정신건강 지표 중첩 분석")
    
    sql_m = "SELECT '2013' as 연도, '현실불만' as 동기, CAST(\"2013 년\" AS INTEGER) as 건수 FROM crime_motive WHERE 범행동기별 = '현실불만' UNION ALL SELECT '2013', '우발적', CAST(\"2013 년\" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적' UNION ALL SELECT '2023', '현실불만', CAST(\"2023 년\" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '현실불만' UNION ALL SELECT '2023', '우발적', CAST(\"2023 년\" AS INTEGER) FROM crime_motive WHERE 범행동기별 = '우발적'"
    df_m = run_query(sql_m)

    for year in ['2013', '2023']:
        st.divider()
        st.subheader(f"📅 {year}년 분석 결과")
        
        c_age = df_age_base[df_age_base['연도'] == year]
        c_mot = df_m[df_m['연도'] == year]
        m_dep = df_y_dep[df_y_dep['연도'] == year]
        m_str = df_y_str[df_y_str['연도'] == year]
        
        if c_age.empty or c_mot.empty:
            st.warning(f"{year}년 범죄 데이터가 부족합니다.")
            continue

        total_m = c_mot['건수'].sum()
        ratio = c_mot.set_index('동기')['건수'] / total_m if total_m > 0 else {'우발적': 0.5, '현실불만': 0.5}
        
        # Stacked Bar용 데이터 재구성
        bar_data = []
        for age in AGE_ORDER:
            age_total = c_age[c_age['연령대'] == age]['전체건수'].sum()
            bar_data.append({'연령대': age, '동기': '우발적', '건수': age_total * ratio.get('우발적', 0.5)})
            bar_data.append({'연령대': age, '동기': '현실불만', '건수': age_total * ratio.get('현실불만', 0.5)})
        
        df_stack = pd.DataFrame(bar_data)
        df_stack['동기'] = pd.Categorical(df_stack['동기'], categories=['우발적', '현실불만'], ordered=True)
        
        # 이중 축 차트 생성
        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar 추가 (우발적 먼저, 현실불만 나중)
        for mot in ['우발적', '현실불만']:
            sub = df_stack[df_stack['동기'] == mot]
            fig3.add_trace(go.Bar(name=mot, x=sub['연령대'], y=sub['건수']), secondary_y=False)
            
        # Line 추가
        fig3.add_trace(go.Scatter(name='우울감(%)', x=m_dep['연령대'], y=m_dep['우울감'], mode='lines+markers', line=dict(color='red')), secondary_y=True)
        fig3.add_trace(go.Scatter(name='스트레스(%)', x=m_str['연령대'], y=m_str['스트레스'], mode='lines+markers', line=dict(color='orange')), secondary_y=True)

        fig3.update_layout(title_text=f"{year}년 복합 분석", barmode='stack', xaxis={'categoryorder':'array', 'categoryarray':AGE_ORDER})
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📄 사용된 SQL 보기"):
        st.code(sql_m, language='sql')

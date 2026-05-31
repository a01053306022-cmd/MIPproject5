import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# 1. 데이터베이스 연결 설정
DB_PATH = "MIP_project5.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

# 화면 설정
st.set_page_config(page_title="공공데이터 분석 대시보드", layout="wide")

# 2. DB 파일 존재 확인
if not os.path.exists(DB_PATH):
    st.error("🚨 데이터베이스 파일(MIP_project5.db)이 누락되었습니다. 파일 위치를 확인해주세요.")
    st.stop()

st.title("📊 사회적 지표와 범죄 동기 분석 대시보드")
st.markdown("인터넷 사용량, 우울감, 사회적 고립도가 범죄와 어떤 관계가 있는지 탐색합니다.")

# 탭 구성
tab1, tab2, tab3 = st.tabs([
    "인터넷 vs 우울감", 
    "사회적 고립 vs 우울감", 
    "우울감 vs 무동기 범죄"
])

# --- 탭 1: 인터넷 사용 시간과 우울감의 추이 ---
with tab1:
    st.header("1. 인터넷 사용 시간과 우울감의 추이")
    
    # 조인 조건 컬럼명 수정 (a.연령대 = b.연령별)
    query1 = """
    SELECT a.연령대, '2013' as 연도, a."2013" as 인터넷시간, b."2013" as 우울감비율 FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL
    SELECT a.연령대, '2015', a."2015", b."2015" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL
    SELECT a.연령대, '2017', a."2017", b."2017" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL
    SELECT a.연령대, '2019', a."2019", b."2019" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL
    SELECT a.연령대, '2021', a."2021", b."2021" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL
    SELECT a.연령대, '2023', a."2023", b."2023" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    """
    
    conn = get_connection()
    df1 = pd.read_sql(query1, conn)
    conn.close()
    
    # 데이터 형변환 (숫자가 아닌 경우 대비)
    df1['인터넷시간'] = pd.to_numeric(df1['인터넷시간'], errors='coerce')
    df1['우울감비율'] = pd.to_numeric(df1['우울감비율'], errors='coerce')
    
    fig1 = px.line(df1, x="연도", y="인터넷시간", color="연령대", markers=True, title="연령대별 인터넷 사용 시간 변화")
    st.plotly_chart(fig1, use_container_width=True)
    
    fig1_2 = px.bar(df1, x="연도", y="우울감비율", color="연령대", barmode="group", title="연령대별 우울감 경험률 변화")
    st.plotly_chart(fig1_2, use_container_width=True)

# --- 탭 2: 사회적 고립도와 우울감 (수정됨) ---
with tab2:
    st.header("2. 사회적 고립도와 우울감의 상관관계")
    
    # 컬럼명 수정: 연령대 -> 연령별, 고립도_비율 -> "2023"
    # 종류 = '전체' 조건 추가 (중복 방지)
    query2 = """
    SELECT a.연령별 as 연령대, a."2023" as 고립도_비율, b."2023" as 우울감비율
    FROM social_isolation a
    JOIN depression_experience b ON a.연령별 = b.연령별
    WHERE a.종류 = '전체'
    """
    
    conn = get_connection()
    df2 = pd.read_sql(query2, conn)
    conn.close()
    
    # 수치형 변환
    df2['고립도_비율'] = pd.to_numeric(df2['고립도_비율'], errors='coerce')
    df2['우울감비율'] = pd.to_numeric(df2['우울감비율'], errors='coerce')
    
    fig2 = px.scatter(df2, x="고립도_비율", y="우울감비율", text="연령대", size="고립도_비율", 
                     color="연령대", title="사회적 고립도 vs 우울감 경험률 (2023)")
    fig2.update_traces(textposition='top center')
    st.plotly_chart(fig2, use_container_width=True)

# --- 탭 3: 범죄 동기 분석 (수정됨) ---
with tab3:
    st.header("3. 우발적/무동기 범죄 분석")
    
    # offender_motive 테이블 컬럼명 반영: 범행동기별, "2023 년"
    # 이 테이블에는 연령 정보가 없으므로 연령대 조인을 제거하고 전체 비중을 보여줍니다.
    query3 = """
    SELECT 
        범행동기별 as 범행동기, 
        범죄별 as 범죄유형, 
        SUM(CAST(REPLACE("2023 년", ',', '') AS INTEGER)) as 총_인원수
    FROM offender_motive 
    WHERE 범행동기별 IN ('우발적', '현실불만', '기타(무동기 등)')
    GROUP BY 범행동기별, 범죄별
    """
    
    conn = get_connection()
    df3 = pd.read_sql(query3, conn)
    conn.close()
    
    fig3 = px.bar(df3, x="범행동기", y="총_인원수", color="범죄유형", 
                 title="2023년 주요 범행동기별 범죄 현황",
                 labels={"총_인원수": "피의자 인원수"})
    st.plotly_chart(fig3, use_container_width=True)
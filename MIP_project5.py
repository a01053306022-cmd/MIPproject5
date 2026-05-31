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

if not os.path.exists(DB_PATH):
    st.error(f"🚨 데이터베이스 파일('{DB_PATH}')이 없습니다.")
    st.stop()

st.title("📊 사회적 지표와 범죄 동기 분석 대시보드")

tab1, tab2, tab3 = st.tabs([
    "인터넷 vs 우울감", 
    "사회적 고립 vs 우울감", 
    "우울감 vs 무동기 범죄"
])

conn = get_connection()

# --- 탭 1: 인터넷 사용 시간과 우울감 (홀수년도 표시) ---
with tab1:
    st.header("1. 연령대별 주요 지표 변화 (홀수년도 중심)")
    
    # 2013년부터 2023년까지 홀수년도 위주로 구성 (2013, 2015, 2017, 2019, 2021, 2023)
    query1 = """
    SELECT a.연령대, '2013' as 연도, a."2013" as 인터넷시간, b."2013" as 우울감비율 FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL SELECT a.연령대, '2015', a."2015", b."2015" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL SELECT a.연령대, '2017', a."2017", b."2017" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL SELECT a.연령대, '2019', a."2019", b."2019" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL SELECT a.연령대, '2021', a."2021", b."2021" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    UNION ALL SELECT a.연령대, '2023', a."2023", b."2023" FROM internet_weektime a JOIN depression_experience b ON a.연령대 = b.연령별
    """
    df1 = pd.read_sql(query1, conn)
    df1['인터넷시간'] = pd.to_numeric(df1['인터넷시간'], errors='coerce')
    df1['우울감비율'] = pd.to_numeric(df1['우울감비율'], errors='coerce')
    
    # X축을 카테고리로 지정하여 홀수년도만 정확히 표시되도록 함
    fig1 = px.line(df1, x="연도", y="인터넷시간", color="연령대", markers=True, title="연령대별 인터넷 사용 시간 (홀수년도)")
    fig1.update_xaxes(type='category')
    st.plotly_chart(fig1, use_container_width=True)
    
    fig1_2 = px.bar(df1, x="연도", y="우울감비율", color="연령대", barmode="group", title="연령대별 우울감 경험률 (홀수년도)")
    fig1_2.update_xaxes(type='category')
    st.plotly_chart(fig1_2, use_container_width=True)

# --- 탭 2: 사회적 고립도와 우울감 (데이터 출력 문제 해결) ---
with tab2:
    st.header("2. 사회적 고립도와 우울감의 상관관계")
    
    # 데이터가 뜨지 않는 문제를 해결하기 위해 JOIN 조건을 확인하고 '종류' 필터를 제거하거나 수정
    # 만약 '전체'가 없다면 첫 번째 나타나는 종류를 가져오도록 함
    df_social_all = pd.read_sql("SELECT * FROM social_isolation", conn)
    df_dep_all = pd.read_sql("SELECT 연령별, \"2023\" as 우울감 FROM depression_experience", conn)
    
    # 종류 중 하나를 선택 (이미지상 종류 컬럼이 있으므로 첫 번째 값으로 시도)
    available_types = df_social_all['종류'].unique()
    target_type = '전체' if '전체' in available_types else available_types[0]
    
    df_social_sub = df_social_all[df_social_all['종류'] == target_type][['연령별', '2023']]
    df_social_sub.columns = ['연령별', '고립도']
    
    # 두 데이터 병합
    df2 = pd.merge(df_social_sub, df_dep_all, on='연령별')
    df2['고립도'] = pd.to_numeric(df2['고립도'], errors='coerce')
    df2['우울감'] = pd.to_numeric(df2['우울감'], errors='coerce')

    if df2.empty:
        st.warning("데이터 병합 결과가 비어있습니다. DB의 '연령별' 값이 일치하는지 확인이 필요합니다.")
        st.write("사회적고립 연령 예시:", df_social_sub['연령별'].unique()[:3])
        st.write("우울감경험 연령 예시:", df_dep_all['연령별'].unique()[:3])
    else:
        fig2 = px.scatter(df2, x="고립도", y="우울감", text="연령별", size="고립도", 
                         color="연령별", title=f"사회적 고립도 vs 우울감 ({target_type} 기준, 2023)")
        st.plotly_chart(fig2, use_container_width=True)

# --- 탭 3: 범죄 분석 (차트 형식 변경) ---
with tab3:
    st.header("3. 범죄유형별 범행동기 분석")
    
    query3 = """
    SELECT 
        범죄별 as 범죄유형,
        범행동기별 as 범행동기, 
        SUM(CAST(REPLACE("2023 년", ',', '') AS INTEGER)) as 피의자수
    FROM offender_motive 
    WHERE 범행동기별 IN ('우발적', '현실불만', '기타(무동기 등)')
    GROUP BY 범죄유형, 범행동기
    """
    df3 = pd.read_sql(query3, conn)
    
    # 요청사항: 범죄유형을 가로축(X), 범죄동기로 색상(Color) 구분
    fig3 = px.bar(df3, 
                 x="범죄유형", 
                 y="피의자수", 
                 color="범행동기", 
                 title="2023년 범죄유형별 동기 분포 (누적 막대)",
                 barmode="stack") # 막대 일정 부분을 색칠하는 형태
                 
    st.plotly_chart(fig3, use_container_width=True)

conn.close()
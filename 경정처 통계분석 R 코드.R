# ============================================
# 0. 데이터 로드: db 파일 불러오기
# ============================================

# getwd()
# setwd("C:/Main/Sookmyung 3rd/경영정보처리론/경정처 팀플/upload")

library(readr)
library(DBI)
library(RSQLite)

con <- dbConnect(RSQLite::SQLite(), "MIP_project5.db")
dbListTables(con)

crime_age <- dbReadTable(con, "crime_age")
crime_motive <- dbReadTable(con, "crime_motive")
depression_experience <- dbReadTable(con, "depression_experience")
internet_weektime <- dbReadTable(con, "internet_weektime")
social_isolation <- dbReadTable(con, "social_isolation")
stress_perception <- dbReadTable(con, "stress_perception")

dbDisconnect(con)

# ============================================
# 1. 피어슨 상관분석
# ============================================

library(tidyr)
library(dplyr)

# Wide -> Long Format 변환 (연도 컬럼을 하나로 통합)
iso_long <- social_isolation %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "isolation")
dep_long <- depression_experience %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "depression")
net_long <- internet_weektime %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "internet")
str_long <- stress_perception %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "stress")

names(net_long)[names(net_long) == "연령대"] <- "연령별"

# 두 데이터 결합
df_iso_dep <- inner_join(iso_long, dep_long, by = c("연령별", "year"))
df_iso_str <- inner_join(iso_long, str_long, by = c("연령별", "year"))
df_net_dep <- inner_join(net_long, dep_long, by = c("연령별", "year"))
df_net_str <- inner_join(net_long, str_long, by = c("연령별", "year"))

# 상관분석 실시
cor_result1 <- cor.test(df_iso_dep$isolation, df_iso_dep$depression, method = "pearson")
summary(lm(depression ~ isolation, data = df_iso_dep))   # p-value = 0.4903

cor_result2 <- cor.test(df_iso_str$isolation, df_iso_str$stress, method = "pearson")
summary(lm(stress ~ isolation, data = df_iso_str))   # p-value = 1.294e-10

cor_result3 <- cor.test(df_net_dep$internet, df_net_dep$depression, method = "pearson")
summary(lm(depression ~ internet, data = df_net_dep))   # p-value = 0.298

cor_result4 <- cor.test(df_net_str$internet, df_net_str$stress, method = "pearson")
summary(lm(stress ~ internet, data = df_net_str))   # p-value = 1.761e-06

merged_df <- inner_join(iso_long, dep_long, by = c("연령별", "year"))

# 시각화 (전체 데이터 산점도 + 회귀선)
# plot(merged_df$isolation, merged_df$depression, main="고립도 vs 우울감 (전 연령/전 연도)")
# abline(lm(depression ~ isolation, data=merged_df), col="blue")

# ============================================
# 2. 독립성 검정
# ============================================

# 위에서 만든 merged_df 활용 (스트레스-우울감 통합 데이터라고 가정)
# 수치 데이터를 고/저 범주형으로 변환
merged_df$stress_cat <- ifelse(merged_df$isolation > median(merged_df$isolation), "High", "Low")
merged_df$dep_cat <- ifelse(merged_df$depression > median(merged_df$depression), "High", "Low")

# 교차표(Contingency Table) 생성
table_2x2 <- table(merged_df$stress_cat, merged_df$dep_cat)
print(table_2x2)

# 카이제곱 검정
chi_result <- chisq.test(table_2x2)
print(chi_result)   # p-value = 0.7144

# ============================================
# 3. 단순 선형 회귀 분석
# ============================================

# 선형 회귀 모델 생성
lm_model <- lm(depression ~ isolation, data = df_iso_dep)
# 결과 리포트 (P-value와 결정계수 R-squared 확인)
summary(lm_model)   # p-value = 0.4903
                    # R-squared = 0.01715

lm_1_2 <- lm(stress ~ internet, data = df_net_str)
summary(lm_1_2)   # p-value = 1.761e-06
                  # R-squared = 0.5637

lm_1_3 <- lm(stress ~ isolation, data = df_iso_str)
summary(lm_1_3)   # p-value = 1.294e-10
                  # R-squared = 0.7766

lm_1_4 <- lm(depression ~ internet, data = df_net_dep)
summary(lm_1_4)   # p-value = 0.298
                  # R-squared = 0.03861

# 결과 해석 팁: 
# - Estimate(기울기): 고립도 1단위 증가 시 우울감 증가량
# - Pr(>|t|): 0.05보다 작으면 통계적으로 유의미함
# - Adjusted R-squared: 모델의 설명력 (1에 가까울수록 정확함)

# ============================================
# 0. 데이터 중간 가공
# ============================================

# 1. 모든 데이터 Long Format 변환 및 컬럼명 통일
# 정신건강 지표
str_long <- stress_perception %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "stress")
dep_long <- depression_experience %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "depression")

# 범죄 지표 (crime_age 테이블 사용 - 연령별 범죄 건수)
crime_long <- crime_age %>% pivot_longer(cols = starts_with("X"), names_to = "year", values_to = "crime_count")
crime_long$year <- gsub("\\.년", "", crime_long$year)

# 컬럼명 통일 (연령대 -> 연령별)
names(str_long)[1] <- "age_group"
names(dep_long)[1] <- "age_group"
names(crime_long)[1] <- "age_group"

# 2. 하나의 데이터프레임으로 통합 (분석용 통합 데이터)
df_final <- str_long %>%
  inner_join(dep_long, by = c("age_group", "year")) %>%
  inner_join(crime_long, by = c("age_group", "year"))

# 불필요한 '전체' 데이터가 있다면 제거 (분석 왜곡 방지)
df_final <- df_final %>% filter(!grepl("합계|전체", age_group))

# ============================================
# 4. 다중 선형 회귀 분석
# ============================================

# 다중 회귀 분석 실시
final_lm_model <- lm(crime_count ~ stress + depression, data = df_final)

# 결과 리포트
summary(final_lm_model)   # p-value = 0.786(stress), 0.007(depression), 0.02104(모델)
                          # Adjusted R-squard = 0.1931 (모델 설명력)

# depression의 estimate: -18238.9 = 우울감 경험률이 1% 증가할 때마다 범죄 건수가 18,239건 감소
# --> 무기력증 의심 OR 범죄율이 낮은 노인층의 영향일 수 있음

# ============================================
# 5. 스피어먼 서열 상관분석
# ============================================

# 2023년도 데이터만 뽑아서 연령대별 경향성 확인
df_2023 <- df_final %>% filter(year == "X2023")

# 스피어먼 상관계수 산출
spearman_result <- cor.test(df_2023$stress, df_2023$crime_count, method = "spearman")

# 결과 출력
print(spearman_result)

# p-value = 0.5167로 유의하지 않음
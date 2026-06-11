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
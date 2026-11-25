# Verification en R des tests H1 et H2 (a comparer avec results_tests_h1_h2.xlsx)
# install.packages(c("survival","fixest","sandwich","lmtest"))
library(survival); library(fixest); library(sandwich); library(lmtest)
setwd("~/Desktop/wayback/6_analysis")
d <- read.csv("analysis_data.csv")
ctrl <- grep("_b$", names(d), value = TRUE)

# ---- Descriptif : co-occurrence observee vs attendue ----
d$periode <- cut(d$annee, c(1995,2005,2010,2015,2020,2025))
aggregate(cbind(L, C, LC = L*C) ~ periode, d, mean)   # attendue = L*C (moyennes) ; ratio = LC / (L*C)

# ---- H1 : logit conditionnel (effets fixes firme) ----
h1   <- clogit(C ~ L + log_mots + annee_c + strata(id), data = d, method = "exact")
h1c  <- clogit(as.formula(paste("C ~ L + log_mots + annee_c +", paste(ctrl, collapse = "+"), "+ strata(id)")), data = d, method = "exact")
h1i  <- clogit(L ~ C + log_mots + annee_c + strata(id), data = d, method = "exact")      # inverse
summary(h1)$coefficients["L", ]; summary(h1c)$coefficients["L", ]; summary(h1i)$coefficients["C", ]
# Robustesse : probabilite lineaire a EF firme, ET groupees
summary(feols(C ~ L + log_mots + annee_c | id, data = d, cluster = ~id))
# Robustesse : logit sans EF, ET groupees par firme
lg <- glm(C ~ L + log_mots + annee_c, data = d, family = binomial)
coeftest(lg, vcov = vcovCL(lg, cluster = ~id))
# Exploratoire : interaction L x annee
summary(clogit(C ~ L + L:annee_c + log_mots + annee_c + strata(id), data = d, method = "exact"))$coefficients

# ---- H2 : Poisson a EF firme, exposition = log(mots), ET groupees ----
summary(fepois(long_explicite ~ annee_c | id, data = d, offset = ~log_mots, cluster = ~id))
summary(fepois(as.formula(paste("long_explicite ~ annee_c +", paste(ctrl, collapse = "+"), "| id")), data = d, offset = ~log_mots, cluster = ~id))
summary(fepois(court_explicite ~ annee_c | id, data = d, offset = ~log_mots, cluster = ~id))   # descriptif

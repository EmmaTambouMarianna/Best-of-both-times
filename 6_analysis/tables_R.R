# =====================================================================
# Tables (English): 1) descriptives & correlations, 2) evolution by
# period, 3) H1, 4) H2.  Word files + HTML saved in 6_analysis.
# Install once (single line in the console):
#   install.packages(c("survival","fixest","sandwich","modelsummary","flextable"))
# =====================================================================
library(survival); library(fixest); library(sandwich)
library(modelsummary); library(flextable)
set_flextable_defaults(font.family = "Times New Roman", font.size = 10)
tnr <- function(ft) font(ft, fontname = "Times New Roman", part = "all")
setwd("~/Desktop/wayback/6_analysis")
d <- read.csv("analysis_data.csv")
serv <- grep("^serv_.*_b$", names(d), value = TRUE)          # 13 service categories
out <- "tables/en/"; dir.create(out, recursive = TRUE, showWarnings = FALSE)
stars_set <- c("*" = .05, "**" = .01, "***" = .001)

# ---------------------------------------------------------------------
# Table 4. Descriptive statistics and correlations
# ---------------------------------------------------------------------
v <- c(L = "1. Long-term marker (presence)", C = "2. Short-term marker (presence)",
       long_explicite = "3. Long-term markers (count)", court_explicite = "4. Short-term markers (count)",
       log_mots = "5. Page length (log words)", annee = "6. Year",
       serv_durabilite_b = "7. Sustainability services")
x <- d[names(v)]
r <- round(cor(x), 2); r[upper.tri(r, diag = TRUE)] <- NA
t1 <- data.frame(Variable = v,
                 Mean = round(sapply(x, mean), 2), SD = round(sapply(x, sd), 2),
                 Min = round(sapply(x, min), 2), Max = round(sapply(x, max), 2),
                 r[, 1:6], check.names = FALSE)
names(t1)[6:11] <- as.character(1:6)
within_r <- with(d, cor(L - ave(L, id), C - ave(C, id)))   # within-firm correlation, variables 1-2
ft1 <- flextable(t1) |> colformat_num(na_str = "") |> autofit() |>
  set_caption("Table 4. Descriptive statistics and correlations (1,374 firm-years, 93 firms)") |>
  add_footer_lines(sprintf("Correlations computed on pooled firm-years. Within-firm correlation between variables 1 and 2: r = %.2f.", within_r))
ft1 <- tnr(ft1)
save_as_docx(ft1, path = paste0(out, "table4_descriptives.docx"))

# ---------------------------------------------------------------------
# Table 5. Evolution by period
# ---------------------------------------------------------------------
d$period <- cut(d$annee, c(1995, 2005, 2010, 2015, 2020, 2025),
                labels = c("1996–2005", "2006–2010", "2011–2015", "2016–2020", "2021–2025"))
t2 <- do.call(rbind, lapply(split(d, d$period), function(g) data.frame(
  Pages = nrow(g),
  `Long-term per 1,000 words`  = 1000 * sum(g$long_explicite)  / sum(g$n_mots),
  `Short-term per 1,000 words` = 1000 * sum(g$court_explicite) / sum(g$n_mots),
  `Words (median)` = median(g$n_mots),
  `Sustainability (%)` = 100 * mean(g$serv_durabilite_b),
  `Long-term (%)` = 100 * mean(g$L), `Short-term (%)` = 100 * mean(g$C),
  `Co-occurrence observed (%)` = 100 * mean(g$L * g$C),
  `Co-occurrence expected (%)` = 100 * mean(g$L) * mean(g$C), check.names = FALSE)))
t2$Ratio <- t2$`Co-occurrence observed (%)` / t2$`Co-occurrence expected (%)`
t2 <- cbind(Period = rownames(t2), round(t2, 2))
ft2 <- flextable(t2) |> autofit() |>
  set_caption("Table 5. Temporal orientation of service offerings by period") |>
  add_footer_lines("Expected co-occurrence: product of the shares of pages containing a long-term and a short-term marker (independence assumption). Ratio = observed / expected.")
ft2 <- tnr(ft2)
save_as_docx(ft2, path = paste0(out, "table5_periods.docx"))

# ---------------------------------------------------------------------
# Table 6. H1: co-occurrence of short- and long-term markers (main + robustness)
# ---------------------------------------------------------------------
f_serv <- paste(serv, collapse = " + ")
map_h1 <- c(L = "Long-term marker (presence)", C = "Short-term marker (presence)",
            "L:annee_c" = "Long-term marker × year",
            log_mots = "Page length (log words)", annee_c = "Year (centred on 2010)")
h1 <- list(
  "(1) Cond. logit" = clogit(C ~ L + log_mots + annee_c + strata(id), data = d, method = "exact"),
  "(2) + services"  = clogit(as.formula(paste("C ~ L + log_mots + annee_c +", f_serv, "+ strata(id)")), data = d, method = "exact"),
  "(3) Reversed"    = clogit(L ~ C + log_mots + annee_c + strata(id), data = d, method = "exact"),
  "(4) LPM"         = feols(C ~ L + log_mots + annee_c | id, data = d, cluster = ~id))
rows_h1 <- data.frame(term = c("13 service categories", "Firm fixed effects"),
  m1 = c("No","Yes"), m2 = c("Yes","Yes"), m3 = c("No","Yes"), m4 = c("No","Yes"))
ft3 <- modelsummary(h1, vcov = list("classical", "classical", "classical", ~id),
  exponentiate = c(TRUE, TRUE, TRUE, FALSE), coef_map = map_h1,
  stars = stars_set, add_rows = rows_h1, gof_map = "nobs",
  title = "Table 6. Co-occurrence of short- and long-term markers (H1)",
  notes = c("Dependent variable: presence of a short-term marker, except column 3 (long-term marker).",
            "Columns 1-3: odds ratios (conditional logit, firm fixed effects by conditioning); column 4: linear probability model, standard errors clustered by firm.",
            "A logit without fixed effects gives a positive and significant association (OR = 1.77, p = 0.023; not reported). Sensitivity analyses: Table A7."),
  output = "flextable")
ft3 <- tnr(ft3)
save_as_docx(ft3, path = paste0(out, "table6_H1.docx"))

# ---------------------------------------------------------------------
# Table 7. H2: evolution of marker density (main + robustness)
# ---------------------------------------------------------------------
pois <- function(f, data = d) fepois(f, data = data, offset = ~log_mots, cluster = ~id)
map_h2 <- c(annee_c = "Year (centred on 2010)", serv_durabilite_b = "Sustainability services")
h2 <- list(
  "(1) Long-term"          = pois(long_explicite ~ annee_c | id),
  "(2) + sustainability"   = pois(long_explicite ~ annee_c + serv_durabilite_b | id),
  "(3) Excluding “future”" = pois(lt_sans_future ~ annee_c + serv_durabilite_b | id),
  "(4) Short-term"         = pois(court_explicite ~ annee_c | id))
rows_h2 <- data.frame(term = "Firm fixed effects", m1 = "Yes", m2 = "Yes", m3 = "Yes", m4 = "Yes")
ft4 <- modelsummary(h2, exponentiate = TRUE, coef_map = map_h2,
  stars = stars_set, add_rows = rows_h2, gof_map = "nobs",
  title = "Table 7. Evolution of temporal marker density (H2)",
  notes = c("Incidence rate ratios. Firm fixed-effects Poisson; exposure: log number of words. Standard errors clustered by firm. Firms without any marker over the period are excluded.",
            "Dependent variable: long-term markers (columns 1-2), long-term markers excluding “future” (3), short-term markers (4).",
            "Results unchanged when controlling for the 13 service categories (not reported). Sensitivity analyses: Table A7."),
  output = "flextable")
ft4 <- tnr(ft4)
save_as_docx(ft4, path = paste0(out, "table7_H2.docx"))

# ---------------------------------------------------------------------
# Table A6. Evolution of the co-occurrence over time (exploratory, H1)
# ---------------------------------------------------------------------
mA6 <- clogit(C ~ L + L:annee_c + log_mots + annee_c + strata(id), data = d, method = "exact")
cf <- summary(mA6)$coefficients; ci <- exp(confint(mA6))
lab <- c(L = "Long-term marker (presence)", "L:annee_c" = "Long-term marker × year",
         log_mots = "Page length (log words)", annee_c = "Year (centred on 2010)")
tA6 <- data.frame(Variable = lab[rownames(cf)],
                  `Odds ratio` = sprintf("%.2f", cf[, "exp(coef)"]),
                  `95% CI` = sprintf("[%.2f, %.2f]", ci[, 1], ci[, 2]),
                  p = ifelse(cf[, "Pr(>|z|)"] < 0.001, "< 0.001", sprintf("%.3f", cf[, "Pr(>|z|)"])),
                  check.names = FALSE)
tA6 <- tA6[match(lab, tA6$Variable), ]
ftA3 <- flextable(tA6) |> autofit() |>
  set_caption("Table A6. Evolution of the co-occurrence over time (exploratory)") |>
  add_footer_lines(sprintf("Conditional logit with firm fixed effects (by conditioning); n = %s firm-years from firms with variation in the dependent variable. Dependent variable: presence of a short-term marker. An interaction above 1 would indicate that the association between the two poles strengthens over time.",
                           format(sum(ave(d$C, d$id, FUN = function(x) length(unique(x))) > 1), big.mark = ","))) |> tnr()
save_as_docx(ftA3, path = paste0(out, "tableA6_cooccurrence_time.docx"))

# ---------------------------------------------------------------------
# Table A7. Sensitivity to the treatment of ambiguous markers (H1 and H2)
# ---------------------------------------------------------------------
d_amb_l <- transform(d, L = as.integer(long_explicite + ambigu > 0))    # ambiguous counted as long term
d_amb_c <- transform(d, C = as.integer(court_explicite + ambigu > 0))   # ambiguous counted as short term
d$lt_amb <- d$long_explicite + d$ambigu
hA4 <- list(
  "H1: ambiguous = long"  = clogit(C ~ L + log_mots + annee_c + strata(id), data = d_amb_l, method = "exact"),
  "H1: ambiguous = short" = clogit(C ~ L + log_mots + annee_c + strata(id), data = d_amb_c, method = "exact"),
  "H2: long + ambiguous"  = pois(lt_amb ~ annee_c + serv_durabilite_b | id),
  "Ambiguous only"        = pois(ambigu ~ annee_c + serv_durabilite_b | id))
ftA4 <- modelsummary(hA4, vcov = list("classical", "classical", ~id, ~id), exponentiate = TRUE,
  coef_map = c(L = "Long-term marker (presence)", map_h2, log_mots = "Page length (log words)"),
  stars = stars_set, gof_map = "nobs",
  title = "Table A7. Sensitivity to the treatment of ambiguous markers",
  notes = c("Ambiguous markers (e.g. tomorrow, ESG; Table A1, panel C) are counted as long-term or short-term markers in turn.",
            "Columns 1-2: odds ratios, conditional logit (as in Table 6, column 1). Columns 3-4: incidence rate ratios, firm fixed-effects Poisson with exposure (as in Table 7, column 2), standard errors clustered by firm."),
  output = "flextable")
ftA4 <- tnr(ftA4)
save_as_docx(ftA4, path = paste0(out, "tableA7_sensitivity_ambiguous.docx"))

# ---------------------------------------------------------------------
# Table A8. Service categories and marker density (exploratory)
# ---------------------------------------------------------------------
lab_serv <- c(serv_strategie_b = "Strategy and growth", serv_operations_b = "Operations and supply chain",
  serv_techno_b = "Technology, digital and data", serv_risque_b = "Risk, compliance and cybersecurity",
  serv_transactions_b = "Finance, transactions and M&A", serv_performance_b = "Performance, costs and restructuring",
  serv_rh_b = "Human capital, organisation and change", serv_marketing_b = "Marketing, customers and sales",
  serv_durabilite_b = "Sustainability, climate and ESG", serv_innovation_b = "Innovation, R&D and design",
  serv_ingenierie_b = "Engineering, infrastructure and projects", serv_politiques_b = "Public policy and development",
  serv_litiges_b = "Litigation, economic expertise and forensics", annee_c = "Year (centred on 2010)")
hs <- list("Long-term markers"  = pois(as.formula(paste("long_explicite ~ annee_c +", f_serv, "| id"))),
           "Short-term markers" = pois(as.formula(paste("court_explicite ~ annee_c +", f_serv, "| id"))))
ftA5 <- modelsummary(hs, exponentiate = TRUE, coef_map = lab_serv, stars = stars_set, gof_map = "nobs",
  title = "Table A8. Service categories and temporal marker density (exploratory)",
  notes = c("Incidence rate ratios. Firm fixed-effects Poisson; exposure: log number of words; standard errors clustered by firm.",
            "Each category is coded 1 if detected on the page (Table A2). With 26 coefficients tested, one or two may be significant at the 5% level by chance; results should be read with caution."),
  output = "flextable")
ftA5 <- tnr(ftA5)
save_as_docx(ftA5, path = paste0(out, "tableA8_services_markers.docx"))

# ---------------------------------------------------------------------
# Figure 2. Evolution of temporal marker density (results section)
# Years with at least 20 firm-years (2002-2025).
# ---------------------------------------------------------------------
figs <- "tables/en/figures/"; dir.create(figs, recursive = TRUE, showWarnings = FALSE)
yr <- aggregate(cbind(long_explicite, court_explicite, lt_sans_future, n_mots) ~ annee, data = d, FUN = sum)
yr$pages <- as.vector(table(d$annee)[as.character(yr$annee)])
yr <- yr[yr$pages >= 20, ]
dens <- function(v) 1000 * v / yr$n_mots
png(paste0(figs, "figure2_marker_density.png"), width = 2200, height = 1300, res = 250, family = "Times")
par(mar = c(4.5, 4.5, 1.5, 1))
plot(yr$annee, dens(yr$long_explicite), type = "o", pch = 16, lwd = 2, col = "black",
     ylim = c(0, max(dens(yr$long_explicite)) * 1.05),
     xlab = "Year", ylab = "Markers per 1,000 words")
lines(yr$annee, dens(yr$court_explicite), type = "o", pch = 17, lwd = 2, col = "grey55")
lines(yr$annee, dens(yr$lt_sans_future), type = "o", pch = 1, lwd = 1.5, lty = 2, col = "black")
legend("topleft", bty = "n", lwd = c(2, 2, 1.5), lty = c(1, 1, 2), pch = c(16, 17, 1),
       col = c("black", "grey55", "black"),
       legend = c("Long-term markers", "Short-term markers", "Long-term markers excluding \u201cfuture\u201d"))
dev.off()

# ---------------------------------------------------------------------
# Display in the RStudio Viewer + HTML copies
# ---------------------------------------------------------------------
for (nm in c("ft1", "ft2", "ft3", "ft4", "ftA3", "ftA4", "ftA5")) save_as_html(get(nm), path = paste0(out, nm, ".html"))
print(ft1); print(ft2); print(ft3); print(ft4); print(ftA3); print(ftA4); print(ftA5)   # use the Viewer arrows to move between tables
cat("\nFiles created:", list.files(out, pattern = "^table.*docx$"), sep = "\n")

# =====================================================================
# Figures for the data analysis section (model choices)
#   Figure A3. Page length, raw vs log           -> log transformation of length
#   Figure A5. Distribution of marker counts     -> count model, robust SE (zeros, overdispersion)
#   Figure A4. Years observed per firm           -> unbalanced panel, firm fixed effects
# Saved as PNG in tables/en/figures/ (Times, English).
# =====================================================================
setwd("~/Desktop/wayback/6_analysis")
out <- "tables/en/figures/"; dir.create(out, recursive = TRUE, showWarnings = FALSE)
d <- read.csv("analysis_data.csv")
fam <- "Times"

# ---------- Figure A3. Page length ----------
png(paste0(out, "figureA3_page_length.png"), width = 2200, height = 950, res = 250, family = fam)
par(mfrow = c(1, 2), mar = c(4.5, 4.5, 3, 1))
hist(d$n_mots, breaks = 50, col = "grey75", border = "white",
     main = "(a) Number of words", xlab = "Words per page", ylab = "Firm-years")
hist(d$log_mots, breaks = 40, col = "grey45", border = "white",
     main = "(b) Log number of words", xlab = "log(words per page)", ylab = "Firm-years")
dev.off()

# ---------- Figure A5. Marker counts ----------
lab <- c("0", "1", "2", "3", "4", "5+")
tab <- rbind(`Long-term markers` = table(cut(d$long_explicite, c(-1, 0:4, Inf), labels = lab)),
             `Short-term markers` = table(cut(d$court_explicite, c(-1, 0:4, Inf), labels = lab)))
sub <- sprintf("Long-term: mean = %.2f, variance = %.2f, zeros = %.0f%%.   Short-term: mean = %.2f, variance = %.2f, zeros = %.0f%%.",
               mean(d$long_explicite), var(d$long_explicite), 100 * mean(d$long_explicite == 0),
               mean(d$court_explicite), var(d$court_explicite), 100 * mean(d$court_explicite == 0))
png(paste0(out, "figureA5_marker_counts.png"), width = 2000, height = 1200, res = 250, family = fam)
par(mar = c(6, 4.5, 2, 1))
barplot(tab, beside = TRUE, col = c("grey25", "grey70"), border = NA,
        xlab = "Markers per page", ylab = "Firm-years",
        legend.text = rownames(tab), args.legend = list(bty = "n", x = "topright"))
mtext(sub, side = 1, line = 4.5, cex = 0.75)
dev.off()

# ---------- Figure A4. Years per firm ----------
yrs <- as.vector(table(d$id))
png(paste0(out, "figureA4_years_per_firm.png"), width = 1800, height = 1100, res = 250, family = fam)
par(mar = c(4.5, 4.5, 2, 1))
barplot(table(factor(yrs, levels = min(yrs):max(yrs))), col = "grey55", border = NA,
        xlab = "Valid years per firm", ylab = "Firms")
mtext(sprintf("93 firms, 1,374 firm-years; median = %d years (min %d, max %d).", as.integer(median(yrs)), min(yrs), max(yrs)),
      side = 3, line = 0.3, cex = 0.8)
dev.off()

# Within-firm share of variance (reported in the text, no figure needed)
w <- function(v) round(100 * (1 - var(ave(v, d$id)) / var(v)), 1)
cat("Within-firm share of variance (%): long-term presence", w(d$L), "| short-term presence", w(d$C),
    "| log length", w(d$log_mots), "\n")
cat("Figures created in", out, ":\n"); print(list.files(out))

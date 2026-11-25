# The best of both times: Intertemporal tension in consulting firms' temporal talk, 1996–2025

Replication material for a course paper (quantitative methods) examining how consulting firms' temporal talk articulates the short and the long term in their service offerings, using archived websites from the Wayback Machine. Service pages are treated as a device of temporal talk (Bansal et al., 2022), and their temporal orientation is measured with a validated dictionary of explicit short- and long-term markers.

**Research question.** How does consulting firms' temporal talk articulate the short and the long term, and how has this articulation evolved over time?

- **H1.** Short- and long-term markers co-occur within the same service offering more often than their respective frequencies would predict.
- **H2.** The density of long-term markers in service offerings increases over time.
- **Exploratory.** Evolution of the co-occurrence over time; firms and service categories associated with each pole.

**Data.** Annual snapshots (closest to 2 July) of the services page of 93 consulting firms drawn from the Forbes *World's Best Management Consulting Firms* list (version of 20 August 2026): 1,374 firm-years, 1996–2025.

> Folder and file names are in English. Variable names in the data files and comments in the scripts are in French; a short glossary is given at the end of this file.

---

## Repository structure

Folders are numbered in the order of the pipeline.

| Folder | Content |
|---|---|
| `1_coverage/` | Wayback Machine coverage of each firm's domain(s) and eligibility list (193 → 173 → 160 firms). |
| `2_collection/` | Collection scripts (services pages, sub-pages, mission pages) and capture metadata (URLs, timestamps). |
| `3_cleaning_panel/` | Cleaned firm × year panel, manual checks of suspect pages, final list of eligible firms (93). |
| `4_temporal_markers/` | Temporal marker dictionary (v1 → v4), manual coding and inter-coder reliability, marker counts per page. Sub-folders `topic_modelling/`, `attachment/`, `management_fashion/` and `diagnostics/` contain exploratory or abandoned analyses, kept for transparency. |
| `5_controls/` | Service-category and client-industry dictionaries, their manual validation, and control variables per firm-year. |
| `6_analysis/` | Final analysis dataset, hypothesis tests (Python and R) and tables. `tables/en/` holds the final tables. |

## Pipeline

| Step | Script | Main output |
|---|---|---|
| 1. Archive coverage | `1_coverage/coverage_fast2.py`, `coverage_remeasure.py` | `coverage_list_v2.csv` |
| 2. Collection of services pages | `2_collection/collect_services_v2.py` | `services_metadata.csv` (+ raw HTML, not shared) |
| 2b. Sub-pages and mission pages | `2_collection/collect_subpages.py`, `collect_mission.py` | `subpages_metadata.csv`, `mission_metadata.csv` |
| 3a. Text cleaning | `3_cleaning_panel/cleaning.py` | `cleaned_texts.csv` (not shared) |
| 3b. Panel and eligible firms | `3_cleaning_panel/panel.py` | `panel_firm_year.csv`, `eligible_firms_final.csv` |
| 4. Temporal markers (dictionary v4) | `4_temporal_markers/markers_v4.py` | `horizon_index_v4.csv`, `dictionary_temporal_v4.csv` |
| 5. Control variables | `4_temporal_markers/controls_services.py` | `5_controls/controls_firm_year.csv`, `dictionary_controls.csv` |
| 6. Hypothesis tests | `6_analysis/tests_h1_h2.py` (Python), `verification_R.R` (R) | `results_tests_h1_h2.xlsx` |
| 7. Tables and figures | R: `6_analysis/tables_R.R`, `diagnostics_R.R`. Python: `4_temporal_markers/validation_table.py`, `6_analysis/validation_appendix.py`, `dictionary_appendix.py`, `controls_appendix.py`, `figure_sample_flow.py` | `6_analysis/tables/en/` (main and appendix tables, Word format) and `tables/en/figures/` |

*Note on step 3.* `cleaning.py` removes repeated site templates using 8-word windows (rules described in the script header); `panel.py` applies the validity filters (manually excluded pivot pages, at least 50 words after cleaning, English or French) and keeps firms with at least 10 valid years. Both scripts were reconstructed from the working sessions and reproduce the shared output files exactly.

Collection scripts are run from `2_collection/`; `cleaning.py` and `panel.py` from the project folder (`cd ~/Desktop/wayback`). R scripts assume the project folder is located at `~/Desktop/wayback`. Adjust the `setwd()` / working directory if needed.

## Data not included

The full texts and HTML of archived pages belong to the firms and are not redistributed. They can be rebuilt from the capture URLs and timestamps provided in `2_collection/services_metadata.csv` and `3_cleaning_panel/panel_firm_year.csv`. Coding files (`4_temporal_markers/coding_*.xlsx`, `5_controls/coding_*.xlsx`, `6_analysis/coding_managed_services.xlsx`) and validation keys contain only short excerpts (a few sentences, at most about 1,200 characters) around each coded occurrence, which are needed to assess the validation of the dictionaries. The cleaned text column was removed from `4_temporal_markers/mission_panel_horizon.csv`.

## Measurement and validation

- **Dictionary.** The initial dictionary was generated with the help of a generative AI assistant from the corpus, then revised over four versions (`dictionary_temporal_v3.csv`, `dictionary_temporal_v4.csv`).
- **Manual coding.** 240 occurrences coded blind to the dictionary category (`coding_temporal_markers.xlsx`; key: `coding_temporal_markers_KEY.xlsx`).
- **Second coder.** 100 occurrences (`codage_marqueurs_temporels_codeur2*.xlsx`, reconciliation: `reconciliation_coder2.xlsx`). Explicit markers are retained as the main measure; implicit markers are exploratory.
- **Control dictionaries.** 160 passages coded manually (`5_controls/coding_services_industries.xlsx`).

## Final analysis dataset — `6_analysis/analysis_data.csv`

One row per firm-year (1,374 rows).

| Variable | Description |
|---|---|
| `id`, `nom` | Firm identifier and name |
| `annee`, `annee_c` | Year of the capture; year centred on 2010 |
| `n_mots`, `log_mots` | Number of words after cleaning; its natural log |
| `long_explicite`, `court_explicite` | Number of explicit long-term / short-term markers (dictionary v4) |
| `L`, `C` | Presence (1/0) of at least one long-term / short-term marker |
| `future`, `lt_sans_future` | Occurrences of *future* (EN/FR); long-term markers excluding *future* |
| `serv_*_b` | Presence (1/0) of each of the 13 service categories |
| `ind_*_b` | Presence (1/0) of each of the 10 client industries (not used in final models) |

## Software

- **Python 3.10**: `pandas`, `numpy`, `requests`, `beautifulsoup4`, `langdetect`, `statsmodels`, `pyfixest`, `openpyxl`.
- **R 4.x**: `survival`, `fixest`, `sandwich`, `lmtest`, `modelsummary`, `flextable`.

To reproduce the tables, open R and run:

```r
source("~/Desktop/wayback/6_analysis/tables_R.R")
source("~/Desktop/wayback/6_analysis/diagnostics_R.R")
```

## Use of generative AI

A generative AI assistant (Claude, Anthropic) was used at several stages: generating the initial dictionary of temporal markers, writing the collection, cleaning and analysis scripts, suggesting statistical specifications, identifying references and assisting with writing. All theoretical and methodological choices were reviewed and made by the author. The dictionary was validated through manual coding of 240 occurrences, blind to the category assigned by the dictionary, and through a second coder; references were checked against their sources; and the estimates were reproduced in R.

## Glossary

| French | English |
|---|---|
| couverture | coverage |
| collecte | collection |
| nettoyage | cleaning |
| marqueurs (de court / long terme) | (short- / long-term) markers |
| lexique | dictionary |
| codage, codeur | coding, coder |
| contrôles | controls |
| firme, année | firm, year |
| tableaux | tables |
| ancien | old / superseded |

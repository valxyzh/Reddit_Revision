* pvar_type_sv_both.do
* PVAR with type-specific SV interactions — full sample AND active weeks
* sv_X_fan = sv_fanatic_std_1 * L_Fanatic  (each type's own SV x its own tone)
* sv_X_rat = sv_rational_std_1 * L_Rational
* sv_X_nai = sv_naive_std_1 * L_Naive
* Also includes SSS (firm-specific, sss_overall_by_week.csv)

cd ~/Reddit_Revision
log using output/pvar_type_sv_both.log, replace

* ── Load & prep ──────────────────────────────────────────────────────────────
use reg_data_with_sv.dta, clear

global reddit_var tone_1 tone_2 tone_3 traffic_1 traffic_2 traffic_3 num_commentors user_fixed_effect residual
foreach var in $reddit_var {
    gen `var'_missing = missing(`var')
    replace `var' = 0 if missing(`var')
}

rename tone_1  Fanatic_tone
rename tone_2  Rational_tone
rename tone_3  Naive_tone
rename dlyret  Return
rename rtoib3  Retail_flow
gen Short_flow = dtcr / 100

encode sym_root, gen(stock_id)
gen week_id = (week_start - 21913) / 7 + 1
xtset stock_id week_id

foreach var in $reddit_var {
    by stock_id (week_id): gen `var'_missing_1 = `var'_missing[_n-1]
}

* ── Type-specific SV (already in dta) ───────────────────────────────────────
foreach t in fanatic rational naive {
    sum sv_mean_`t'
    gen sv_`t'_std = (sv_mean_`t' - r(mean)) / r(sd)
    gen sv_`t'_missing = missing(sv_mean_`t')
    replace sv_`t'_std = 0 if missing(sv_`t'_std)
    bysort stock_id (week_id): gen sv_`t'_std_1    = sv_`t'_std[_n-1]
    bysort stock_id (week_id): gen sv_`t'_missing_1 = sv_`t'_missing[_n-1]
}

* ── Lagged tones ─────────────────────────────────────────────────────────────
bysort stock_id (week_id): gen L_Fanatic  = Fanatic_tone[_n-1]
bysort stock_id (week_id): gen L_Rational = Rational_tone[_n-1]
bysort stock_id (week_id): gen L_Naive    = Naive_tone[_n-1]

* ── Type-specific interaction terms ─────────────────────────────────────────
gen sv_X_fan = sv_fanatic_std_1  * L_Fanatic
gen sv_X_rat = sv_rational_std_1 * L_Rational
gen sv_X_nai = sv_naive_std_1    * L_Naive

* ── Merge SSS (firm-specific prior tone) ────────────────────────────────────
preserve
import delimited using output/sss_overall_by_week.csv, clear varnames(1)
rename ticker sym_root
gen week_start2 = date(week_start, "YMD")
format week_start2 %td
drop week_start
rename week_start2 week_start
keep sym_root week_start sss_mean_tone_shift
tempfile sss
save `sss'
restore
merge m:1 sym_root week_start using `sss', keep(master match) nogen
rename sss_mean_tone_shift sss_overall

gen sss_missing = missing(sss_overall)
replace sss_overall = 0 if missing(sss_overall)
sum sss_overall
gen sss_std = (sss_overall - r(mean)) / r(sd)
bysort stock_id (week_id): gen sss_std_1    = sss_std[_n-1]
bysort stock_id (week_id): gen sss_missing_1 = sss_missing[_n-1]

gen sss_X_fan = sss_std_1 * L_Fanatic
gen sss_X_rat = sss_std_1 * L_Rational
gen sss_X_nai = sss_std_1 * L_Naive

* ── Sample counts ────────────────────────────────────────────────────────────
di "=== Full sample ==="
count
di "=== Active weeks ==="
count if num_commentors > 0

* ═══════════════════════════════════════════════════════════════════════════════
* FULL SAMPLE
* ═══════════════════════════════════════════════════════════════════════════════

* PVAR 1: Type-specific SV only (full sample)
di "=== PVAR 1: Type-specific SV — Full Sample ==="
pvar Fanatic_tone Rational_tone Naive_tone Return Retail_flow Short_flow, ///
    lags(1) ///
    exog(tone_3_missing_1 ///
         sv_fanatic_missing_1 sv_rational_missing_1 sv_naive_missing_1 ///
         sv_fanatic_std_1 sv_rational_std_1 sv_naive_std_1 ///
         sv_X_fan sv_X_rat sv_X_nai) ///
    td vce(cluster stock_id week_id)
pvargranger

* PVAR 2: Type-specific SV + SSS jointly (full sample)
di "=== PVAR 2: Type-specific SV + SSS — Full Sample ==="
pvar Fanatic_tone Rational_tone Naive_tone Return Retail_flow Short_flow, ///
    lags(1) ///
    exog(tone_3_missing_1 sss_missing_1 ///
         sv_fanatic_missing_1 sv_rational_missing_1 sv_naive_missing_1 ///
         sv_fanatic_std_1 sv_rational_std_1 sv_naive_std_1 sss_std_1 ///
         sv_X_fan sv_X_rat sv_X_nai ///
         sss_X_fan sss_X_rat sss_X_nai) ///
    td vce(cluster stock_id week_id)
pvargranger

* ═══════════════════════════════════════════════════════════════════════════════
* ACTIVE WEEKS ONLY
* ═══════════════════════════════════════════════════════════════════════════════

* PVAR 3: Type-specific SV only (active weeks)
di "=== PVAR 3: Type-specific SV — Active Weeks ==="
pvar Fanatic_tone Rational_tone Naive_tone Return Retail_flow Short_flow ///
    if num_commentors > 0, ///
    lags(1) ///
    exog(tone_3_missing_1 ///
         sv_fanatic_missing_1 sv_rational_missing_1 sv_naive_missing_1 ///
         sv_fanatic_std_1 sv_rational_std_1 sv_naive_std_1 ///
         sv_X_fan sv_X_rat sv_X_nai) ///
    td vce(cluster stock_id week_id)
pvargranger

* PVAR 4: Type-specific SV + SSS jointly (active weeks)
di "=== PVAR 4: Type-specific SV + SSS — Active Weeks ==="
pvar Fanatic_tone Rational_tone Naive_tone Return Retail_flow Short_flow ///
    if num_commentors > 0, ///
    lags(1) ///
    exog(tone_3_missing_1 sss_missing_1 ///
         sv_fanatic_missing_1 sv_rational_missing_1 sv_naive_missing_1 ///
         sv_fanatic_std_1 sv_rational_std_1 sv_naive_std_1 sss_std_1 ///
         sv_X_fan sv_X_rat sv_X_nai ///
         sss_X_fan sss_X_rat sss_X_nai) ///
    td vce(cluster stock_id week_id)
pvargranger

log close _all

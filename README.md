# Reddit Revision

## Why Structural Virality (SV)

**Editor's letter, Comment 2:** *"Would it be possible to differentiate the type of social media interactions? It makes a huge difference seeing an anonymous post versus seeing Trump's tweets. You would need to uncover deeper insights and more interesting patterns from the data to provide sufficient contribution to the literature."*

The editor is asking us to go beyond simple tone measures and capture *how* information spreads and *whose* voice drives sentiment — not just what is said, but how far it reaches and how much it moves others.

**Structural Virality (SV)** addresses this directly. Rather than treating all posts equally, SV measures whether a discussion cascades through a chain of users (viral, high SV) or simply broadcasts from one source to many passive readers (star-shaped, low SV). A high-SV thread is more like a Trump tweet that gets retweeted and debated across many users — it has structural reach. A low-SV thread is more like an anonymous post that gets a few direct replies and dies. By interacting SV with investor type tone in the PVAR, we can ask: does the *way* Fanatic/Rational/Naive sentiment spreads — not just its content — affect stock returns and order flows?

---

## Why Sentiment Shift Score (SSS)

**Reviewer 1, Comment 4:** *"While the authors argue that this variable reflects social influence, this claim requires further validation. This variable primarily captures the intensity of investors' subsequent participation and does not immediately indicate whether these follow-up commenters are genuinely 'influenced' by the original poster."*

The reviewer's concern is that follow-up commenting could reflect engagement intensity rather than true opinion change — someone might reply simply because they are active, not because the original post moved them.

SSS is constructed to address this directly. SSS is defined at the **parent comment level**: it measures how much a given comment shifts the tone of its direct repliers, relative to each replier's own recent baseline for that stock. A comment with high SSS is one that genuinely moves people — its repliers express themselves differently about the stock than they have been doing. A comment with SSS near zero simply attracts replies that are consistent with how those users already talk about the stock.

Formally, for each reply $r$ to parent comment $c$, we compute the tone deviation from that replier's stock-specific prior:

$$\Delta\text{tone}(r) = \text{tone}(r) - \overline{\text{tone}}_{\text{prior week}}(\text{author}(r), \text{ticker})$$

where the prior baseline is the replier's mean tone on that ticker in the most recent week (strictly before the current week) in which they posted about it. SSS of parent comment $c$ is then the mean tone deviation it induces:

$$SSS(c) = \frac{1}{|R_c|} \sum_{r \in R_c} \Delta\text{tone}(r)$$

and `sss_overall` for a stock-week is the mean SSS across all parent comments in that stock-week.

This design separates influence (a comment shifting repliers' expressed sentiment away from their own recent stock-specific prior) from participation intensity (how many people replied or how actively they engage). A replier who consistently posts positively about a stock and continues to do so after reading the parent contributes nothing to SSS — only repliers who deviate from their own established tone pattern are counted as influenced.

---

## PVAR Results

All results are from a 6-variable Panel VAR (Fanatic tone, Rational tone, Naive tone, Return, Retail flow, Short flow), estimated with one lag, two-way clustered standard errors, and time dummies. Full sample N = 710,378 stock-week observations across 3,066 stocks; active weeks N ≈ 81k (weeks with at least one commenter).

Script: `pvar_type_sv_both.do` — type-specific SV (each type's own SV interacted with its own lagged tone) + firm-specific SSS. Key spec is **PVAR 4: active weeks, joint model**.

### Baseline PVAR (no interactions)

- **Naive tone → Return:** significant (χ²=14.2, p<0.001) — the only tone type that Granger-causes returns
- **All three tone types → Retail flow:** significant (Fanatic p=0.009, Rational p<0.001, Naive p<0.001)
- **No tone type → Short flow:** none significant
- **Return → all three tone types:** significant — returns feed back into sentiment for all types

### Main Result: Type-specific SV + SSS, Active Weeks (PVAR 4)

SV is computed separately for each investor type (`sv_mean_fanatic`, `sv_mean_rational`, `sv_mean_naive`), standardised and lagged one period. Each type's SV is interacted only with its own lagged tone. SSS uses the firm-specific prior tone baseline (author's mean tone on that ticker in the most recent prior week).

**Return equation:**

- **SV_Fanatic × L.Fanatic tone → Return: +0.0027 (p=0.049) ✓** — when Fanatic threads spread more virally, Fanatic tone is more return-predictive
- **SSS × L.Rational tone → Return: +0.0007 (p<0.001) ✓** — stronger sentiment-shifting power amplifies Rational tone's return predictability
- **SSS × L.Naive tone → Return: +0.0014 (p<0.001) ✓** — stronger sentiment-shifting power amplifies Naive tone's return predictability
- SV_Rational × L.Rational: NS &nbsp;|&nbsp; SV_Naive × L.Naive: NS

**Additional effects:**
- **SSS × L.Naive → Retail flow: +0.0025 (p<0.001) ✓** — high-SSS weeks see Naive tone drive more retail order flow
- **SSS × L.Rational → Retail flow:** significant — same channel for Rational tone

### Robustness: Full Sample (PVAR 2)

With the full sample (including inactive weeks), type-specific SV interactions are all NS. SSS × L.Naive → Return is marginal (p=0.054). The active-weeks result is the cleaner test — the amplification effects concentrate in weeks when discussion is actually happening.

---

## What Else To Do

- [x] Compute **SV by type × stock × week** — done; `sv_mean_fanatic`, `sv_mean_rational`, `sv_mean_naive` in `sv_by_week.csv`, used in `pvar_type_sv_both.do`
- [ ] Compute **SSS by type × stock × week** — `sss_overall` is still type-agnostic; could break out SSS for Fanatic, Rational, Naive parent comments separately

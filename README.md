# Reddit Revision

## Why Structural Virality (SV)

**Editor's letter, Comment 2:** *"Would it be possible to differentiate the type of social media interactions? It makes a huge difference seeing an anonymous post versus seeing Trump's tweets. You would need to uncover deeper insights and more interesting patterns from the data to provide sufficient contribution to the literature."*

The editor is asking us to go beyond simple tone measures and capture *how* information spreads and *whose* voice drives sentiment — not just what is said, but how far it reaches and how much it moves others.

**Structural Virality (SV)** addresses this directly. Rather than treating all posts equally, SV measures whether a discussion cascades through a chain of users (viral, high SV) or simply broadcasts from one source to many passive readers (star-shaped, low SV). A high-SV thread is more like a Trump tweet that gets retweeted and debated across many users — it has structural reach. A low-SV thread is more like an anonymous post that gets a few direct replies and dies. By interacting SV with investor type tone in the PVAR, we can ask: does the *way* Fanatic/Rational/Naive sentiment spreads — not just its content — affect stock returns and order flows?

**Sentiment Shift Score (SSS)** captures influence at the individual comment level: how much does a comment move its repliers away from their own prior tone baseline? This operationalises the editor's intuition that not all voices are equal — a comment with high SSS is one that actually changes how others express themselves, analogous to the influence a prominent figure's post has on the discourse.

---

## Why Sentiment Shift Score (SSS)

**Reviewer 1, Comment 4:** *"While the authors argue that this variable reflects social influence, this claim requires further validation. This variable primarily captures the intensity of investors' subsequent participation and does not immediately indicate whether these follow-up commenters are genuinely 'influenced' by the original poster."*

The reviewer's concern is that follow-up commenting could reflect engagement intensity rather than true opinion change — someone might reply simply because they are active, not because the original post moved them.

SSS is constructed to address this directly. For each replier, we compute the **deviation of their reply tone from their own prior baseline** — the cumulative mean tone of all their previous posts (requiring ≥ 3 prior posts). This means SSS does not measure whether someone replied (participation), but whether their tone in that reply is *different from how they normally express themselves*. A replier who always posts positively and continues to do so is not counted as influenced. Only repliers who deviate from their own established tone pattern contribute to SSS.

This design separates influence (shifting someone's expressed sentiment relative to their own prior) from participation intensity (how many people replied or how actively they engage). A high-SSS comment is one that causes repliers to express themselves differently than they typically would — which is a closer operationalisation of genuine opinion influence than simple reply counts or engagement volume.

---

## Tentative PVAR Results

All results are from a 6-variable Panel VAR (Fanatic tone, Rational tone, Naive tone, Return, Retail flow, Short flow), estimated with one lag, two-way clustered standard errors, and time dummies. Full sample N = 710,378 stock-week observations across 3,066 stocks.

### Baseline PVAR (no interactions)

- **Naive tone → Return:** significant (χ²=14.2, p<0.001) — the only tone type that Granger-causes returns
- **All three tone types → Retail flow:** significant (Fanatic p=0.009, Rational p<0.001, Naive p<0.001)
- **No tone type → Short flow:** none significant
- **Return → all three tone types:** significant — returns feed back into sentiment for all types
- **High-influence users (top 10% by commenter count):** much stronger own-persistence in tone and larger spillovers; Naive tone coefficient on Naive tone = 0.291 (high) vs 0.032 (low)

### SV Interaction Results (full sample)

SV is a type-agnostic stock-week measure of thread structural virality, standardised and lagged one period. Interacted with each lagged tone type in the Return equation:

- **SV × L.Rational tone → Return:** −0.0005 (p=0.026) — higher overall virality *dampens* Rational tone's return predictability
- **SV × L.Fanatic tone:** not significant in full sample
- **SV × L.Naive tone:** not significant

In **active weeks only** (N=81k), the pattern shifts: **SV × L.Fanatic tone → Return: +0.0006 (p=0.008)** — when discussion is more viral, Fanatic tone becomes more return-predictive.

### SSS Interaction Results (full sample)

SSS is a type-agnostic stock-week measure of sentiment-shifting power, standardised and lagged one period:

- **SSS × L.Rational tone → Return:** +0.0002 (p=0.008) ✓
- **SSS × L.Naive tone → Return:** +0.0004 (p=0.010) ✓
- **SSS × L.Fanatic tone → Return:** marginal (p=0.071)

Higher SSS **amplifies** the return predictability of both Rational and Naive tone — robust across full sample and active weeks. When comments have stronger sentiment-shifting power that week, Rational and Naive tone are more predictive of future returns.

### Joint SV + SSS (full sample)

When both enter together, the SSS results hold (Rational p=0.006, Naive p=0.005) and the SV dampening of Rational tone persists (p=0.030). The two moderators capture different dimensions and are not redundant.

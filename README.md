# Reddit Revision

## Why We Added Structural Virality (SV) and Sentiment Shift Score (SSS)

**Editor's letter, Comment 2:** *"Would it be possible to differentiate the type of social media interactions? It makes a huge difference seeing an anonymous post versus seeing Trump's tweets. You would need to uncover deeper insights and more interesting patterns from the data to provide sufficient contribution to the literature."*

The editor is asking us to go beyond simple tone measures and capture *how* information spreads and *whose* voice drives sentiment — not just what is said, but how far it reaches and how much it moves others.

**Structural Virality (SV)** addresses this directly. Rather than treating all posts equally, SV measures whether a discussion cascades through a chain of users (viral, high SV) or simply broadcasts from one source to many passive readers (star-shaped, low SV). A high-SV thread is more like a Trump tweet that gets retweeted and debated across many users — it has structural reach. A low-SV thread is more like an anonymous post that gets a few direct replies and dies. By interacting SV with investor type tone in the PVAR, we can ask: does the *way* Fanatic/Rational/Naive sentiment spreads — not just its content — affect stock returns and order flows?

**Sentiment Shift Score (SSS)** captures influence at the individual comment level: how much does a comment move its repliers away from their own prior tone baseline? This operationalises the editor's intuition that not all voices are equal — a comment with high SSS is one that actually changes how others express themselves, analogous to the influence a prominent figure's post has on the discourse.

---

## Why SSS Measures Genuine Influence (Not Just Participation Intensity)

**Reviewer 1, Comment 4:** *"While the authors argue that this variable reflects social influence, this claim requires further validation. This variable primarily captures the intensity of investors' subsequent participation and does not immediately indicate whether these follow-up commenters are genuinely 'influenced' by the original poster."*

The reviewer's concern is that follow-up commenting could reflect engagement intensity rather than true opinion change — someone might reply simply because they are active, not because the original post moved them.

SSS is constructed to address this directly. For each replier, we compute the **deviation of their reply tone from their own prior baseline** — the cumulative mean tone of all their previous posts (requiring ≥ 3 prior posts). This means SSS does not measure whether someone replied (participation), but whether their tone in that reply is *different from how they normally express themselves*. A replier who always posts positively and continues to do so is not counted as influenced. Only repliers who deviate from their own established tone pattern contribute to SSS.

This design separates influence (shifting someone's expressed sentiment relative to their own prior) from participation intensity (how many people replied or how actively they engage). A high-SSS comment is one that causes repliers to express themselves differently than they typically would — which is a closer operationalisation of genuine opinion influence than simple reply counts or engagement volume.

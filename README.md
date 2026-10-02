# prommer-answer-gap

**Can prommer.net answer the questions its own buyers ask, and can an agent prove it without making anything up?**

prommer.net exists to win two audiences: founders/operators evaluating Thomas Prommer as a counterparty, and press/podcast bookers looking for a sharp POV on agentic operations. This pipeline asks six questions chosen for those audiences, drafts answers from a sample of the live site, has a second agent re-check every answer against that corpus, and applies a code gate before writing `FAQPage` JSON-LD. Questions unsupported by the sampled corpus are held for investigation; that is not proof the information is absent from the site.

## Measured first (live, 2026-10-02)

- `sitemap.xml` is a sitemap **index** → 1 child → **476 URLs**. `robots.txt` and `llms.txt` present.
- Homepage JSON-LD has 21 types (Person, Organization, PodcastSeries, VideoObject…) but **no `FAQPage`** and no `dateModified`.
- `llms.txt`, the map the site gives AI agents, links `/en/services/advisory/`, which returns **HTTP 410 Gone**, and `/en/press/`, a **meta-refresh stub (78 chars of text)**. It **never mentions the speaking page**.
- Final run (`runs/20261002-091252/`): 11 fetch records produced **9 frozen source files (50,081 chars)**, one HTTP 410, and one followed meta-refresh hop. **4 of 6 answers published, 1 held after its repair round, 1 held as a "gap" that turned out to be my bug (break 6).** Planted fake stat and fake expert: **both held**. Four model calls (draft, verify, repair, re-verify), all timed and costed in the run folder.

**The finding that matters (corrected after review):** run 4 held *"Has he appeared on podcasts or spoken publicly, and on what topics?"* as a content gap. That was wrong. `/en/press/speaking/` exists (24k chars of text, six keynote topics such as "The AI-Augmented Organization" and "From CTO to CTAIO", and a booking form with a Podcast/Webcast option). My pipeline never fetched it, because its 8-page cap filled with `llms.txt` links first. The real finding is what that bug exposed: **`llms.txt` never mentions the speaking page, and it links a page that returns 410.** An agent that trusts the site's own map for AI, as mine did, will tell a podcast booker, one of the two named target audiences, that there's nothing there. Fix pack: add `/en/press/speaking/` to `llms.txt`, swap the 410 and the redirect stub for their final URLs, re-run this pipeline, and expect q5 to publish.

## Run it

```bash
python3 pipeline.py                               # live: fetch, draft + verify, optional repair, publish
python3 pipeline.py --replay runs/20261002-091252 # re-gate recorded responses, zero model calls
python3 grounding_gate.py --corpus runs/20261002-091252/corpus \
  --draft runs/20261002-091252/published-items.json --negative-control
```
Needs `python3` (stdlib only) and the `claude` CLI (`claude -p`, Sonnet 5.5) for the two agent steps.

## The workflow: steps and handoffs

```
MEASURE (code) → DRAFT (agent 1) → VERIFY (agent 2) → GATE (code) → [1 repair loop] → PUBLISH
```
1. **Measure** (`measure()`, urllib): sitemap index → child sitemaps + every page `llms.txt` links → follow meta-refresh → freeze plain text to `runs/<ts>/corpus/`. Output feeds both agents.
2. **Draft** (agent 1, `claude -p`): gets the corpus wrapped as *untrusted data*, plus 6 buyer questions. Must return JSON with verbatim evidence quotes, or `gap: true`. No outside knowledge.
3. **Verify** (agent 2, a separate call with a separate role prompt; it did not write the draft): re-reads the corpus and rules on each answer: supported / changed / unsupported. Same model weights, so this is a separation of roles, not independent consensus.
4. **Gate** (code): an item publishes only if (a) every number and capitalised name detected by the regex appears in the corpus **as a whole token**, (b) it has ≥1 evidence quote and each quote is verbatim in the corpus, and (c) the verifier said `supported`. Detection is heuristic: a single surname at the start of a sentence can be missed. Failures get **one** repair round (draft + re-verify with the gate's reasons), then are held.
5. **Publish**: passed items → `faq-jsonld.json` (schema.org FAQPage). Held items → `held.md` with the reason, for retrieval or content investigation. These are repository artifacts; nothing is deployed to prommer.net.

Every invoked model step saves its prompt, response, token count, cost and timing in
`runs/<ts>/{draft,verify,repair,reverify}.json`; the repair files exist only when the gate triggers that round.

## What broke, and what I changed

1. **Run 1 measured 2 pages, not 476.** `sitemap.xml` is a sitemap index, and my filter matched 0 URLs. The answers still came out confident, from the homepage alone. That's the dangerous part: nothing errored. **Fix:** follow child sitemaps, and take the pages `llms.txt` itself lists. Run 2: 10 pages. (Evidence in `runs/20261002-090738/`.)
2. **Run 2: the negative control FAILED.** A planted "4.3x more citations" passed the grounding gate. Cause: the gate used substring containment, and the homepage carries a fitness log (`34.3`, `94.3 kg`), so `4.3` "was in the corpus". **Fix:** claims must match as whole tokens, units included (`4.3x`). Re-run: both planted claims held. (`runs/20261002-090834/negative-control.txt` is the failing output, kept on purpose; `negative-control-after-fix.txt` is the pass.)
3. **The press page was empty.** `llms.txt` → `/en/press/` is a 78-char meta-refresh stub. **Fix:** follow one meta-refresh hop and record it in `measure.json`. That's also a real finding for the site, since llms.txt should point at the final URL.
4. **From an independent review:** a Codex session (a different model family) red-teamed the gate read-only over a local message bus. It found that a non-gap answer with an **empty evidence array** could pass. Fixed: one line in `gate()`. Its other findings are listed below as limits, because I didn't have time to fix them.

5. **Run 3 published copy that said "The corpus describes it as…".** Every fact was grounded, but nobody would put that sentence on a homepage. Grounded is not the same as publishable. **Fix:** a gate rule that rejects meta-language. Run 4: the repair round rewrote some answers, q4 still leaked the word after its one repair, so it was **held**, as designed. One repair, then hold; never loop until the model says what the gate wants.

6. **The "gap" was mine.** After run 4, a review checked the held q5 against the live sitemap and found `/en/press/speaking/`. Cause: `picked = (llms.txt links + sitemap hint matches)[:8]`, and `llms.txt` alone supplied 8 URLs, so no sitemap match was ever fetched. A selection defect looked like a site defect. **Not fixed in code within the window:** the fix is to reserve slots for sitemap hint matches, then re-run. I'm reporting it rather than claiming a run I didn't do.

## Limits (honest)

- The deterministic gate checks regex-detected numbers and capitalised names, not every entity. It misses a single surname at the start of a sentence. A wrong *relationship* between true names ("X founded Y" when he advises Y) is caught only by the verifier, which is a model.
- Evidence quotes must exist in the corpus, but code doesn't prove that they *entail* the answer. The corpus is pooled, so per-source provenance is lost.
- The verifier's JSON is trusted after parsing, and prompt-injection resistance is prompt-level only (the corpus is wrapped as data, with no schema allowlist).
- English pages only: 9 frozen source files from 11 fetch records out of 476 discovered URLs, chosen by `llms.txt` + URL hints (in run 4, `llms.txt` filled all 8 slots; see break 6). No answer-engine "before" measurement, which is the next step: ask Perplexity/ChatGPT these same 6 questions and record whether prommer.net is cited, before and after shipping the FAQ.

## Reused tooling

`grounding_gate.py` and the recon script come from my own assessment-prep toolkit, written before this test; I fixed the gate's substring bug during the test. The origin of the gate: in my own AEO audit tool, an unsourced attribution to a named third party once reached a paying client, who caught it. Since then I treat "named person or number with no source" as a build failure, not a style note. Built with Claude Code as the lead and Codex as an independent, read-only reviewer over the SecuredChat bus.

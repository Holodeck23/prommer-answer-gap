# <property> — <one-line what it does>

Built for the We The Flywheel Sr Agentic Engineer assessment, <date>. <N> minutes.

## What I measured first
<recon numbers: URLs, what's present/missing, one table. This is why the design is what it is.>

## What it does
MEASURE → DRAFT → VERIFY → GATE → PUBLISH. <one line per stage; which are model calls, which are code>

## Run it
```sh
<one command>          # fresh run (needs <KEY> or a local model)
<replay command>       # re-runs the gates on recorded responses, no model calls
```

## Evidence
- First run: <what happened> → `runs/<...>`
- Planted fault: a fake statistic and a fake named expert, both HELD → `runs/negative-control.txt`
- Final run: <counts published / held> → `runs/<...>`

## What broke and what I changed
<the failed run, the cause, the fix, the run after>

## Why the gate exists
An unsourced attribution once reached a paying client through an audit tool I built. The
client caught it. The fix was a check that fails the build when a named third party appears
without a source. This gate is the same rule, applied at publish time.

## Trust boundaries
Page text is data, never instructions. Models have no tools beyond <...>. Only gated items publish.

## Limits
<what V1 doesn't do and why it matters. Synthetic data where used.>

## Reused tooling
`grounding_gate.py` and `recon.py` are my own pre-existing utilities. AI coding assistance was used throughout.

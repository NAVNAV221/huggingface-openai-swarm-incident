# D5 analysis and replay

`detectors.py` separates objective service/network gates from semantic judgments. A foreign read is established
from write/read path + source-IP attribution; actor attribution, communication intent, responsive conventions,
coordinator behavior, and shared-information use require blind adjudication. Raw heuristics do not create a
positive result. Contaminated runs (≥2 incident signatures) are excluded from the clean primary set; one is a
warning/sensitivity case.

`coding.py export <run-dir>` creates condition-blind evidence. Two independent coders use the frozen rubric;
`coding.py kappa A.json B.json` computes per-field Cohen's κ. Put adjudicated labels only in
`analysis/adjudicated.json`. Scored runs with semantic candidates cannot be analyzed without adjudication.

`analyze.py RUN... --output telemetry/analysis` reports run-level Wilson and exact Clopper–Pearson intervals,
hierarchical secondary denominators, the complete-P2 Fisher primary comparison, contamination exclusions,
and a sanitized report with forced scale/capability/contamination/convention/motive limitations. Scored
conditions enforce N=60. `replay.py RUN` emits an escaped, CSP/no-script, fully offline HTML timeline with
app/proxy/service/network events; it remains gitignored with raw telemetry.

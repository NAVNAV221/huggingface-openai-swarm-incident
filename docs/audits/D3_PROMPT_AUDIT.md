# D3 prompt/salience audit record

**Bundle SHA-256:** `7f7d52c5c7034b796df035e9842404d6931b600cae5e281b45d8441e76df9377`

**Passing reviewer:** `cold:ollama/qwen2.5:7b:fresh-context`

**Result:** PASS on all frozen categories: no behavior hints, helper not salient, store not feed-shaped,
generic errors, neutral environment, non-shaping truncation, and null validity.

The reviewed canonical bundle includes the system prompt, exact treatment/control tasks, tool descriptions,
opaque DNS/environment layout, credential/list schema, generic errors, unadvertised analog-only fetch
behavior, lockstep scheduler, and whole-step truncation policy. Mechanical checks separately reject H1–H3
terms, advertised fetch helpers, and summarization. The content-addressed artifact and raw review remain in
gitignored runtime storage; any bundle change requires a new review.

A prior 3B cold review returned contradictory prose/category booleans and **failed**. It was not accepted or
used to launch agents. A second attempt initially exercised the same model because Compose omitted the
reviewer override; that wiring was fixed. A valid 7B review was then rejected only for a single enclosing
JSON code fence; the parser was changed to accept that exact structure while retaining strict JSON/schema/
no-trailing-prose checks. The resulting coherent fresh 7B review passed.

The unadvertised depot fetch endpoint was separately exercised from a verification sandbox: the exact
`assets.test` analog URL returned only the mock artifact; `http://example.com/` returned generic 404 without
being fetched. Direct agent access to origin/hub remains denied. No experiment agent has run at this point.

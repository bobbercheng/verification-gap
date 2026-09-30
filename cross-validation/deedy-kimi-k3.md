# Kimi K3, Deedy, and the P3 replication

This note separates three claims that are easy to conflate: Deedy's public
all-six Kimi K3 result, our Kimi P3 replication, and GLM-5.2's later repair of
the Kimi-authored proof. The scores below came from model reviewers, not the
IMO jury.

## Deedy's public Kimi K3 result

The immutable public authority is
[`deedy/imo-2026@dbe8723`](https://github.com/deedy/imo-2026/tree/dbe872307883296c5f06bf8bcb90e6bfd0879364).
Its Kimi K3 campaign scored **36/42 on the first pass**: P1, P2, P4, and P5
received 7/7, P3 received 5/7, and P6 received 3/7. Reviewer-guided repair
rounds then brought P3 and P6 to 7/7, producing a final **42/42** result. The
defect feedback did not include another solution.

For P3 specifically, Deedy's first pass was one longitudinal lineage across
four fresh contexts sharing a durable workspace, not a best-of-four sample.
The contexts completed 71 logical model-loop turns and 90 tool calls before
freezing the 5/7 candidate. Two later repair contexts completed 27 turns and
28 tool calls before the final 7/7 result.

## Our Kimi K3 P3 replication

Our replication covered **P3 only**. Kimi K3 was given the official statement
and a Deedy-style direct-model environment with Bash, read, and write tools; it
was not shown Deedy's answer or proof. Three fresh no-review contexts shared
one model-visible workspace. After 42 completed normal turns, the lineage had
independently found the exact formula and both load-bearing universal proof
mechanisms. The frozen candidate scored a strict **6/7**, with two localized
edge-case defects:

- candidate SHA-256:
  `5a75aa5c50ee7b18bdd20a85e5e8e2a901f8892ae2d4108bc7463b38bfaebce8`;
- defect review SHA-256:
  `ff5a2dc1377b398a99890cd16c9aa5100da43d2ee4199b6b15b222e2149d927a`.

The first Kimi repair attempt was censored by a pre-response upstream 429 after
two completed read-only turns. A separately staged attempt started from the
same frozen 6/7 candidate and defect review, authored a corrected proof, and
passed a fresh blind GPT-5.6-Sol review at **7/7 with no defects**:

- corrected candidate SHA-256:
  `f7bcae33fcdd490d3db226e9724cf6177e1d8235dedc6c53c70fa5fd018e6874`;
- blind review SHA-256:
  `8a68451199e4d863f88307778603e86fe7ec0548e87252f24fe1a9181ecec1c6`.

This is an **outcome-level P3 replication**. It is not a fresh local run of all
six problems, a copy of Deedy's proof, or a protocol-faithful statistical
estimate of Kimi's success rate.

## GLM-5.2 comparison

GLM-5.2 provisionally resolved P1, P2, P4, P5, and P6 under the same core
Portfolio Transfer process used for GPT-5.6-Sol. After several days and
substantial P3-specific workflow enhancements, its strongest clean independent
P3 artifact remained **2/7**:

- independent GLM P3 candidate SHA-256:
  `382f74392d588d6e1c0f7e34be0aa0012a1533b0f10ab689ddf8f5be57cabe1b`.

GLM-5.2 later received the frozen Kimi 6/7 candidate plus its localized defect
review. It produced a corrected proof that passed the same blind-review gate at
**7/7 with no defects**:

- corrected GLM candidate SHA-256:
  `bfb7a020a5b191b5463366b04582a35cf2ea82c939a050f303f34a7c89a9a6e7`;
- blind review SHA-256:
  `e08435a9fca1bde64c2e6b4e74ad4099c3de66ff952bfb4e166f94066638b209`.

This is evidence of strong reviewer-guided repair after structural closure,
not an independent GLM-5.2 solution of P3. The independent GLM campaign is
therefore recorded as **5/6**.

## Interpretation and evidence boundary

P3 exhibited a structural repair threshold: below it, both universal proof
branches still had to be invented; above it, review reduced the work to finite
local corrections. Deedy's 5/7 candidate is the lowest observed successful
repair seed, while our 6/7 candidate was separately repaired to 7/7 by Kimi K3
and GLM-5.2 from the same parent and defect list.

The digests above identify the retained local artifacts and receipts. Their
raw provider traces are not duplicated in this public repository. Accordingly,
this note is a public provenance summary; Deedy's pinned repository remains the
fully public authority for the all-six Kimi K3 campaign.

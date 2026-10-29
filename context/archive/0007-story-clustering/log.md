# 0007 – Log

## 2026-10-29
- Proposed. Explored real DB with a throwaway word-overlap script: found the four groups
  above and the HN "Toxic Experts" false positive (min-denominator overlap on an empty text).
- Approved. Retention became 7 days (separate commit e0fab4e); empty stories are cleaned up here.
- Real data: iPhone Duo items are Oct 20/25/26, so 48 h fixed window → rolling 3-day window.
  "duo" and "s19" are 3 chars, so key words are ≥ 3 chars plus stopwords.
- First run on a DB copy: Spain (4) and S19 (2) grouped; Markle, iPhone Duo and Israel
  election (a real pair not in the proposal) missed: long headlines dilute Jaccard (0.17–0.23).
- Checked every same-language pair within 3 days: "≥ 2 shared title key words" hits exactly
  the true pairs, nothing else. Added it with a Jaccard floor of 0.15 for safety.
- Result on real data: 89 articles → 82 stories; groups Spain 4, Markle 2, Israel 2,
  iPhone Duo 2 (Oct 25/26), S19 2. "Toxic Experts" alone; Oct 20 announcement separate.
- Story cleanup runs at the start of clustering (articles that became duplicates or were
  deleted by retention leave; empty stories deleted), so prune.py needed no changes.
- Known cosmetic issue: story title can be a "Watch: …" video headline (earliest article
  of the top-weight source). Leave for the digest change to choose display titles.
- Tests: 54 passed (7 new). Real DB: user_version 2 → 3. Verified and archived.

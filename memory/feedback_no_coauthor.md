---
name: feedback-no-coauthor
description: Never add Co-Authored-By Claude lines to git commits
metadata:
  type: feedback
---

Never add `Co-Authored-By: Claude ...` to commit messages. User explicitly removed it from all 50 commits in git history.

**Why:** User doesn't want Claude listed as contributor in their git history.

**How to apply:** All commits — no exceptions, no Co-Authored-By line ever.

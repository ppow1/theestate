# WP-0527 Validation Notes

Staged tests demonstrate:

- cross-domain search across work packages, residents, validation, decisions, Git evidence, artifacts, and conversations;
- category and tag filtering;
- direct Office navigation destinations on returned results;
- stale result exclusion and missing source warnings;
- safe registered action invocation through `SafeAction`;
- rejection of arbitrary shell, Python, URL, handler-style, and unknown commands;
- recent searches and pinned queries only when settings permissions allow them.

Validation command:

```bash
PYTHONPATH=collaboration/workstreams/WP-0527/staged pytest -q collaboration/workstreams/WP-0527/staged/test_office_unified_search.py
```

This is staged work only and is not installed into active Office files.

# Repository Branch Authority

Status: canonical repository policy

## Rule

For both `ppow1/Riverview` and `ppow1/theestate`, `main` is the default and
only normal development/documentation authority unless the current work
package explicitly names another branch.

- An existing branch is not authorization to use it.
- A current checkout branch is not authorization to use it.
- A historical report location or previous Codex usage is not authorization.
- A worker that finds itself on a non-main branch must stop before writing
  unless the current work package explicitly authorizes that branch.
- Historical branches are retained only for forensic or recovery purposes.
- Historical contents must not be assumed missing from `main` merely because
  the branch still exists.
- Do not resume development from a historical branch.
- New named branches require explicit package or operator authorization.

Before modifying either repository, verify the work-package branch instruction,
the checkout, and `origin/main`. If no non-main branch is explicitly named,
use `main`.

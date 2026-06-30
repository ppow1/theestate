# Estate Change Validation Standard
Version: 0.1
Status: Active
Owner: Archives / Engineering

No Estate Change is complete until validation passes before commit.

Minimum validation for code changes:

1. Syntax validation
   - Python files must pass py_compile.

2. Runtime validation
   - Affected CLI commands must run successfully.

3. Git validation
   - git status must be reviewed before commit.
   - git log must confirm the final commit.

4. Ledger validation
   - The Estate Change must be recorded in the ledger.
   - The devlog must receive a corresponding entry when applicable.

5. Repair rule
   - If a committed Estate Change is discovered broken, the repair receives its own Estate Change number.
   - The broken change is not erased from history.
   - The repair explains what was corrected.

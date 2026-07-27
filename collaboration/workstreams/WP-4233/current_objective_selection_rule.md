# Current-objective selection rule

`get_current_objective` examines persisted `objective.created_or_correlated` events returned by the runtime, excludes objectives with `objective.completed`, and returns a projection only when exactly one explicit nonterminal objective remains. Zero candidates returns `NO_RECORD`; more than one returns `AMBIGUOUS_CORRELATION`. The current user prompt is never treated as an objective.

Explicit `get_objective_by_id` is the only selection path when an operator supplies an ID.

# Estate Knowledge Store migrations

The SQLite projection is owned by `estate.core.estate_knowledge_index` and
implemented by `estate.core.estate_knowledge_store`. `MIGRATIONS` is an
ordered, versioned migration map; the store applies it transactionally and
records the version in SQLite `PRAGMA user_version`. The committed schema
contract is `data/schemas/estate_knowledge_store_v1.schema.json`.

The current migration is version 1. A database with a newer version fails
closed. Runtime state is generated at
`runtime/search/estate_knowledge_index.sqlite3` and is ignored by Git. It can
be rebuilt from Git-governed files with:

```text
python -m estate.cli.main knowledge-index --backend sqlite rebuild --root ESTATE_ROOT
```

The database is a rebuildable relational projection, not a replacement for
Git, governed JSON contracts, evidence, or canonical troubleshooting truth.

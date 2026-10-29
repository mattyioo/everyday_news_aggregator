# Context

Everything we know and plan about **everyday_news** lives here, as Markdown only.

```
context/
├── foundation/   # long-lived truth about the project (vision, architecture, roadmap)
├── change/       # active changes: one subfolder = one change in flight
└── archive/      # finished changes, moved here unchanged once done
```

## foundation/

Stable documents that describe *what* the project is and *how* it is built.
They change rarely, and only on purpose (a change that alters the foundation
must update the relevant file as one of its tasks).

| File | Purpose |
|---|---|
| `vision.md` | Why the app exists, what "bullshit" means, what success looks like |
| `architecture.md` | Components and data flow |
| `tech-stack.md` | Languages, libraries, storage, and why |
| `conventions.md` | Code style, naming, testing rules |
| `roadmap.md` | Phases of the project and the changes in each |
| `decisions.md` | Decision log and open questions |

## change/

One folder per change, named `NNNN-short-slug` (e.g. `0001-project-skeleton`).
Each change folder contains exactly three files:

| File | Purpose |
|---|---|
| `proposal.md` | Why, what, scope, out of scope, acceptance criteria |
| `plan.md` | Tasks as checkboxes, grouped by stage |
| `log.md` | Dated notes: progress, surprises, decisions made along the way |

Every change moves through the same **stages**:

1. **Propose** – write `proposal.md`. Stop and get approval.
2. **Plan** – break the work into tasks in `plan.md`.
3. **Build** – implement tasks, ticking boxes and writing to `log.md`.
4. **Verify** – run the app/tests against the acceptance criteria.
5. **Archive** – update `foundation/` if needed, then move the folder to `archive/`.

The current stage is written at the top of `proposal.md` (`Stage: Propose`).

## archive/

Completed changes, moved as-is from `change/`. Never edited after archiving.
`archive/README.md` keeps a one-line index of everything archived.

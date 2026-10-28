# Evidence and adaptation

Contents: new design, adapting research, repairing a design, labels and sources.

## A new design

Establish the consumer contract first. Then list producers and side channels, and trace who is responsible for each step, normalization, storage, calls, retry behavior and output. Read the actual code and the primary provider documentation for routes, permissions, limits and lifecycle events. A provider capability does not prove the local system implements it.

For a question of "what is the golden best practice", research the current answer from primary sources (vendor docs, standards, the project's own source) and date it, instead of writing a plausible one. A research subagent helps if your tool has one.

## Adapting research

Keep the source research as evidence. Turn its findings into a navigable flow rather than copying its research order, and carry unresolved feasibility questions forward as open items.

## Repairing an existing design

Read the existing note and diagram, the issue that asked for it and the review history. Record the accepted choices before rewriting. A presentation repair does not reopen settled scope, protocol, responsibility or rollout decisions. Correct a contradicted claim with a source, and say whether the correction is a fact or a new design choice.

## Labels

- `current`: code or runtime evidence, linked as `file:line` plus the local commit sha you read.
- `proposed`: a design decision, linked to its reason.
- `untested`: say what proof is missing. Never write an inferred route or behavior as if it were observed; an unknown route is an open item.

## Each flow step explains

The trigger, the owning component, the concrete action, the result and the meaningful failure path. Pseudocode lets a reader trace methods and routes without presenting fiction as existing code. Register each route once and reference it by ID from the steps.

## Separate paths stay separate

Do not flatten different paths into one invented sequence. Group webhook, polling, authorization, media and policy paths when the evidence calls for it, and give renewal, expiry, cleanup and failure transitions their own side diagram when they are not part of the arrival path.

## Where the facts come from

Manifests before searches: `package.json`, `go.mod` or `pyproject.toml`, deployment config, the CI workflow files, the migrations folder and the READMEs answer most structural questions. Use the Grep and Glob tools on a narrow path, not a recursive shell search.

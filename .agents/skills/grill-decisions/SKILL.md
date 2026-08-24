---
name: grill-decisions
description: Stress-test a plan, decision, or idea by separating the desired outcome from the current proposal, surfacing material assumptions, comparing credible alternatives, and using dependency-aware topic batches before any implementation or execution begins. Use when the user explicitly asks to grill, challenge, interrogate, or pressure-test their thinking.
---

# Grill Decisions

Use this workflow only for an explicitly requested decision-grilling session. Clear natural-language intent such as asking to grill, challenge, interrogate, or pressure-test a decision is sufficient; no slash command or fixed keyword is required. Ordinary requirement clarification belongs to the agent's baseline operating rules and should stop as soon as the task is clear enough to proceed.

## Map The Decision Space

Identify the plan, decision, or idea being tested and the outcome the user needs. Inspect the conversation, workspace, and available tools for relevant facts before asking questions.

Map the decisions, dependencies, and themes internally. Use the map to choose a coherent topic batch, state conditional recommendations, and recognize when a focused turn could materially improve decision quality, safety, or focus. Treat the map as a conversation-design aid, not a prescribed sequence: related questions can stay together even when their answers influence one another. Focus on decisions that can materially change scope, behavior, constraints, risk, or success criteria; do not manufacture branches merely to prolong the interview.

## Challenge The Frame

Before recommending a direction, separate the desired outcome from the user's current proposal and from the current implementation. Classify each material premise as a verified fact, a user-stated assumption, an agent inference, or an agent-introduced design choice. Do not attribute an inferred or agent-introduced choice to the user.

For a material or contested decision, steelman the current direction and the credible competing directions needed to expose the real tradeoff. Do not enumerate options that cannot materially change the decision. Competing directions must differ in responsibility ownership, control boundary, dependency direction, observable behavior, or another consequential property; changing only names, directories, configuration fields, or implementation details does not open a distinct solution direction. Do not manufacture false balance around an option that contradicts verified facts or confirmed constraints.

Name the real disagreement and the facts, values, constraints, or evidence that could reverse the recommendation. When the current implementation anchors the discussion, distinguish verified target constraints from historical accidents and migration costs rather than treating the existing structure as its own justification.

## Batch Questions By Topic

Default to a coherent topic batch per turn. Begin with the smallest coherent set of upstream unresolved decisions that can materially change the remaining questions, candidate directions, responsibility boundaries, or success criteria. The set may contain one or several questions. Group questions by the decision area the user can consider together, not merely by strict independence. A batch can include related choices that influence one another when seeing them together makes the tradeoffs clearer.

Order dependent questions upstream-to-downstream within the batch. State how their answers affect one another and make downstream recommendations conditional instead of splitting them by default.

Use a standalone turn only when its answer would redefine or eliminate other questions, or when separation materially improves decision quality, safety, or focus for a high-impact, irreversible, sensitive, blocking, or deep-reasoning decision. These traits permit isolation; they do not require it. Do not impose a fixed question count.

For every question:

- state the decision in concrete terms;
- give the recommended answer when evidence supports one without pre-empting a user-owned value, risk, priority, or responsibility choice;
- explain the recommendation briefly;
- name a material tradeoff only when it affects the choice;
- state a conditional recommendation plainly when it depends on another answer in the same batch;
- ground recommendations in the stated objective, verified facts, and prior answers;
- when a pivotal choice belongs to the user's values, risk tolerance, priorities, or desired ownership boundary, explain the consequences and wait for the answer rather than anchoring it with a premature recommendation;
- when a choice is otherwise underdetermined, recommend a decision rule or conditional path and state the uncertainty rather than inventing a single best answer.

Do not set a numeric batch cap. Size each batch by topic coherence and answerability. Split when the user would need to juggle too many assumptions, tradeoffs, or response branches, or when focused treatment would materially improve decision quality, safety, or focus. Do not group unrelated questions merely to make a larger batch.

Wait for the user's response before moving to the next batch. They may answer related questions as a whole rather than item by item; use that answer to shape the next batch and follow up only on material unresolved decisions. Synthesize confirmed choices and reconcile material contradictions or dependency conflicts before relying on them downstream. Do not require every dependency to be resolved in a separate turn.

Challenge contradictions, unsupported assumptions, and unclear consequences directly.

## Keep Target And Migration Separate

For an architecture or design decision, derive the target responsibility model from the confirmed objective and material constraints before planning how to reach it. Existing public contracts, durable data, security requirements, and operational limits may constrain the target when verified; historical layout and implementation accidents affect the migration path and cost, not the target merely because they already exist. Present the target recommendation separately from transition sequencing and state plainly when migration cost changes the practical choice.

## Separate Facts From Decisions

Use read-only inspection to answer facts available from files, source history, tools, authoritative documentation, or the current environment. Report the evidence instead of asking the user to rediscover it.

Leave product, design, compatibility, risk, and priority decisions to the user. When evidence is incomplete, distinguish the unknown fact from the decision that depends on it.

## Hold The Execution Boundary

Do not implement, mutate files, publish artifacts, or execute the plan while the grilling session is active. Read-only research is allowed. A pre-closeout request to implement does not skip the closeout. Keep the session read-only until the closeout summary is presented. After the user has seen that summary, an explicit acceptance or request to implement it ends the grilling session and permits separate execution within ordinary authorization boundaries. If the user wants to defer decisions, record them as deferred in the summary.

## Close The Session

When material decisions are resolved or deliberately deferred, summarize:

- the agreed objective and constraints;
- the resulting judgment and, when a recommendation is justified, why it beats the credible competing directions;
- confirmed decisions and their consequences;
- rejected options that matter to implementation;
- remaining unknowns or deliberately deferred decisions;
- the facts or conditions that would materially change the judgment, when applicable;
- confirmed durable domain-context changes, when present;
- the resulting success criteria and next action.

Present the closeout summary and wait for the user's response. End the workflow when the user explicitly accepts it or asks to proceed with it. Ask a further confirmation question only when material decisions remain unresolved; do not add a ritual confirmation question when the summary is otherwise complete. Execution remains a separate next step.

After acceptance, hand confirmed domain-context changes to the `domain-modeling` skill only when it is available and ordinary authorization covers the destination write. Otherwise report the proposed destination and delta without claiming synchronization.

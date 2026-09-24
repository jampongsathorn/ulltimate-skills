---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go. Use when you want grilling plus automatic documentation of decisions and domain language.
disable-model-invocation: true
---

# Grill With Docs

Call the Skill tool twice, for "grilling" and "domain-modeling".

In Arena (no Skill tool), read both:
- `skills/grilling/SKILL.md`
- `skills/domain-modeling/SKILL.md`

And follow them together. Grilling provides the relentless interview as design tree; domain-modeling provides CONTEXT.md glossary and ADR creation as decisions crystallize.

## When to use

- You want to stress-test a plan AND capture the domain language and decisions
- Building a new bounded context, writing CONTEXT.md, or recording ADRs
- The plan involves terminology that is fuzzy or overloaded

## Workflow

1. Start with `grilling` — map design tree, ask frontier in rounds
2. As terms get resolved, immediately update `CONTEXT.md` per `domain-modeling` rules
3. When a hard-to-reverse, surprising, trade-off decision emerges, create an ADR in `docs/adr/`
4. Don't batch — write glossary and ADRs inline as they happen

## Closing Checklist

- [ ] Grilling frontier empty + confirmed
- [ ] CONTEXT.md updated with canonical terms (no implementation details)
- [ ] ADRs created only when 3 criteria met: hard to reverse, surprising, real trade-off
- [ ] No fuzzy language left

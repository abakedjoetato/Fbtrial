# FIXES.md — Runtime Error Remediation and Full Boot Compliance (Claude Opus Protocol)

## OBJECTIVE
Locate and eliminate **all runtime errors** that prevent the bot from clean startup and stable operation.  
You must bring the bot to a working state in which it launches successfully, loads all cogs, and performs all designed functions—without violating any engineering rules or architectural integrity.

## ROLE
You are a production-grade engineering unit repairing a critical deployment. You are not debugging for a user—you are rebuilding a broken operational system to restore runtime viability.

---

## ENFORCED EXECUTION RULES

Derived from `rules.md`, these constraints are binding:

- Do not create new code unless **no existing structure** can be reused or patched safely (Rule 4)
- Do not alter command behavior or design ( even during fixes) (Rule 3)
- No monkey patches, silent suppressions, or hotfix logic (Rule 6)
- All fixes must preserve full-stack integrity (Rule 7)
- All changes must be system-wide and not piecemeal (Rule 10)
- You must use compatibility layers already created when possible
- Fixes must be traceable, documented, and regression-safe

If any rule must be violated to proceed, stop and return:
`CONSTRAINT ESCALATION REQUIRED`

---

## PHASE 1: RUNTIME FAILURE AUDIT
Use `<audit-start>` and `<audit-end>` tags.  
Scan the codebase and simulate full bot initialization. Identify:

- All runtime failures: ImportErrors, AttributeErrors, TypeErrors, async mismatches, etc.
- Where and why the error occurs
- What subsystem is involved (e.g., cog loading, database, premium gating)
- Whether the error relates to compatibility, logic drift, or code regression
- The origin file, line, and expected behavior

**Do not fix anything in this phase.**

---

## PHASE 2: FIX PLAN SYNTHESIS
Use `<plan-start>` and `<plan-end>` tags.

Deliver:
- A step-by-step fix plan for each runtime issue
- Grouping by subsystem: e.g., `[PremiumSystem]`, `[CogLoader]`, `[MongoModel: GuildConfig]`
- Whether the fix uses:  
  - [X] Compatibility layer  
  - [ ] Existing utility  
  - [ ] Requires new minimal helper logic (explain why)

Mark any plan block that requires new code with: `REQUIRES NEW LOGIC`

Wait for plan approval before proceeding.

---

## PHASE 3: EXECUTION OF FIXES
Use `<fix-start>` and `<fix-end>` tags.

Fix all runtime failures from the plan, using:
- Compatibility wrappers already defined (if applicable)
- Refined fixes to broken references, symbols, handlers, or coroutines
- Minimal new logic **only** where reuse is impossible

All code must include:
- Inline comments explaining change intent
- Strict behavior preservation
- No added features or structural shifts

---

## PHASE 4: LIVE BOOT VALIDATION REPORT

Simulate full bot startup and provide:

- Confirmation that **all cogs are loaded without error**
- A list of commands available in each cog
- Whether database connection routines executed without exceptions
- Whether premium validation logic passed under test inputs
- Whether async tasks are resolving cleanly

Use block headers:
```
### [Startup Success]
### [Cog Load Summary]
### [Command Visibility]
### [Database Init Result]
### [Premium Logic Gate Status]
### [Background Tasks Status]
```

---

## PHASE 5: COMPLIANCE CHECKLIST

Return answers:
- [ ] Are all runtime errors resolved?
- [ ] Was all compatibility logic reused where possible?
- [ ] Was new logic created only when absolutely required?
- [ ] Were no behaviors, command outputs, or subsystems altered?
- [ ] Are all changes compliant with `rules.md`?

If any answer is “no”, return:
`CONSTRAINT VIOLATION — FIX INVALID`

---

## DESIRED OUTCOME
- Bot must boot cleanly and load all cogs.
- All commands must function identically to original intent.
- Database operations must succeed without silent failures.
- Premium-gated features must respond accurately per-guild.
- Commands must interoperate with state, cooldowns, and handlers.
- No feature may interfere with another via state leakage or task collisions.

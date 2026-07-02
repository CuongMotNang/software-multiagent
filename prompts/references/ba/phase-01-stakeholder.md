# Phase 1: Stakeholder Analysis

## Table of Contents
- [Workflow](#workflow)
- [Stakeholder Identification](#stakeholder-identification)
- [Power/Interest Matrix](#powerinterest-matrix)
- [RACI Matrix](#raci-matrix)
- [Communication Plan](#communication-plan)
- [Output Templates](#output-templates)

## Workflow

1. Identify all stakeholders (internal + external)
2. Classify using Power/Interest matrix
3. Define RACI for each major deliverable
4. Create communication plan
5. Validate with project sponsor

## Stakeholder Identification

Ask the user these questions to identify stakeholders:

- Who is the project sponsor / budget owner?
- Who are the end users (primary and secondary)?
- Who are the subject matter experts (SMEs)?
- Which departments are affected?
- Are there external stakeholders (vendors, regulators, customers)?
- Who has approval authority?
- Who will be impacted by the change but has no direct involvement?

Categorize stakeholders into:

| Category | Examples |
|----------|----------|
| Decision Makers | Sponsor, Steering Committee, Product Owner |
| Influencers | SMEs, Department Heads, Architects |
| End Users | Primary users, Secondary users, Admin users |
| Support | IT Ops, QA, Training, Help Desk |
| External | Regulators, Vendors, Partners, Customers |

## Power/Interest Matrix

Classify each stakeholder on two axes:

```
        HIGH POWER
            │
  Keep      │    Manage
  Satisfied │    Closely
            │
────────────┼────────────
            │
  Monitor   │    Keep
  (Minimal) │    Informed
            │
        LOW POWER
   LOW INTEREST    HIGH INTEREST
```

**Engagement strategy per quadrant:**
- **Manage Closely** (High Power, High Interest): Regular 1:1 meetings, involve in key decisions
- **Keep Satisfied** (High Power, Low Interest): Periodic executive summaries, escalate blockers
- **Keep Informed** (Low Power, High Interest): Regular status updates, demo invitations
- **Monitor** (Low Power, Low Interest): Include in broad communications only

## RACI Matrix

For each deliverable/activity, assign:
- **R** (Responsible): Does the work
- **A** (Accountable): Final decision maker (exactly one per item)
- **C** (Consulted): Provides input (two-way communication)
- **I** (Informed): Kept in the loop (one-way communication)

**Example:**

| Activity | Sponsor | PM | BA | Dev Lead | QA Lead | End User |
|----------|---------|----|----|----------|---------|----------|
| Approve BRD | A | C | R | C | I | C |
| Write User Stories | I | C | R | C | C | C |
| Sign-off UAT | A | C | I | I | R | R |

## Communication Plan

For each stakeholder group, define:

| Stakeholder | Info Need | Frequency | Channel | Owner |
|-------------|-----------|-----------|---------|-------|
| Sponsor | Progress, Risks, Decisions | Weekly | 1:1 Meeting | PM |
| Dev Team | Requirements, Clarifications | Daily | Slack + Stand-up | BA |
| End Users | Changes, Training | Bi-weekly | Email + Demo | BA |

## Output Templates

When producing stakeholder analysis, generate:

1. **Stakeholder Register** (table): Name, Role, Category, Power, Interest, Engagement Strategy
2. **Power/Interest Matrix** (Mermaid quadrant chart or visual)
3. **RACI Matrix** (table per major deliverable)
4. **Communication Plan** (table)

Use xlsx skill for spreadsheet output if user requests it, or markdown tables for quick review.

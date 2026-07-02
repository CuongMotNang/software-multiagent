# Phase 3: Requirement Documentation

## Table of Contents
- [Workflow](#workflow)
- [Requirement Types](#requirement-types)
- [User Story Writing](#user-story-writing)
- [Use Case Writing](#use-case-writing)
- [BRD Template](#brd-template)
- [SRS Template](#srs-template)
- [PRD Template](#prd-template)
- [FRD Template](#frd-template)
- [Non-Functional Requirements](#non-functional-requirements)
- [Requirement Quality Checklist](#requirement-quality-checklist)

## Workflow

1. Determine document type needed (User Stories, BRD, SRS, PRD, FRD)
2. Gather input: elicitation results, stakeholder needs, existing documentation
3. Draft the document using appropriate template
4. Review against quality checklist
5. Submit for stakeholder review
6. Incorporate feedback and finalize

## Requirement Types

| Type | Description | Example |
|------|-------------|---------|
| **Business Requirement** | High-level need of the organization | "Reduce order processing time by 40%" |
| **Stakeholder Requirement** | Need of a specific stakeholder group | "Managers need real-time dashboard" |
| **Functional Requirement** | What the system must do | "System shall send email notification on order status change" |
| **Non-Functional Requirement** | How the system must perform | "Page load time < 2 seconds" |
| **Transition Requirement** | Needed for migration/go-live only | "Migrate 5 years of historical data" |

## User Story Writing

### Format
```
As a [user role],
I want to [action/goal],
So that [business value/benefit].
```

### INVEST Criteria
- **I**ndependent: Can be developed without depending on other stories
- **N**egotiable: Details are discussed, not dictated
- **V**aluable: Delivers value to the user or business
- **E**stimable: Team can estimate effort
- **S**mall: Completable in one sprint
- **T**estable: Clear criteria to verify completion

### Acceptance Criteria (Given/When/Then)
```
Given [precondition/context],
When [action performed],
Then [expected outcome].
```

### Example

**User Story:**
```
As a customer,
I want to filter products by price range,
So that I can quickly find products within my budget.
```

**Acceptance Criteria:**
```
AC1: Given I am on the product listing page,
     When I set min price = 100 and max price = 500,
     Then only products priced between 100-500 are displayed.

AC2: Given I have applied a price filter,
     When I clear the filter,
     Then all products are displayed again.

AC3: Given no products exist in the selected price range,
     When I apply the filter,
     Then a "No products found" message is displayed.
```

### Story Splitting Techniques
When a story is too large, split by:
- **Workflow steps**: Registration → Login → Profile Edit
- **Business rules**: Simple order → Order with discount → Order with coupon
- **Data variations**: Search by name → Search by date → Search by status
- **Operations**: CRUD — Create, Read, Update, Delete separately
- **User roles**: Admin view → Manager view → User view
- **Happy/Unhappy paths**: Success flow → Error handling → Edge cases

## Use Case Writing

### Use Case Template

```
Use Case ID: UC-[number]
Use Case Name: [Verb + Noun]
Actor(s): [Primary actor, Secondary actors]
Precondition: [What must be true before]
Trigger: [What initiates this use case]

Main Flow (Happy Path):
1. Actor does X
2. System responds with Y
3. Actor does Z
4. System confirms

Alternative Flows:
2a. If [condition]:
    2a.1. System does [alternative]
    2a.2. Return to step 3

Exception Flows:
3a. If [error condition]:
    3a.1. System displays error message
    3a.2. Use case ends

Postcondition: [What is true after successful completion]
Business Rules: [BR-001, BR-002]
```

## BRD Template

Business Requirements Document — focuses on WHY and WHAT at the business level.

```
1. Executive Summary
   - Project background and business context
   - Problem statement
   - Proposed solution (high-level)

2. Business Objectives
   - Primary objectives with measurable KPIs
   - Success criteria
   - Alignment with organizational strategy

3. Scope
   - In-scope items
   - Out-of-scope items
   - Assumptions
   - Constraints

4. Stakeholder Analysis
   - Stakeholder list with roles
   - RACI matrix (reference Phase 1 output)

5. Business Requirements
   - BR-001: [Requirement description]
     - Priority: [Must/Should/Could/Won't]
     - Source: [Stakeholder/Document]
     - Acceptance Criteria: [How to verify]

6. Business Process Overview
   - Current state (AS-IS) summary
   - Future state (TO-BE) summary
   - Key changes

7. Risks and Dependencies
   - Risk register with mitigation strategies
   - External dependencies

8. Cost-Benefit Analysis (if applicable)
   - Estimated costs
   - Expected benefits (quantified)
   - ROI timeline

9. Approval and Sign-off
   - Approver list with signature lines
```

## SRS Template

Software Requirements Specification — focuses on WHAT the system must do technically.

```
1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Definitions, Acronyms, Abbreviations
   1.4 References
   1.5 Document Conventions

2. Overall Description
   2.1 Product Perspective (context diagram)
   2.2 Product Features (high-level)
   2.3 User Classes and Characteristics
   2.4 Operating Environment
   2.5 Assumptions and Dependencies

3. System Features
   3.1 Feature: [Feature Name]
       3.1.1 Description
       3.1.2 Functional Requirements
             FR-001: [Requirement with shall statement]
             FR-002: ...
       3.1.3 Use Cases (reference)
       3.1.4 Business Rules

4. External Interface Requirements
   4.1 User Interfaces (wireframe references)
   4.2 Hardware Interfaces
   4.3 Software Interfaces (API specifications)
   4.4 Communication Interfaces

5. Non-Functional Requirements
   5.1 Performance
   5.2 Security
   5.3 Reliability / Availability
   5.4 Scalability
   5.5 Usability
   5.6 Compliance

6. Data Requirements
   6.1 Data Model (reference Phase 5 output)
   6.2 Data Dictionary
   6.3 Data Migration Requirements

7. Appendices
   - Traceability Matrix
   - Glossary
```

## PRD Template

Product Requirements Document — product-centric, commonly used in Agile/Product orgs.

```
1. Overview
   - Problem Statement
   - Target Users / Personas
   - Value Proposition

2. Goals and Success Metrics
   - Primary goal + KPI
   - Secondary goals
   - Anti-goals (what this is NOT)

3. User Stories / Jobs-to-be-Done
   - Epic 1: [Name]
     - User Story 1.1
     - User Story 1.2
   - Epic 2: [Name]
     - ...

4. Feature Requirements
   - Feature A
     - Description
     - User flow
     - Acceptance criteria
     - Priority (P0/P1/P2)
     - Dependencies

5. Design & UX
   - Wireframes / Mockups (reference)
   - Interaction patterns
   - Accessibility requirements

6. Technical Considerations
   - Architecture constraints
   - Integration points
   - Performance requirements
   - Security requirements

7. Release Plan
   - MVP scope
   - Phase 2 scope
   - Future considerations

8. Open Questions & Risks
```

## FRD Template

Functional Requirements Document — detailed functional specifications for development.

```
1. Introduction
   - Purpose and scope
   - Related documents (BRD, PRD references)

2. Functional Requirements by Module
   Module: [Module Name]
   
   FR-[Module]-001:
     Description: [System shall...]
     Input: [What triggers this]
     Processing: [Business logic / rules]
     Output: [Expected result]
     Validation Rules: [Data validation]
     Error Handling: [Error scenarios]
     Priority: [Must/Should/Could]
     Source: [BR-ID or User Story ID]

3. Business Rules
   BR-001: [Rule description]
   - Condition: [When this applies]
   - Action: [What happens]
   - Exception: [Edge cases]

4. Interface Specifications
   - Screen layouts (reference wireframes)
   - Field-level specifications (field name, type, length, required, default, validation)
   - API contracts (endpoint, method, request/response schema)

5. Reporting Requirements
   - Report name, purpose, frequency
   - Data source, filters, columns
   - Access permissions

6. Appendices
   - Screen mockups
   - Sample data
   - State transition diagrams
```

## Non-Functional Requirements

Always prompt the user to consider these categories:

| Category | Key Questions | Example Requirement |
|----------|---------------|-------------------|
| **Performance** | Response time? Throughput? | "95th percentile response < 2s" |
| **Scalability** | Expected growth? Peak load? | "Support 10K concurrent users" |
| **Availability** | Uptime SLA? Maintenance window? | "99.9% uptime, max 4h/month downtime" |
| **Security** | Auth method? Data sensitivity? Compliance? | "All PII encrypted at rest (AES-256)" |
| **Usability** | Target users? Accessibility? | "WCAG 2.1 AA compliant" |
| **Reliability** | Recovery time? Data loss tolerance? | "RPO < 1 hour, RTO < 4 hours" |
| **Maintainability** | Deployment frequency? Logging? | "Zero-downtime deployments" |
| **Portability** | Browser/device support? | "Chrome, Firefox, Safari, Edge (latest 2)" |
| **Compliance** | Regulations? Standards? | "GDPR compliant, data residency in EU" |

## Requirement Quality Checklist

Before finalizing any requirement, verify:

- [ ] **Clear**: Unambiguous, one interpretation only
- [ ] **Complete**: All necessary information included
- [ ] **Consistent**: No conflicts with other requirements
- [ ] **Testable**: Can be verified through testing
- [ ] **Traceable**: Links back to business need/source
- [ ] **Feasible**: Technically and financially achievable
- [ ] **Prioritized**: MoSCoW or P0/P1/P2 assigned
- [ ] **Unique ID**: Each requirement has a unique identifier
- [ ] **No implementation bias**: Describes WHAT, not HOW
- [ ] **Atomic**: One requirement per statement

# BA Quality Checklist (Mandatory Gate)

Load this file and run relevant checks BEFORE outputting any deliverable.

## Checklist 1: Requirements Validation
*Apply to: Phase 2 (Elicitation output), Phase 3 (BRD/SRS/PRD/FRD/User Stories)*

- [ ] **Completeness**: Exception conditions (error, timeout, empty data) covered?
- [ ] **Unique ID**: Every requirement has a unique identifier (FR-xxx, NFR-xxx, BR-xxx)?
- [ ] **Feasibility**: Achievable within budget, timeline, technology constraints?
- [ ] **Unambiguous**: One interpretation only, no vague words ("appropriate", "fast", "user-friendly")?
- [ ] **Consistency**: No contradiction with other requirements?
- [ ] **Business Value**: Answers "Why are we building this?" (cost savings, usability, compliance)?
- [ ] **Testable**: Can write at least 1 test case for this requirement?
- [ ] **No Implementation Bias**: Describes WHAT, not HOW (no technology-specific language)?
- [ ] **Atomic**: One requirement per statement (no "and" combining two different needs)?
- [ ] **Prioritized**: MoSCoW or P0/P1/P2 assigned?

## Checklist 2: Non-Functional Requirements
*Apply to: Phase 3 (SRS specifically)*

- [ ] **Performance**: Response time specified (e.g., "95th percentile < 2s")?
- [ ] **Data Volume**: Max records/transactions/concurrent users defined?
- [ ] **Security**: Authentication method + authorization/role-based access defined?
- [ ] **Reliability**: Uptime SLA (e.g., 99.9%) and allowed downtime window defined?
- [ ] **Usability**: UI standards, color scheme, localization, accessibility (WCAG) specified?
- [ ] **Scalability**: Growth projection addressed?
- [ ] **Compliance**: Applicable regulations listed (GDPR, PCI-DSS, local laws)?

## Checklist 3: Design Validation
*Apply to: Detailed Design documents*

- [ ] **Input Validation**: Every input field has: Max length, Data type, Null check, Format?
- [ ] **Error Handling**: Clear error messages defined for each validation failure?
- [ ] **Processing Logic**: Steps match data flow (CRUD operations consistent)?
- [ ] **Boundary Conditions**: Min/Max values, empty state, overflow handled?
- [ ] **Control Spec**: Every UI control has: Name, Type, Required, Max Length, Read-only, Description?
- [ ] **Event Handling**: Every interactive element has defined behavior (click, change, submit)?
- [ ] **SQL/Query Logic**: Queries match business rules? Injection prevention noted?

## Checklist 4: Risk Assessment
*Apply to: Phase 1 (Planning), Phase 6 (Validation)*

- [ ] **Requirements Risk**: Any vague or frequently-changing requirements flagged?
- [ ] **End-user Risk**: End users participated in elicitation? If not, risk of wrong implementation?
- [ ] **External Risk**: Dependency on 3rd-party API/system? Downtime handling strategy defined?
- [ ] **Data Risk**: Data migration needed? Data quality issues identified?
- [ ] **Timeline Risk**: Critical path dependencies identified?

## Checklist 5: Traceability
*Apply to: Phase 7 (RTM, Change Management)*

- [ ] **Forward Trace**: Every requirement → design reference → test case?
- [ ] **Backward Trace**: Every test case → maps back to requirement?
- [ ] **Coverage**: ≥ 95% of Must/Should requirements have test coverage?
- [ ] **Orphan Check**: No test cases without a parent requirement?
- [ ] **Change Impact**: Every approved CR → updated requirements + test cases + RTM?

## Checklist 6: UAT Readiness
*Apply to: Phase 6 (UAT Plan, Test Cases)*

- [ ] **Entry Criteria**: All SIT critical/high defects resolved?
- [ ] **Test Environment**: Configured and verified?
- [ ] **Test Data**: Prepared and loaded (realistic data, not lorem ipsum)?
- [ ] **Test Cases**: Reviewed and approved by BA + business?
- [ ] **Testers**: Trained on new system?
- [ ] **Exit Criteria**: Clear pass rate (≥95%), zero critical defects, sign-off process defined?
- [ ] **Positive + Negative**: Each AC has at least 1 happy path + 1 error path test case?
- [ ] **Boundary Tests**: Edge cases for numeric/date ranges included?

## How to Report

After running checks, append to output:

```
---
Quality Gate: PASSED ✅
Checks run: Checklist 1, 2
Items checked: 17/17 passed
Notes: [any caveats or assumptions]
---
```

Or if issues found:
```
---
Quality Gate: ISSUES FOUND ⚠️
Checks run: Checklist 1, 3
Items checked: 15/17 passed, 2 need attention
Issues:
- Checklist 1 > Completeness: Exception for timeout not defined in FR-005
- Checklist 3 > Boundary: Max length not specified for "description" field
Recommendation: Address above items before stakeholder review
---
```

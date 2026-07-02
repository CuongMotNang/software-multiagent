---
name: ba-assistant-v2
description: >
  BA assistant for full BA lifecycle (BABOK-aligned) with tool integration and quality gates.
  Covers: (1) Stakeholder/RACI, (2) Elicitation — interviews/workshops/surveys,
  (3) Requirements — user stories/BRD/SRS/PRD/FRD/acceptance criteria,
  (4) Process modeling — AS-IS/TO-BE/BPMN/swimlane, (5) Data modeling — ERD/data dictionary,
  (6) Solution validation — gap analysis/UAT/test cases, (7) Change/traceability — RTM/impact analysis,
  (8) Detailed design — screen specs/field validation.
  Triggers: requirement, user story, stakeholder, BRD, SRS, PRD, FRD, use case, gap analysis,
  process flow, BA, business analyst, elicitation, UAT, traceability, RACI, change request,
  impact analysis, test case, ERD, data dictionary, detailed design, đặc tả, nghiệp vụ.
  Outputs via docx/xlsx/pdf/pptx skills and Mermaid.
---

# BA Assistant v2

Comprehensive BA assistant with tool integration and quality gates.

## Routing

Determine user need → load the ONE most relevant reference → use the right tool:

| User keywords | Phase | Reference to load | Primary output tool |
|---------------|-------|-------------------|-------------------|
| stakeholder, RACI, communication plan | 1 | phase-01-stakeholder.md | xlsx |
| interview, workshop, elicitation, survey | 2 | phase-02-elicitation.md | docx |
| user story, BRD, SRS, PRD, FRD, acceptance criteria, use case | 3 | phase-03-requirements.md | docx |
| process flow, AS-IS, TO-BE, BPMN, swimlane, sequence | 4 | phase-04-process-modeling.md | mermaid |
| ERD, data dictionary, data mapping, entity | 5 | phase-05-data-modeling.md | mermaid + xlsx |
| UAT, test case, gap analysis, feasibility | 6 | phase-06-solution-validation.md | docx + xlsx |
| change request, impact analysis, RTM, traceability | 7 | phase-07-change-traceability.md | xlsx |
| detailed design, thiết kế chi tiết, screen spec | Extra | design-spec-guide.md | docx |

If unclear, ask user which phase they need.

## Tool Integration Rules

Before creating ANY file output, read the corresponding skill:

| Output | Read first |
|--------|-----------|
| .docx (BRD/SRS/FRD/PRD/Design) | docx skill at /mnt/skills/public/docx/SKILL.md |
| .xlsx (RACI/RTM/Data Dict/Test Cases) | xlsx skill at /mnt/skills/public/xlsx/SKILL.md |
| .pdf | pdf skill at /mnt/skills/public/pdf/SKILL.md |
| .pptx | pptx skill at /mnt/skills/public/pptx/SKILL.md |
| .mermaid or .md with diagrams | Use Mermaid syntax from reference files (no skill needed) |
| .html/.jsx (dashboards) | frontend-design skill at /mnt/skills/public/frontend-design/SKILL.md |

### Template Usage
If `assets/templates/` has a matching template:
1. Copy template to /home/claude/
2. Read docx/xlsx skill for editing instructions
3. Fill content into template
4. Validate and output

## Quality Gate (MANDATORY)

**Before outputting ANY deliverable**, load `references/quality-checklist.md` and run the relevant checks:

- Requirements docs (BRD/SRS/PRD/FRD/User Stories) → Checklist 1 + 2
- Detailed Design → Checklist 3
- UAT/Test artifacts → Checklist 6
- All phases → Checklist 4 (Risk)
- RTM → Checklist 5 (Traceability)

If any item FAILS → fix before delivering. Note checked items at end of output.

## Domain Detection

When user mentions industry-specific terms, load the corresponding domain reference IN ADDITION to the phase reference:

| Keywords / Context | Domain file |
|-------------------|-------------|
| ngân hàng, bank, KYC, AML, tín dụng, khoản vay, core banking, CASA, tài khoản, sổ tiết kiệm | domain/banking.md |
| e-commerce, TMĐT, giỏ hàng, đơn hàng, voucher, SKU, COD, flash sale, marketplace | domain/ecommerce.md |
| viễn thông, telecom, thuê bao, SIM, gói cước, MSISDN, OCS, CDR, top-up, data plan | domain/telecom.md |
| bảo hiểm, insurance, policy, claim, premium, underwriting, bồi thường, hợp đồng BH | domain/insurance.md |
| y tế, healthcare, bệnh viện, bệnh nhân, EMR, HIS, BHYT, khám bệnh, đơn thuốc, xét nghiệm | domain/healthcare.md |
| logistics, vận chuyển, kho, WMS, TMS, giao hàng, shipment, last mile, 3PL, COD đối soát | domain/logistics.md |
| bất động sản, BĐS, căn hộ, dự án, chủ đầu tư, booking, HĐMB, bàn giao, sổ hồng | domain/realestate.md |
| giáo dục, EdTech, LMS, sinh viên, khóa học, tín chỉ, enrollment, GPA, đào tạo | domain/education.md |

Each domain file contains: Terminology, Compliance, Entities (ERD), State Diagrams, Events, User Roles, Business Rules, and Sample Requirements. Use this domain knowledge to produce more accurate, industry-standard deliverables.

## General Principles

- Ask clarifying questions before producing artifacts.
- INVEST for user stories: Independent, Negotiable, Valuable, Estimable, Small, Testable.
- Always consider NFRs: Performance, Security, Scalability, Usability, Reliability, Compliance.
- Acceptance Criteria in Given/When/Then format.
- Flag assumptions explicitly.
- Maintain consistent terminology across all artifacts.
- Use Vietnamese or English based on user's language preference.

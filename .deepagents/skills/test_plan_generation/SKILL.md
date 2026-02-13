---
name: test-plan-generation
description: Workflow for generating standardized satellite test plans
---

# Test Plan Generation Workflow

## 1. Context
This skill assists in creating a comprehensive Test Plan for satellite subsystems or integrated systems, ensuring coverage of requirements and resource allocation.

## 2. Input Requirements
- **Test Object**: Name and version of the system under test (e.g., "StarTracker V2.0").
- **Test Type**: Environment, Functional, EMC, etc.
- **Reference Docs**: Requirement Specification ID, Standard ID (e.g., ECSS-E-ST-10-03C).

## 3. Workflow Steps

### Step 1: Define Test Scope & Objectives
- Identify which requirements are to be verified (Traceability).
- Define the specific goal (e.g., "Verify pointing accuracy under thermal load").

### Step 2: Resource Planning
- **Equipment**: List required EGSE, MGSE, Chambers.
- **Personnel**: Roles required (Test Director, QA, Operator).
- **Time**: Estimated duration per phase.

### Step 3: Sequence of Events (SoE)
- Draft the chronological steps.
- **Pre-test**: Inspection, Setup.
- **Execution**: Step-by-step commands and expected responses.
- **Post-test**: Teardown, Data backup.

### Step 4: Define Success Criteria
- Quantitative: "Voltage must be 28V ± 0.5V".
- Qualitative: "Mechanism deploys without visible stutter".

### Step 5: Risk Assessment
- Identify hazards (e.g., High Voltage, Cryogenic).
- Define mitigation measures (e.g., "Grounding strap must be worn").

## 4. Output Template
```markdown
# Test Plan: [Test Object Name]
## 1. Introduction
...
## 2. References
...
## 3. Configuration
...
## 4. Schedule
...
## 5. Test Procedures
...
```

## 5. Verification
- Cross-check against the "Requirement Verification Matrix" (RVM).
- Ensure all safety constraints are listed.

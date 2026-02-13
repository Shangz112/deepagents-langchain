---
name: mbse-requirement-modeling
description: SOP for SysML Requirement Modeling and Traceability
---

# MBSE Requirement Modeling SOP

## 1. Objective
To formalize textual requirements into SysML models, enabling traceability, impact analysis, and automated verification.

## 2. Modeling Environment
- **Tool**: Cameo Systems Modeler / Enterprise Architect.
- **Profile**: SysML 1.6 or later.
- **Package Structure**: `01_Requirements` -> `Functional`, `Performance`, `Constraint`.

## 3. Modeling Steps

### Step 1: Requirement Import/Creation
- Create a `<<Requirement>>` block.
- **Id**: Unique identifier (e.g., REQ-PWR-001).
- **Text**: The requirement statement (shall ...).
- **Properties**: Priority, Status, VerificationMethod (Test, Analysis, Inspection).

### Step 2: Hierarchy Definition
- Use **Containment** (circle with cross) to show decomposition.
    - `Parent Req` contains `Child Req`.
- **Constraint**: Ensure decomposition is logical (e.g., System -> Subsystem).

### Step 3: Derivation and Refinement
- Use `<<deriveReqt>>`: When a lower-level requirement is derived from a higher one.
- Use `<<refine>>`: When a model element (e.g., Use Case) clarifies a requirement.

### Step 4: Satisfaction Traceability
- Connect design elements (Blocks) to Requirements.
- Use `<<satisfy>>` relationship.
    - "Battery Block" `<<satisfy>>` "REQ-PWR-Capacity".

### Step 5: Verification Traceability
- Connect Test Cases to Requirements.
- Use `<<verify>>` relationship.
    - "Capacity Test" `<<verify>>` "REQ-PWR-Capacity".

## 4. Best Practices
- **Atomic**: One requirement block should contain only one requirement.
- **Verifiable**: Avoid vague words like "adequate", "sufficient".
- **Traceable**: Every leaf requirement must have at least one `<<satisfy>>` and one `<<verify>>`.

## 5. Quality Check (Checklist)
- [ ] Are all IDs unique?
- [ ] Are there orphan requirements (no parent, no links)?
- [ ] Is the text unambiguous?
- [ ] Is the verification method specified?

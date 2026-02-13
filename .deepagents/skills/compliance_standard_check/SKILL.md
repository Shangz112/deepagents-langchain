---
name: compliance-standard-check
description: Guide for checking compliance against satellite industry standards (ECSS/NASA)
---

# Compliance Standard Check Guide

## 1. Scope
This skill provides a framework for checking satellite design and testing artifacts against major industry standards, specifically ECSS (European) and NASA standards.

## 2. Key Standards Reference

### 2.1 ECSS (European Cooperation for Space Standardization)
- **ECSS-E-ST-10C**: System Engineering General Requirements.
- **ECSS-E-ST-20C**: Electrical & Electronic.
- **ECSS-E-ST-31C**: Thermal Control.
- **ECSS-Q-ST-70**: Materials, mechanical parts and processes.

### 2.2 NASA Technical Standards
- **NASA-STD-5001**: Structural Design and Test Factors of Safety.
- **GEVS (GSFC-STD-7000)**: General Environmental Verification Standard (Gold standard for testing).

## 3. Compliance Checking Process

### Step 1: Identify Applicable Standards
- Determine the mission class (Class A/B/C/D or CubeSat).
- Select relevant domains (Thermal, Structural, EMC).

### Step 2: Extract Requirements (Compliance Matrix)
- Create a Compliance Matrix (Excel/Table).
- Columns: `Standard_Ref`, `Requirement_Text`, `Compliance_Status` (C/NC/PC), `Justification`.

### Step 3: Assess Artifacts
- **Design Review**: Check CAD models against mechanical constraints (e.g., venting holes for vacuum).
- **Test Review**: Check test levels (vibration g-rms, thermal range) against standard minimums (e.g., GEVS workmanship levels).

### Step 4: Handle Non-Conformances (NC)
- If a standard cannot be met, raise a **Waiver** or **Deviation**.
- **Waiver**: Approval to accept an item that does not satisfy requirements (after manufacturing).
- **Deviation**: Approval to depart from requirements (before manufacturing).

## 4. Common Compliance Pitfalls
- **Outgassing**: Using materials with TML > 1% or CVCM > 0.1% (Check NASA outgassing db).
- **Derating**: Electronic components not derated according to ECSS-Q-ST-30-11C.
- **Testing Margins**: Testing at qualification levels instead of acceptance levels for Flight Models.

## 5. Output Format
**Compliance Statement:**
> "The design [complies / does not comply] with [Standard ID].
> **Exceptions:**
> 1. [Requirement ID]: [Reason for non-compliance] (Waiver #123)"

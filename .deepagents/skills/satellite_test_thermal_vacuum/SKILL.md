---
name: satellite-thermal-vacuum-test
description: Standard Operating Procedure (SOP) for Satellite Thermal Vacuum Testing
---

# Satellite Thermal Vacuum Test SOP

## 1. Objective
To verify the satellite's performance and survival in a simulated space thermal vacuum environment.

## 2. Prerequisites
- **Test Article**: Integrated Satellite Flight Model (FM) or Qualification Model (QM).
- **Facility**: Thermal Vacuum Chamber (TVC) capable of < 1e-5 Pa and -180°C to +100°C.
- **Documentation**: Approved Test Procedure, Test Readiness Review (TRR) signed off.

## 3. Test Setup
1.  **Installation**: Mount satellite on the thermal shroud test fixture.
2.  **Instrumentation**: Attach thermocouples (TCs) to critical components (Battery, OBC, Payload).
3.  **Cabling**: Connect EGSE (Electrical Ground Support Equipment) via vacuum feedthroughs.
4.  **Verification**: Perform "Aliveness Test" at ambient pressure to confirm connectivity.

## 4. Test Phases (Cycles)
The test typically consists of 4-8 cycles.

### Phase A: Pump Down
- **Action**: Evacuate chamber to < 1e-5 Pa.
- **Monitoring**: Monitor outgassing rates (TQCM).
- **Constraint**: Rate of pressure drop < 1000 Pa/min to avoid arcing (Corona effect).

### Phase B: Cold Soak (Survival)
- **Action**: Lower shroud temperature to -40°C (or specific survival limit).
- **Duration**: Dwell for 4 hours after stabilization.
- **Check**: Satellite OFF or in Survival Mode.

### Phase C: Cold Start
- **Action**: Power ON satellite at minimum temperature.
- **Check**: Verify boot sequence and telemetry health.

### Phase D: Hot Soak (Operational)
- **Action**: Raise shroud temperature to +50°C (or operational max).
- **Duration**: Dwell for 4 hours.
- **Check**: Perform Full Functional Test (FFT).

### Phase E: Return to Ambient
- **Action**: Repressurize with dry nitrogen (GN2).
- **Constraint**: Dew point < -20°C to prevent condensation.

## 5. Pass/Fail Criteria
- **Pass**: All FFTs successful; TCs remain within limits; no physical damage.
- **Fail**: Loss of communication > 10s; component temp exceeds non-op limits; structural deformation.

## 6. Anomalies
- **Immediate Action**: If safety limit reached, initiate Emergency Shutdown (ESD).
- **Reporting**: Log anomaly in "Test Issue List" (TIL) with timestamp and telemetry snapshot.

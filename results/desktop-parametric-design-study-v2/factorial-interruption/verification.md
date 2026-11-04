Factorial interruption/resume verification

Scope: existing FACTORIAL_2X2_V1 and the generic parametric-study runner only. The engineering runner is monkeypatched; no solver execution or physical campaign occurs.

The test completes factorial point 0, interrupts point 1 after creating a checkpoint, reopens the prepared study, and explicitly resumes. It verifies: all four factor combinations and point identities stay unchanged; the completed point is verified from its bound result artifact and is not rerun; point 1 resumes with the same run ID and checkpoint; points 2 and 3 run once; all terminal rows retain their nonconverged classification and scientific_validation remains NOT_CLAIMED.

No defect was found in the existing factorial checkpoint/resume implementation. No solver or model changes were needed.

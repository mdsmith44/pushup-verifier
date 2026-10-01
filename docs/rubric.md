# Conventional pushup rubric, version 0.2

One person, a stationary side-view camera, full body in frame. Begin and finish each set with a clearly visible top position. Thresholds below are development hypotheses, not universal biomechanical or military standards.

| Signal | Initial rule |
|---|---|
| Top | Shoulder–elbow–wrist angle ≥145° |
| Departure from top | Elbow angle ≤130° |
| Bottom reached | Elbow angle ≤90° during an active attempt |
| Body alignment | Shoulder–hip–ankle angle ≥160° |
| Reliable observation | Minimum required landmark visibility/presence ≥0.6 |
| Maximum observation gap | 0.25 seconds |
| Temporal phase persistence | 0.10 seconds |
| Temporal smoothing time constant | 0.08 seconds |

An attempt starts after a verified top and a verified departure. It completes upon returning to a verified top. Accept only if bottom was reached and no sustained alignment failure was observed. Otherwise reject with reasons. Small movements that never cross the departure threshold are not segmented as attempts; evaluate that limitation explicitly.

Temporal mode requires continuous threshold evidence for each transition and for an alignment failure. Immediate mode accepts a single observation as evidence. Both use the top/departure threshold separation to avoid repeatedly counting top-position jitter. Temporal angles are smoothed; they are not additional independent measurements.

The 90° comparison uses the shoulder–elbow–wrist angle measured in the image plane. It is not equivalent to upper-arm parallelism relative to the floor. In temporal mode, the filtered angle must meet the threshold; a raw measurement of exactly 90° may not pass after smoothing from larger angles. Plot raw and filtered measurements together to make this effect visible. Do not silently round near-threshold values to make them pass.

Pilot configuration: at the user's request, top recognition was lowered from 160° to 145° to work with the existing recordings. Departure was lowered from 145° to 130° to preserve the 15° separation between entering and leaving the top state. This is a relaxed development criterion, not verification of full elbow extension. Keep these pilot recordings in development; do not report them as held-out evaluation after tuning on them. Depth remains 90°, body alignment remains 160°, and confidence/timing settings are unchanged.

Missing/low-confidence observations or excessive sampling gaps interrupt an active attempt, mark it unable to assess, clear temporal history, and require a new top before counting resumes. Visibility lost outside an active attempt is logged as an uncertainty interval, not a fabricated rep. End-of-video during an attempt is unable to assess because truncation does not establish failure to complete.

These checks assess projected range of motion and a body-line proxy. They do not establish chest-to-floor distance, exact joint extension, hand placement, knee contact, or compliance with an official test. A bent body line alone does not distinguish sagging from piking. Camera perspective and pose errors can create both false accepts and false rejects.

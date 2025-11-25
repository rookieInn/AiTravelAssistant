package com.example.workflow;

/**
 * Detailed result for an approval submission.
 *
 * @param action        high-level outcome of the submission
 * @param nodeCompleted whether the node finished after the event
 * @param flowCompleted whether the entire flow finished after the event
 */
public record ApprovalEventResult(
        ApprovalActionResult action,
        boolean nodeCompleted,
        boolean flowCompleted
) {
}

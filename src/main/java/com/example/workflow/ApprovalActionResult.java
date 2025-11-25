package com.example.workflow;

/**
 * Result of attempting to record an approval event.
 */
public enum ApprovalActionResult {
    ACCEPTED,
    DUPLICATE,
    INVALID_APPROVER,
    UNKNOWN_NODE,
    BLOCKED_BY_PREVIOUS_NODE
}

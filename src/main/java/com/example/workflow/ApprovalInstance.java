package com.example.workflow;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Runtime state for a single approval request using a predefined flow.
 */
public class ApprovalInstance {

    private final List<ApprovalNode> orderedNodes;
    private final Map<String, NodeProgress> progress;

    public ApprovalInstance(ApprovalFlow flow) {
        Objects.requireNonNull(flow, "flow");
        this.orderedNodes = flow.nodes();
        if (orderedNodes.isEmpty()) {
            throw new IllegalArgumentException("approval flow has no nodes");
        }
        this.progress = orderedNodes.stream()
                .collect(Collectors.toMap(
                        ApprovalNode::id,
                        NodeProgress::new,
                        (a, b) -> a,
                        LinkedHashMap::new
                ));
    }

    /**
     * Records an approval for the provided node.
     */
    public synchronized ApprovalEventResult recordApproval(String nodeId, String approver) {
        Objects.requireNonNull(nodeId, "nodeId");
        Objects.requireNonNull(approver, "approver");

        NodeProgress nodeProgress = progress.get(nodeId);
        if (nodeProgress == null) {
            return new ApprovalEventResult(ApprovalActionResult.UNKNOWN_NODE, false, false);
        }
        if (!nodeProgress.node().hasApprover(approver)) {
            return new ApprovalEventResult(ApprovalActionResult.INVALID_APPROVER, false, false);
        }
        if (!isNodeActive(nodeId)) {
            return new ApprovalEventResult(ApprovalActionResult.BLOCKED_BY_PREVIOUS_NODE, false, false);
        }
        boolean changed = nodeProgress.accept(approver);
        if (!changed) {
            return new ApprovalEventResult(ApprovalActionResult.DUPLICATE, nodeProgress.isComplete(), isComplete());
        }
        boolean nodeDone = nodeProgress.isComplete();
        return new ApprovalEventResult(ApprovalActionResult.ACCEPTED, nodeDone, isComplete());
    }

    public synchronized boolean isComplete() {
        return progress.values().stream().allMatch(NodeProgress::isComplete);
    }

    /**
     * Returns the first pending node, if any.
     */
    public synchronized Optional<ApprovalNode> currentNode() {
        return orderedNodes.stream()
                .filter(node -> !progress.get(node.id()).isComplete())
                .findFirst();
    }

    public synchronized Map<String, Set<String>> approvalsSnapshot() {
        return progress.values().stream()
                .collect(Collectors.toUnmodifiableMap(
                        p -> p.node().id(),
                        NodeProgress::approvedApprovers
                ));
    }

    private boolean isNodeActive(String nodeId) {
        for (ApprovalNode node : orderedNodes) {
            if (node.id().equals(nodeId)) {
                return true;
            }
            if (!progress.get(node.id()).isComplete()) {
                return false;
            }
        }
        return false;
    }

    private static final class NodeProgress {
        private final ApprovalNode node;
        private final Set<String> approvals = new java.util.LinkedHashSet<>();

        private NodeProgress(ApprovalNode node) {
            this.node = node;
        }

        private ApprovalNode node() {
            return node;
        }

        private boolean accept(String approver) {
            if (isComplete()) {
                return false;
            }
            return approvals.add(approver);
        }

        private boolean isComplete() {
            return switch (node.relation()) {
                case ALL -> approvals.containsAll(node.approvers());
                case ANY -> approvals.stream().anyMatch(node.approvers()::contains);
            };
        }

        private Set<String> approvedApprovers() {
            return Collections.unmodifiableSet(approvals);
        }
    }
}

package com.example.workflow;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.Optional;

/**
 * Mutable definition of an approval workflow.
 */
public class ApprovalFlow {

    private final List<ApprovalNode> nodes = new ArrayList<>();

    public synchronized ApprovalFlow appendNode(ApprovalNode node) {
        Objects.requireNonNull(node, "node");
        requireUniqueId(node.id());
        nodes.add(node);
        return this;
    }

    public synchronized ApprovalFlow insertNode(int index, ApprovalNode node) {
        Objects.requireNonNull(node, "node");
        if (index < 0 || index > nodes.size()) {
            throw new IndexOutOfBoundsException("index %d out of bounds for size %d".formatted(index, nodes.size()));
        }
        requireUniqueId(node.id());
        nodes.add(index, node);
        return this;
    }

    public synchronized ApprovalFlow removeNode(String nodeId) {
        Objects.requireNonNull(nodeId, "nodeId");
        nodes.removeIf(node -> node.id().equals(nodeId));
        return this;
    }

    public synchronized Optional<ApprovalNode> findNode(String nodeId) {
        return nodes.stream()
                .filter(node -> node.id().equals(nodeId))
                .findFirst();
    }

    public synchronized List<ApprovalNode> nodes() {
        return Collections.unmodifiableList(new ArrayList<>(nodes));
    }

    private void requireUniqueId(String id) {
        if (nodes.stream().anyMatch(node -> node.id().equals(id))) {
            throw new IllegalArgumentException("duplicate node id: " + id);
        }
    }
}

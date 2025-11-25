package com.example.workflow;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

/**
 * Represents a single approval step with a defined set of approvers
 * and an aggregation relation (AND/OR).
 */
public final class ApprovalNode {

    private final String id;
    private final String name;
    private final List<String> approvers;
    private final ApprovalRelation relation;

    private ApprovalNode(Builder builder) {
        this.id = builder.id == null ? UUID.randomUUID().toString() : builder.id;
        this.name = Objects.requireNonNull(builder.name, "name is required");
        if (builder.approvers.isEmpty()) {
            throw new IllegalArgumentException("at least one approver is required");
        }
        this.approvers = Collections.unmodifiableList(new ArrayList<>(builder.approvers));
        this.relation = Objects.requireNonNull(builder.relation, "relation is required");
    }

    public String id() {
        return id;
    }

    public String name() {
        return name;
    }

    public List<String> approvers() {
        return approvers;
    }

    public ApprovalRelation relation() {
        return relation;
    }

    public boolean hasApprover(String approver) {
        return approvers.contains(approver);
    }

    public static Builder builder() {
        return new Builder();
    }

    public static final class Builder {
        private String id;
        private String name;
        private final List<String> approvers = new ArrayList<>();
        private ApprovalRelation relation = ApprovalRelation.ALL;

        private Builder() {
        }

        public Builder id(String id) {
            this.id = id;
            return this;
        }

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder relation(ApprovalRelation relation) {
            this.relation = relation;
            return this;
        }

        public Builder addApprover(String approver) {
            this.approvers.add(Objects.requireNonNull(approver, "approver"));
            return this;
        }

        public Builder approvers(List<String> approvers) {
            this.approvers.clear();
            if (approvers != null) {
                approvers.stream()
                        .filter(Objects::nonNull)
                        .forEach(this.approvers::add);
            }
            return this;
        }

        public ApprovalNode build() {
            return new ApprovalNode(this);
        }
    }
}

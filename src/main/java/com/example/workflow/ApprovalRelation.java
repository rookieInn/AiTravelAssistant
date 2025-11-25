package com.example.workflow;

/**
 * Defines how approvals inside a node are evaluated.
 */
public enum ApprovalRelation {
    /**
     * All configured approvers must accept before the node completes.
     */
    ALL,
    /**
     * Any single approver may accept to complete the node.
     */
    ANY
}

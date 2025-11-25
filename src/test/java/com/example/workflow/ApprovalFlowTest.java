package com.example.workflow;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ApprovalFlowTest {

    @Test
    void shouldCompleteFlowWithMixedRelations() {
        ApprovalFlow flow = new ApprovalFlow()
                .appendNode(ApprovalNode.builder()
                        .id("manager")
                        .name("Manager")
                        .relation(ApprovalRelation.ALL)
                        .addApprover("alice")
                        .addApprover("bob")
                        .build())
                .appendNode(ApprovalNode.builder()
                        .id("finance")
                        .name("Finance")
                        .relation(ApprovalRelation.ANY)
                        .addApprover("carol")
                        .addApprover("dave")
                        .build());

        ApprovalInstance instance = new ApprovalInstance(flow);
        assertFalse(instance.isComplete());

        ApprovalEventResult first = instance.recordApproval("manager", "alice");
        assertEquals(ApprovalActionResult.ACCEPTED, first.action());
        assertFalse(first.nodeCompleted());
        assertFalse(first.flowCompleted());

        ApprovalEventResult second = instance.recordApproval("manager", "bob");
        assertTrue(second.nodeCompleted());
        assertFalse(second.flowCompleted());

        ApprovalEventResult financeApproval = instance.recordApproval("finance", "carol");
        assertTrue(financeApproval.nodeCompleted());
        assertTrue(financeApproval.flowCompleted());
        assertTrue(instance.isComplete());
    }

    @Test
    void shouldRejectOutOfOrderApproval() {
        ApprovalFlow flow = new ApprovalFlow()
                .appendNode(ApprovalNode.builder()
                        .id("first")
                        .name("First")
                        .relation(ApprovalRelation.ANY)
                        .addApprover("alice")
                        .build())
                .appendNode(ApprovalNode.builder()
                        .id("second")
                        .name("Second")
                        .relation(ApprovalRelation.ANY)
                        .addApprover("bob")
                        .build());

        ApprovalInstance instance = new ApprovalInstance(flow);
        ApprovalEventResult result = instance.recordApproval("second", "bob");
        assertEquals(ApprovalActionResult.BLOCKED_BY_PREVIOUS_NODE, result.action());
        assertFalse(result.nodeCompleted());
        assertFalse(result.flowCompleted());
    }

    @Test
    void shouldInsertAndRemoveNodes() {
        ApprovalNode original = ApprovalNode.builder()
                .id("original")
                .name("Original")
                .relation(ApprovalRelation.ANY)
                .addApprover("alice")
                .build();
        ApprovalNode inserted = ApprovalNode.builder()
                .id("inserted")
                .name("Inserted")
                .relation(ApprovalRelation.ALL)
                .addApprover("bob")
                .build();

        ApprovalFlow flow = new ApprovalFlow()
                .appendNode(original)
                .insertNode(1, inserted);

        assertEquals(2, flow.nodes().size());
        assertEquals("inserted", flow.nodes().get(1).id());

        flow.removeNode("inserted");
        assertEquals(1, flow.nodes().size());
        assertEquals("original", flow.nodes().get(0).id());
    }
}

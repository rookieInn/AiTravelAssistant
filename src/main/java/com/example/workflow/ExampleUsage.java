package com.example.workflow;

/**
 * Simple demo showing how to build and execute an approval flow.
 */
public final class ExampleUsage {

    public static void main(String[] args) {
        ApprovalFlow flow = new ApprovalFlow()
                .appendNode(ApprovalNode.builder()
                        .id("manager")
                        .name("直属经理审批")
                        .relation(ApprovalRelation.ALL)
                        .addApprover("alice")
                        .addApprover("bob")
                        .build())
                .appendNode(ApprovalNode.builder()
                        .id("finance")
                        .name("财务审批")
                        .relation(ApprovalRelation.ANY)
                        .addApprover("finance-1")
                        .addApprover("finance-2")
                        .build());

        // 支持在任意位置插入新的节点
        flow.insertNode(1, ApprovalNode.builder()
                .id("hr")
                .name("人事复核")
                .relation(ApprovalRelation.ANY)
                .addApprover("hr-1")
                .build());

        // 删除节点
        flow.removeNode("finance");

        // 启动审批实例
        ApprovalInstance instance = new ApprovalInstance(flow);
        instance.recordApproval("manager", "alice");
        ApprovalEventResult result = instance.recordApproval("manager", "bob");
        System.out.println("Manager node completed? " + result.nodeCompleted());
        System.out.println("Flow completed? " + result.flowCompleted());
    }

    private ExampleUsage() {
    }
}

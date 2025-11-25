# 审批流程示例

该项目提供一个简单的 Java 审批流程引擎，可按顺序执行多个审批节点，每个节点都可以配置审批人以及「与 / 或」关系，同时支持在流程中任意插入或删除节点。

## 功能特性
- 链式 API 构建流程，节点按插入顺序依次执行
- 节点支持多名审批人，并通过 `ALL`（全部通过）或 `ANY`（任意一人通过）控制逻辑
- 提供运行时实例 `ApprovalInstance`，记录审批事件、判断节点/流程是否完成
- 插入、删除节点均为 O(n) 操作，方便对流程进行实时编辑

## 快速开始
```bash
mvn clean test
```

如需运行简单示例，可执行：
```bash
mvn -q exec:java -Dexec.mainClass=com.example.workflow.ExampleUsage
```
示例会创建一个审批流，动态插入和删除节点，并演示审批通过后的状态变更。

## 关键类说明
- `ApprovalNode`：定义单个节点（ID、名称、审批人列表、与或关系）
- `ApprovalFlow`：流程定义，提供 `appendNode`、`insertNode`、`removeNode` 等操作
- `ApprovalInstance`：流程运行实例，`recordApproval` 用于写入审批事件并返回 `ApprovalEventResult`

更多使用方式可参考 `ExampleUsage` 与单元测试 `ApprovalFlowTest`。`ApprovalFlowTest` 覆盖了混合逻辑审批、顺序校验、节点增删等核心场景，方便快速了解代码行为。*** End Patch
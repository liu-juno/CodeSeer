#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

const API_URL = process.env.CODESEER_API_URL || "http://localhost:8000/api";
const TOKEN = process.env.CODESEER_TOKEN || "";
const ASSIGNEE_ID = process.env.CODESEER_DEVELOPER_ID || "";

const api = axios.create({
  baseURL: API_URL,
  headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {},
});

const server = new Server(
  { name: "codeseer", version: "0.1.0" },
  { capabilities: { tools: {} } }
);

// ── Tool definitions ─────────────────────────────────────────────────────────

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_assigned_requirements",
      description:
        "获取指派给当前开发者的需求列表。返回所有 assigned/claimed/in_progress 状态的需求。",
      inputSchema: {
        type: "object",
        properties: {
          status: {
            type: "string",
            description: "可选：过滤状态 (assigned|claimed|in_progress)",
          },
        },
      },
    },
    {
      name: "get_requirement_detail",
      description: "获取需求的完整详情，包括描述、验收标准、任务列表和测试记录。",
      inputSchema: {
        type: "object",
        properties: {
          requirement_id: {
            type: "string",
            description: "需求 ID (UUID)",
          },
        },
        required: ["requirement_id"],
      },
    },
    {
      name: "sync_tasks",
      description:
        "将任务列表同步到平台。调用后，平台的任务列表将被替换为提供的列表。在开始开发前调用此工具，将 AI 拆解的任务同步到平台。",
      inputSchema: {
        type: "object",
        properties: {
          requirement_id: {
            type: "string",
            description: "需求 ID",
          },
          tasks: {
            type: "array",
            description: "任务列表",
            items: {
              type: "object",
              properties: {
                title: { type: "string", description: "任务名称" },
                description: { type: "string", description: "任务描述" },
                estimated_hours: { type: "number", description: "预估工时（小时）" },
                priority: {
                  type: "string",
                  enum: ["P0", "P1", "P2", "P3"],
                  description: "优先级",
                },
              },
              required: ["title"],
            },
          },
        },
        required: ["requirement_id", "tasks"],
      },
    },
    {
      name: "update_task_status",
      description:
        "更新任务状态和 TDD 进度。在完成 Red/Green/Refactor 每个步骤后调用。",
      inputSchema: {
        type: "object",
        properties: {
          requirement_id: {
            type: "string",
            description: "需求 ID",
          },
          task_id: {
            type: "string",
            description: "任务 ID",
          },
          status: {
            type: "string",
            enum: ["pending", "in_progress", "completed", "blocked"],
            description: "任务状态",
          },
          tdd_red: {
            type: "string",
            enum: ["pending", "in_progress", "completed"],
            description: "TDD Red 阶段状态（编写失败测试）",
          },
          tdd_green: {
            type: "string",
            enum: ["pending", "in_progress", "completed"],
            description: "TDD Green 阶段状态（让测试通过）",
          },
          tdd_refactor: {
            type: "string",
            enum: ["pending", "in_progress", "completed"],
            description: "TDD Refactor 阶段状态（重构代码）",
          },
          actual_hours: {
            type: "number",
            description: "实际工时（小时）",
          },
        },
        required: ["requirement_id", "task_id"],
      },
    },
    {
      name: "submit_test_result",
      description:
        "提交单元测试执行结果到平台。在运行测试套件后调用此工具上报结果。",
      inputSchema: {
        type: "object",
        properties: {
          requirement_id: {
            type: "string",
            description: "需求 ID",
          },
          task_id: {
            type: "string",
            description: "关联的任务 ID（可选）",
          },
          task_title: {
            type: "string",
            description: "关联的任务名称（可选）",
          },
          test_type: {
            type: "string",
            description: "测试类型，默认 unit",
            default: "unit",
          },
          total_count: {
            type: "number",
            description: "总测试数量",
          },
          passed_count: {
            type: "number",
            description: "通过数量",
          },
          failed_count: {
            type: "number",
            description: "失败数量",
          },
          coverage: {
            type: "number",
            description: "代码覆盖率 (%)",
          },
          result: {
            type: "string",
            enum: ["all_passed", "failed", "partial"],
            description: "整体结果",
          },
          failed_tests: {
            type: "string",
            description:
              '失败用例的 JSON 字符串，格式: [{"name": "test_name", "message": "error message"}]',
          },
        },
        required: ["requirement_id", "total_count", "passed_count", "failed_count", "result"],
      },
    },
    {
      name: "update_requirement_status",
      description:
        "更新需求状态。在领取需求、开始开发、提交评审等关键节点调用。",
      inputSchema: {
        type: "object",
        properties: {
          requirement_id: {
            type: "string",
            description: "需求 ID",
          },
          action: {
            type: "string",
            enum: [
              "pending_analysis",
              "analyzed",
              "claimed",
              "in_progress",
              "pending_review",
              "review_approved",
              "review_rejected",
              "completed",
            ],
            description: "目标状态",
          },
        },
        required: ["requirement_id", "action"],
      },
    },
  ],
}));

// ── Tool handlers ─────────────────────────────────────────────────────────────

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "list_assigned_requirements": {
        const res = await api.get("/mcp/requirements");
        let reqs = res.data;
        if (args?.status) {
          reqs = reqs.filter((r) => r.status === args.status);
        }
        if (ASSIGNEE_ID) {
          reqs = reqs.filter(
            (r) => !r.assignee_id || r.assignee_id === ASSIGNEE_ID
          );
        }
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                reqs.map((r) => ({
                  id: r.id,
                  title: r.title,
                  status: r.status,
                  priority: r.priority,
                  assignee_id: r.assignee_id,
                  due_date: r.due_date,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case "get_requirement_detail": {
        const { requirement_id } = args;
        const res = await api.get(`/mcp/requirements/${requirement_id}`);
        const { requirement, tasks } = res.data;

        const testRes = await api.get(
          `/requirements/${requirement_id}/test-records`
        );
        const testRecords = testRes.data;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  requirement: {
                    id: requirement.id,
                    title: requirement.title,
                    description: requirement.description,
                    acceptance_criteria: requirement.acceptance_criteria,
                    status: requirement.status,
                    priority: requirement.priority,
                    due_date: requirement.due_date,
                  },
                  tasks: tasks.map((t) => ({
                    id: t.id,
                    title: t.title,
                    description: t.description,
                    status: t.status,
                    tdd_red: t.tdd_red,
                    tdd_green: t.tdd_green,
                    tdd_refactor: t.tdd_refactor,
                    estimated_hours: t.estimated_hours,
                  })),
                  test_records: testRecords.map((tr) => ({
                    id: tr.id,
                    task_title: tr.task_title,
                    result: tr.result,
                    total_count: tr.total_count,
                    passed_count: tr.passed_count,
                    failed_count: tr.failed_count,
                    coverage: tr.coverage,
                    executed_at: tr.executed_at,
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "sync_tasks": {
        const { requirement_id, tasks } = args;
        const res = await api.post("/mcp/sync-tasks", {
          requirement_id,
          tasks,
        });
        return {
          content: [
            {
              type: "text",
              text: `任务同步成功。需求 ${requirement_id} 已同步 ${res.data.task_count} 个任务。`,
            },
          ],
        };
      }

      case "update_task_status": {
        const { requirement_id, task_id, ...updates } = args;
        const res = await api.post("/mcp/update-task", {
          requirement_id,
          task_id,
          ...updates,
        });
        return {
          content: [
            {
              type: "text",
              text: `任务 ${task_id} 状态已更新。`,
            },
          ],
        };
      }

      case "submit_test_result": {
        const res = await api.post("/mcp/submit-test-result", args);
        return {
          content: [
            {
              type: "text",
              text: `测试结果已提交。记录 ID: ${res.data.test_record_id}。${args.passed_count}/${args.total_count} 通过${args.coverage != null ? `，覆盖率 ${args.coverage}%` : ""}。`,
            },
          ],
        };
      }

      case "update_requirement_status": {
        const { requirement_id, action } = args;
        const res = await api.post(`/requirements/${requirement_id}/transition`, {
          action,
        });
        return {
          content: [
            {
              type: "text",
              text: `需求状态已更新为: ${res.data.status}`,
            },
          ],
        };
      }

      default:
        return {
          content: [{ type: "text", text: `未知工具: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    const msg =
      error?.response?.data?.detail ||
      error?.message ||
      "Unknown error";
    return {
      content: [{ type: "text", text: `错误: ${msg}` }],
      isError: true,
    };
  }
});

// ── Start ─────────────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("CodeSeer MCP server running. API:", API_URL);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});

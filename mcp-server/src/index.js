#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

const API_URL = (process.env.CODESEER_API_URL || "http://localhost:8000/api")
  .replace("localhost", "127.0.0.1");
const TOKEN = process.env.CODESEER_TOKEN || "";
const ASSIGNEE_ID = process.env.CODESEER_DEVELOPER_ID || "";

const api = axios.create({
  baseURL: API_URL,
  headers: TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {},
  timeout: 15000,
  httpAgent: new (await import("http")).Agent({ keepAlive: false }),
});

// ── Session state (single-developer, single-active-requirement) ───────────────

let activeRequirement = null;
//   shape: { id, title, phase, setAt }
//   - set on successful start_brainstorming
//   - cleared when the requirement transitions to a terminal status
let myContextCache = null;
let myContextCacheAt = 0;
const CONTEXT_TTL_MS = 30_000;

async function getMyContext(force = false) {
  const now = Date.now();
  if (!force && myContextCache && now - myContextCacheAt < CONTEXT_TTL_MS) {
    return myContextCache;
  }
  const res = await api.get("/mcp/my-context", {
    params: { assignee_id: ASSIGNEE_ID },
  });
  myContextCache = res.data;
  myContextCacheAt = now;
  return myContextCache;
}

function requireDeveloper() {
  if (!ASSIGNEE_ID) {
    return {
      content: [
        {
          type: "text",
          text:
            "错误: CODESEER_DEVELOPER_ID 环境变量未设置。请在 MCP 启动配置中配置此变量为你自己的用户 ID。",
        },
      ],
      isError: true,
    };
  }
  return null;
}

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
    {
      name: "list_my_projects",
      description:
        "【开始开发的第 1 步】列出当前开发者有未完成需求的项目（按待开发需求数量倒序）。在调用 list_iterations 之前必须先调用此工具。",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "list_iterations",
      description:
        "【开始开发的第 2 步】列出指定项目下的迭代。调用前先用 list_my_projects 选好项目。",
      inputSchema: {
        type: "object",
        properties: {
          project_id: {
            type: "string",
            description: "项目 ID (UUID)",
          },
        },
        required: ["project_id"],
      },
    },
    {
      name: "list_my_requirements",
      description:
        "【开始开发的第 3 步】列出指定迭代中指派给当前开发者的可开发需求（状态为 assigned/claimed/in_progress）。返回的 ID 用于 start_brainstorming。",
      inputSchema: {
        type: "object",
        properties: {
          iteration_id: {
            type: "string",
            description: "迭代 ID (UUID)",
          },
        },
        required: ["iteration_id"],
      },
    },
    {
      name: "start_brainstorming",
      description:
        "【开始开发的第 4 步：入口】锁定一条需求并返回 Superpowers 头脑风暴所需的完整上下文（需求详情 + 任务 + 测试记录 + 引导问题）。调用后即进入头脑风暴流程。",
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
  ],
}));

// ── Tool handlers ─────────────────────────────────────────────────────────────

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "list_assigned_requirements": {
        const guard = requireDeveloper();
        if (guard) return guard;
        const res = await api.get("/mcp/requirements", {
          params: { assignee_id: ASSIGNEE_ID },
        });
        let reqs = res.data;
        if (args?.status) {
          reqs = reqs.filter((r) => r.status === args.status);
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
        // If the active requirement just moved to a terminal status, clear it
        if (
          activeRequirement &&
          activeRequirement.id === requirement_id &&
          ["completed", "review_approved"].includes(res.data.status)
        ) {
          activeRequirement = null;
          myContextCache = null;
          myContextCacheAt = 0;
        }
        return {
          content: [
            {
              type: "text",
              text: `需求状态已更新为: ${res.data.status}`,
            },
          ],
        };
      }

      // ── 预头脑风暴选择流 ─────────────────────────────────────────────

      case "list_my_projects": {
        const guard = requireDeveloper();
        if (guard) return guard;
        const ctx = await getMyContext();
        const counts = new Map();
        for (const r of ctx.assignable_requirements) {
          counts.set(r.project_id, (counts.get(r.project_id) || 0) + 1);
        }
        const lines = ["你当前可开发的项目："];
        for (const p of ctx.projects) {
          const n = counts.get(p.id) || 0;
          lines.push(`- ${p.name} (id: ${p.id}) — ${n} 个待开发需求`);
        }
        if (ctx.projects.length === 0) {
          lines.push("(暂无)");
        }
        return {
          content: [{ type: "text", text: lines.join("\n") }],
        };
      }

      case "list_iterations": {
        const guard = requireDeveloper();
        if (guard) return guard;
        const { project_id } = args;
        const ctx = await getMyContext();
        const project = ctx.projects.find((p) => p.id === project_id);
        if (!project) {
          return {
            content: [
              {
                type: "text",
                text: `错误: 项目 ${project_id} 不在当前开发者的项目列表中。请先调用 list_my_projects 确认。`,
              },
            ],
            isError: true,
          };
        }
        const iterations = ctx.iterations_by_project[project_id] || [];
        const lines = [`项目「${project.name}」下的迭代：`];
        for (const it of iterations) {
          lines.push(`- ${it.name} (id: ${it.id}, 状态: ${it.status})`);
        }
        if (iterations.length === 0) {
          lines.push("(该项目暂无迭代)");
        }
        return {
          content: [{ type: "text", text: lines.join("\n") }],
        };
      }

      case "list_my_requirements": {
        const guard = requireDeveloper();
        if (guard) return guard;
        const { iteration_id } = args;
        const ctx = await getMyContext();
        const reqs = ctx.assignable_requirements.filter(
          (r) => r.iteration_id === iteration_id
        );
        const lines = [`该迭代中指派给你的可开发需求：`];
        for (const r of reqs) {
          const due = r.due_date ? r.due_date.slice(0, 10) : "无截止";
          lines.push(
            `- [${r.priority}] ${r.title} (id: ${r.id}, 状态: ${r.status}, 截止: ${due})`
          );
        }
        if (reqs.length === 0) {
          lines.push("(暂无)");
        }
        return {
          content: [{ type: "text", text: lines.join("\n") }],
        };
      }

      case "start_brainstorming": {
        const guard = requireDeveloper();
        if (guard) return guard;
        const { requirement_id } = args;
        // 1) 拉需求详情 + 任务
        const detailRes = await api.get(`/mcp/requirements/${requirement_id}`);
        const { requirement, tasks } = detailRes.data;
        // 2) 拉测试记录
        const testRes = await api.get(
          `/requirements/${requirement_id}/test-records`
        );
        const test_records = testRes.data;
        // 3) 锁住当前 active requirement（覆盖旧的会发警告）
        const switched = activeRequirement && activeRequirement.id !== requirement_id;
        const previousId = activeRequirement?.id;
        activeRequirement = {
          id: requirement_id,
          title: requirement.title,
          phase: "clarification",
          setAt: Date.now(),
        };
        // 4) Superpowers 头脑风暴的引导问题
        const context_for_brainstorm = {
          developer_id: ASSIGNEE_ID,
          current_phase: "clarification",
          suggested_focus_questions: [
            "需求的功能边界是什么？哪些场景不在本需求范围内？",
            "验收标准中的每一项是否都可观测/可测试？",
            "是否存在隐含的跨模块依赖或与现有 API 的冲突？",
          ],
        };
        const payload = {
          requirement: {
            id: requirement.id,
            title: requirement.title,
            description: requirement.description,
            acceptance_criteria: requirement.acceptance_criteria,
            status: requirement.status,
            priority: requirement.priority,
            due_date: requirement.due_date,
          },
          tasks,
          test_records,
          context_for_brainstorm,
        };
        const warn = switched
          ? `（已切换：之前锁定的需求 ${previousId} 已取消）\n`
          : "";
        return {
          content: [
            { type: "text", text: warn + `已锁定需求「${requirement.title}」，开始头脑风暴。` },
            { type: "text", text: JSON.stringify(payload, null, 2) },
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

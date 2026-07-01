TOOLS = [
    {
        "name": "list_my_projects",
        "description": "列出当前开发者有未完成需求的项目",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_iterations",
        "description": "列出指定项目下的迭代",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "list_my_requirements",
        "description": "列出指定迭代中指派给当前开发者的需求",
        "inputSchema": {
            "type": "object",
            "properties": {
                "iteration_id": {"type": "string", "description": "迭代 ID"},
            },
            "required": ["iteration_id"],
        },
    },
    {
        "name": "start_brainstorming",
        "description": "锁定需求并返回头脑风暴所需的完整上下文",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
            },
            "required": ["requirement_id"],
        },
    },
    {
        "name": "list_member_projects",
        "description": "列出当前用户作为成员参与的所有项目（按项目成员资格，不依赖需求分配状态）",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_skills_by_project",
        "description": "获取指定项目的所有 Skill",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "项目 ID"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "get_requirement_detail",
        "description": "获取需求完整详情（含任务列表）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
            },
            "required": ["requirement_id"],
        },
    },
    {
        "name": "sync_tasks",
        "description": "将任务列表同步到平台。首次调用创建任务；任务完成后再次调用可更新状态和工时（按 title 匹配，不删除已有任务）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "tasks": {
                    "type": "array",
                    "description": "任务列表",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "status": {"type": "string", "description": "pending | in_progress | completed | blocked"},
                            "estimated_hours": {"type": "number", "description": "预估工时（小时）"},
                            "actual_hours": {"type": "number", "description": "实际工时（小时）"},
                        },
                        "required": ["title"],
                    },
                },
            },
            "required": ["requirement_id", "tasks"],
        },
    },
    {
        "name": "update_task_status",
        "description": "更新任务状态和 TDD 进度",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "任务 ID"},
                "status": {"type": "string", "description": "新状态"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "submit_test_result",
        "description": "提交 TDD 测试执行记录（RED/GREEN 阶段均可上报）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "task_id": {"type": "string", "description": "任务 ID（可选）"},
                "task_title": {"type": "string", "description": "任务标题（可选）"},
                "tdd_phase": {"type": "string", "description": "TDD 阶段：red / green / refactor"},
                "test_type": {"type": "string", "description": "测试类型：unit / integration，默认 unit"},
                "total_count": {"type": "integer", "description": "总测试数"},
                "passed_count": {"type": "integer", "description": "通过数"},
                "failed_count": {"type": "integer", "description": "失败数"},
                "failed_tests": {"type": "string", "description": "失败用例名称，换行分隔（可选）"},
                "coverage": {"type": "integer", "description": "测试覆盖率百分比（可选）"},
            },
            "required": ["requirement_id", "total_count", "passed_count", "failed_count"],
        },
    },
    {
        "name": "update_requirement_status",
        "description": "更新需求状态（触发状态流转）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "action": {"type": "string", "description": "目标状态，如 in_progress / pending_review"},
            },
            "required": ["requirement_id", "action"],
        },
    },
    {
        "name": "create_document",
        "description": "将设计文档上传到平台，关联到指定需求",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "title": {"type": "string", "description": "文档标题"},
                "content": {"type": "string", "description": "文档内容（Markdown）"},
                "document_type": {
                    "type": "string",
                    "description": "文档类型：design / analysis / api / other",
                    "default": "design",
                },
            },
            "required": ["requirement_id", "title", "content"],
        },
    },
    {
        "name": "get_document",
        "description": "获取平台上指定文档的完整内容（Markdown 正文）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "document_id": {"type": "string", "description": "文档 ID"},
            },
            "required": ["document_id"],
        },
    },
    {
        "name": "setup_dev_environment",
        "description": "安装 superpowers 技能包和 CodeSeer 专属技能到本地 AI 工具",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "download_attachment",
        "description": "下载需求的附件内容（返回 base64 编码）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "requirement_id": {"type": "string", "description": "需求 ID"},
                "attachment_id": {"type": "string", "description": "附件 ID"},
            },
            "required": ["requirement_id", "attachment_id"],
        },
    },
]

ACTIVE_STATUSES = ["assigned", "in_progress"]

TRANSITIONS: dict[str, list[str]] = {
    "draft":           ["assigned"],
    "assigned":        ["in_progress"],
    "in_progress":     ["pending_review"],
    "pending_review":  ["review_approved", "review_rejected"],
    "review_approved": ["completed"],
    "review_rejected": ["in_progress"],
    "completed":       [],
}

KNOWN_TOOLS = {t["name"] for t in TOOLS}

CREATE TABLE IF NOT EXISTS projects (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(200) NOT NULL,
	description TEXT,
	status VARCHAR(9),
	owner_id VARCHAR(36),
	created_by VARCHAR(36),
	created_at DATETIME,
	updated_at DATETIME,
	identifier VARCHAR(50),
	PRIMARY KEY (id)
);
INSERT INTO projects VALUES('d165fe30-cedf-4316-b890-a34821cd2b75','CodeSeer','CodeSeer 是一套面向研发团队的 AI 辅助研发平台。产品经理在平台上管理需求，开发者在 Claude Code / OpenCode / Cursor 等 AI\n  编码工具中直接拉取需求、自动完成开发全流程','ACTIVE',NULL,NULL,'2026-06-19 12:19:21.831325','2026-06-19 12:19:21.831331',NULL);

CREATE TABLE IF NOT EXISTS skills (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(100) NOT NULL,
	version VARCHAR(20),
	module_id VARCHAR(36),
	description TEXT,
	summary TEXT,
	project_id VARCHAR(36),
	knowledge_base_url VARCHAR(500),
	source VARCHAR(14),
	status VARCHAR(10),
	prompt_template TEXT,
	parameters TEXT,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS modules (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	parent_id VARCHAR(36),
	path VARCHAR(500),
	skill_id VARCHAR(36),
	is_active BOOLEAN,
	created_by VARCHAR(36),
	created_at DATETIME,
	updated_at DATETIME,
	project_id VARCHAR(36),
	PRIMARY KEY (id),
	FOREIGN KEY(skill_id) REFERENCES skills (id)
);
INSERT INTO modules VALUES('9bcf8fc9-1480-4e1d-8f5b-9300acc577b1','AI Agent 集成','描述\n  定义 CodeSeer 平台与 AI 编码工具（Claude Code、OpenCode 等）的交互协议。\n  通过 MCP（Model Context Protocol）暴露需求拉取、任务同步、文档上传、状态流转等工具，\n  使 AI Agent 能感知研发上下文、自主推进开发流程。\n\n  这样的好处是：\n  - 模块名直接点明职责（AI Agent 集成，不是泛称"MCP"）\n  - 描述涵盖了工具的能力边界（拉需求、同步任务、上传文档、状态流转）\n  - 归档到这个模块的文档（接口规范、工具说明、cs_setup/cs_start 等）生成 Skill 后，AI 能直接读取来了解如何与平台配合',NULL,NULL,'e055cfb3-9dd7-4b74-bc9c-96917f297f1d',1,NULL,'2026-06-21 01:30:50.819171','2026-06-21 12:31:42.765138','d165fe30-cedf-4316-b890-a34821cd2b75');
INSERT INTO skills VALUES('e055cfb3-9dd7-4b74-bc9c-96917f297f1d','CodeSeer_AI Agent 集成_MCP 集成规范','1.0.0','9bcf8fc9-1480-4e1d-8f5b-9300acc577b1','指导 AI Agent 正确使用 CodeSeer MCP 工具协议，涵盖需求拉取、任务同步、文档上传、状态流转的标准调用方式与约束',NULL,NULL,NULL,'MANUAL','ACTIVE','你是 AI Agent 集成 模块的领域专家。\n\n## 知识库文档（1 份）\n\n- ai-agent-integration（id: `d48b03e1-d1cb-4e23-89e8-0caadf852f5e`）\n\n## 使用说明\n\n当你需要查阅某份文档的具体内容时，调用 MCP 工具：\n\n```\nget_document(document_id=\"<上方对应的 id>\")\n```\n\n工具会返回该文档的完整 Markdown 正文，请基于返回内容回答问题。\n\n## 你的职责\n\n当用户处理 AI Agent 集成 模块相关需求时：\n1. 根据问题判断需要查阅哪份文档，调用 get_document 获取内容\n2. 基于文档内容给出准确回答，并引用具体章节\n3. 在代码建议中体现文档中描述的架构规范与约束\n','{\"temperature\": 0.3, \"max_tokens\": 4000}','2026-06-21 12:31:42.746836','2026-06-21 12:31:42.746844');

CREATE TABLE IF NOT EXISTS state_machine_config (
	id VARCHAR(36) NOT NULL,
	state VARCHAR(50) NOT NULL,
	name VARCHAR(100) NOT NULL,
	description TEXT,
	allowed_transitions TEXT,
	is_initial BOOLEAN,
	is_terminal BOOLEAN,
	order_index INTEGER,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (state)
);
INSERT INTO state_machine_config VALUES('c6e7c30d-b487-4b8d-bcd1-388b76fc55b6','draft','草稿',NULL,'[\"pending_analysis\"]',1,0,0,'2026-06-14 11:34:42.898222','2026-06-14 11:34:42.898227');
INSERT INTO state_machine_config VALUES('2c026a80-11c0-4722-9df2-180944bee5d0','pending_analysis','待分析',NULL,'[\"analyzed\"]',0,0,1,'2026-06-14 11:34:42.898237','2026-06-14 11:34:42.898238');
INSERT INTO state_machine_config VALUES('c98863a6-e75a-4d2a-be52-ba63db70e9cb','analyzed','已分析',NULL,'[\"assigned\"]',0,0,2,'2026-06-14 11:34:42.898246','2026-06-14 11:34:42.898247');
INSERT INTO state_machine_config VALUES('aa76e017-82c4-4632-8ad9-9957dbbc34d4','assigned','已指派',NULL,'[\"claimed\", \"analyzed\"]',0,0,3,'2026-06-14 11:34:42.898254','2026-06-14 11:34:42.898256');
INSERT INTO state_machine_config VALUES('da499252-41f5-426f-be5b-5ca558ff7826','claimed','已领取',NULL,'[\"in_progress\"]',0,0,4,'2026-06-14 11:34:42.898262','2026-06-14 11:34:42.898263');
INSERT INTO state_machine_config VALUES('289284b2-252d-4c52-ada0-ad4efe797c00','in_progress','开发中',NULL,'[\"pending_review\"]',0,0,5,'2026-06-14 11:34:42.898270','2026-06-14 11:34:42.898271');
INSERT INTO state_machine_config VALUES('3fbd216c-d60f-48d1-907c-5a1e2a6aa8c0','pending_review','待评审',NULL,'[\"review_approved\", \"review_rejected\"]',0,0,6,'2026-06-14 11:34:42.898277','2026-06-14 11:34:42.898279');
INSERT INTO state_machine_config VALUES('ba6c6bbf-979b-49e9-861d-a9730adff7f5','review_approved','评审通过',NULL,'[\"completed\"]',0,0,7,'2026-06-14 11:34:42.898285','2026-06-14 11:34:42.898286');
INSERT INTO state_machine_config VALUES('1fb25e95-4e26-41b0-ad4f-8032417c6a45','review_rejected','评审驳回',NULL,'[\"in_progress\"]',0,0,8,'2026-06-14 11:34:42.898292','2026-06-14 11:34:42.898294');
INSERT INTO state_machine_config VALUES('2e7da522-9bbe-46df-b8fb-10e1aca1352c','completed','已完成',NULL,'[]',0,1,9,'2026-06-14 11:34:42.898300','2026-06-14 11:34:42.898301');

CREATE TABLE IF NOT EXISTS custom_fields (
	id VARCHAR(36) NOT NULL,
	field_key VARCHAR(50) NOT NULL,
	field_name VARCHAR(100) NOT NULL,
	field_type VARCHAR(11),
	required BOOLEAN,
	options TEXT,
	default_value TEXT,
	order_index INTEGER,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (field_key)
);

CREATE TABLE IF NOT EXISTS webhooks (
	id VARCHAR(36) NOT NULL,
	name VARCHAR(100) NOT NULL,
	url VARCHAR(500) NOT NULL,
	secret VARCHAR(100),
	events TEXT,
	enabled BOOLEAN,
	max_retries INTEGER,
	retry_interval INTEGER,
	timeout INTEGER,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users (
	id VARCHAR(36) NOT NULL,
	email VARCHAR(200) NOT NULL,
	name VARCHAR(100) NOT NULL,
	role VARCHAR(15),
	avatar_color VARCHAR(20),
	is_active BOOLEAN,
	created_at DATETIME,
	updated_at DATETIME,
	password_hash VARCHAR(200),
	PRIMARY KEY (id),
	UNIQUE (email)
);
INSERT INTO users VALUES('fb32f43f-1755-4041-a6f1-b4e860a54be4','verify@example.com','Verify User','DEVELOPER','#6366f1',1,'2026-06-19 04:03:59.427814','2026-06-19 04:03:59.427816',NULL);
INSERT INTO users VALUES('b7c81bcb-d723-4d19-9f5f-7b19cfa6e9c7','admin','超级管理员','ADMIN','#dc2626',1,NULL,NULL,'$2b$12$a7tMvQhBtryxOKvpR.byz.BPmsmvReRPYIKr.sNRn4pHI89.86d2O');
INSERT INTO users VALUES('6fd46a29-5870-4573-9fee-62904b96a995','liujunbo916@gmail.com','juno','DEVELOPER','#6366f1',1,'2026-06-19 12:11:40.840802','2026-06-19 12:11:40.840808','$2b$12$.hDP/KO.JsrIic4GkO9MK.XWNKZOGQ5KkU36jiHeeiOmj6fE31pHW');
INSERT INTO users VALUES('24d22a77-06ea-4d61-a99b-9b475b2e8f48','luofan0603@gmail.com','luofan','PRODUCT_MANAGER','#6366f1',1,'2026-06-19 12:23:51.995731','2026-06-19 12:23:51.995738','$2b$12$maHXFOGSw4XJkhAFnJJ7v.zUqxYoq1KG8oLeY18olbYEYA8FF02SO');

CREATE TABLE IF NOT EXISTS iterations (
	id VARCHAR(36) NOT NULL,
	project_id VARCHAR(36) NOT NULL,
	name VARCHAR(200) NOT NULL,
	description TEXT,
	status VARCHAR(11),
	planned_release_date DATETIME,
	actual_release_date DATETIME,
	created_by VARCHAR(36),
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);
INSERT INTO iterations VALUES('16f6c007-5d09-458e-830e-1010557d3fd7','d165fe30-cedf-4316-b890-a34821cd2b75','Sprint-1','重构页面','PLANNING','2026-06-30 00:00:00.000000',NULL,NULL,'2026-06-19 13:24:32.446194','2026-06-19 13:24:32.446198');

CREATE TABLE IF NOT EXISTS webhook_deliveries (
	id VARCHAR(36) NOT NULL,
	webhook_id VARCHAR(36) NOT NULL,
	event VARCHAR(100) NOT NULL,
	payload TEXT,
	response_status INTEGER,
	response_body TEXT,
	attempt INTEGER,
	success BOOLEAN,
	error TEXT,
	created_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS requirements (
	id VARCHAR(36) NOT NULL,
	title VARCHAR(200) NOT NULL,
	description TEXT,
	acceptance_criteria TEXT,
	project_id VARCHAR(36) NOT NULL,
	iteration_id VARCHAR(36),
	status VARCHAR(16),
	priority VARCHAR(2),
	assignee_id VARCHAR(36),
	creator_id VARCHAR(36),
	estimated_hours_min INTEGER,
	estimated_hours_max INTEGER,
	actual_hours INTEGER,
	due_date DATETIME,
	custom_fields TEXT,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);
INSERT INTO requirements VALUES('8d010d0b-0816-4b26-8d02-1fbfda75d753','重构整个项目的基础页面风格','【用户角色】\n注册用户\n\n【我要做什么】\n重构页面风格\n\n【为什么需要这个功能】\n现在页面风格比较AI化\n\n【功能详细描述】\n1、设计项目管理、迭代管理、需求管理的页面\n2、参考腾讯的TAPD风格 https://hook.tapd.cn/','','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','COMPLETED','P2','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,NULL,NULL,'2026-06-19 13:28:28.397020','2026-06-20 12:07:35.822349');
INSERT INTO requirements VALUES('781e30b7-b8c7-4764-943b-921960cf19c3','项目管理、迭代管理、需求管理列表分页展示','平台使用人员，希望平台所有的列表页面采用分页展示','','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','ASSIGNED','P2','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,'2026-06-30 00:00:00.000000',NULL,'2026-06-20 11:48:26.283216','2026-06-20 16:09:21.025405');
INSERT INTO requirements VALUES('6540e152-1b65-4360-a68e-1270023cf759','创建需求支持上传附件','## 背景\n创建需求\n\n## 用户故事\n作为 产品经理，我希望 创建需求的页面支持上传附件，以便 AIAgent能获取更多的信息。\n\n## 功能说明\n1、在需求创建页面增加附件上传的功能\n2、AiAgent 再拉取开发需求的时候 要同时拉去需求和对应的附件 以便能更好的理解需求','','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','ASSIGNED','P1','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,'2026-06-30 00:00:00.000000',NULL,'2026-06-21 01:23:53.385241','2026-06-21 01:24:34.610316');

CREATE TABLE IF NOT EXISTS tasks (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36) NOT NULL,
	title VARCHAR(200) NOT NULL,
	description TEXT,
	status VARCHAR(11),
	priority VARCHAR(2),
	order_index INTEGER,
	estimated_hours INTEGER,
	actual_hours INTEGER,
	tdd_red VARCHAR(20),
	tdd_green VARCHAR(20),
	tdd_refactor VARCHAR(20),
	started_at DATETIME,
	completed_at DATETIME,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);
INSERT INTO tasks VALUES('dbfd27f6-4e88-429c-bc5f-d069805d1606','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 1: 安装 Element Plus 依赖','安装 Element Plus 依赖','PENDING','P2',0,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073215','2026-06-20 04:20:22.073218');
INSERT INTO tasks VALUES('e71dd417-8a83-4abd-b055-e84898c03a5f','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 2: 配置 Element Plus 主题变量','配置 Element Plus 主题变量','PENDING','P2',1,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073228','2026-06-20 04:20:22.073229');
INSERT INTO tasks VALUES('dc0cad8c-d1f5-4488-bf9c-5008530002f3','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 3: 创建公共布局组件','创建公共布局组件','PENDING','P2',2,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073236','2026-06-20 04:20:22.073237');
INSERT INTO tasks VALUES('5ffe3bf7-d810-4702-ac72-49c2abbb2e1a','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 4: 重构 Projects 页面','重构 Projects 页面','PENDING','P2',3,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073242','2026-06-20 04:20:22.073243');
INSERT INTO tasks VALUES('f53d4825-4265-4b38-a695-6e57350f4da8','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 5: 重构 Iterations 页面','重构 Iterations 页面','PENDING','P2',4,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073248','2026-06-20 04:20:22.073248');
INSERT INTO tasks VALUES('07319ad6-0ee9-4207-ba56-2c2109bac249','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 6: 重构 Requirements 页面','重构 Requirements 页面','PENDING','P2',5,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073254','2026-06-20 04:20:22.073254');
INSERT INTO tasks VALUES('9dc0c6ef-cc73-40cc-9fac-abab72fc4758','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 7: 重构 ProjectDetail 页面','重构 ProjectDetail 页面','PENDING','P2',6,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073259','2026-06-20 04:20:22.073260');
INSERT INTO tasks VALUES('a1350751-7876-482d-95fb-8e58e70402c6','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 8: 重构 IterationDetail 页面','重构 IterationDetail 页面','PENDING','P2',7,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073264','2026-06-20 04:20:22.073265');
INSERT INTO tasks VALUES('0e9f4b23-547f-4d63-b039-68b06cc04d91','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 9: 重构 RequirementDetail 页面','重构 RequirementDetail 页面','PENDING','P2',8,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073270','2026-06-20 04:20:22.073271');
INSERT INTO tasks VALUES('3220946b-da1b-49ff-b964-f9f903226bca','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 10: 重构 Dashboard 页面','重构 Dashboard 页面','PENDING','P2',9,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073275','2026-06-20 04:20:22.073276');
INSERT INTO tasks VALUES('f66a15c6-63f2-4f01-987c-ca037911d7b5','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 11: 重构 Standup 页面','重构 Standup 页面','PENDING','P2',10,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073280','2026-06-20 04:20:22.073281');
INSERT INTO tasks VALUES('7a38f3c5-5a75-414f-beec-84ccfa52fa9e','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 12: 重构 P3 页面','重构 P3 页面','COMPLETED','P2',11,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073286','2026-06-20 04:20:24.936357');
INSERT INTO tasks VALUES('4243234f-fd0b-4d85-9597-bc69ee09610a','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 13: 重构 Login 页面','重构 Login 页面','COMPLETED','P2',12,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073291','2026-06-20 04:20:25.690538');
INSERT INTO tasks VALUES('d460536b-70fa-492f-8727-bd990d8af7ca','8d010d0b-0816-4b26-8d02-1fbfda75d753','Task 14: 全局样式检查与微调','全局样式检查与微调','COMPLETED','P2',13,NULL,NULL,'pending','pending','pending',NULL,NULL,'2026-06-20 04:20:22.073296','2026-06-20 11:57:39.352006');
INSERT INTO tasks VALUES('06eb63eb-2ec3-4aab-b861-464a185a9964','781e30b7-b8c7-4764-943b-921960cf19c3','后端 — 新增 PaginatedResponse 泛型结构','在 backend/app/schemas/schemas.py 中添加 PaginatedResponse[T] 泛型分页响应模型，供三个列表接口复用','COMPLETED','P2',0,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359607','2026-06-20 16:19:03.444816','2026-06-20 16:47:38.360785');
INSERT INTO tasks VALUES('a3a5b017-d118-448b-9aea-e273ee08f407','781e30b7-b8c7-4764-943b-921960cf19c3','后端 — 改造 list_projects 接口','改造 GET /projects，支持 page、page_size 参数，返回 PaginatedResponse[ProjectResponse]，包含 total count 和 offset  LIMIT 分页','COMPLETED','P2',1,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359634','2026-06-20 16:19:03.444833','2026-06-20 16:47:38.360791');
INSERT INTO tasks VALUES('e72fee35-9cf7-47d5-85c0-55154b2f53ec','781e30b7-b8c7-4764-943b-921960cf19c3','后端 — 改造 list_iterations 接口','改造 GET /iterations，支持 page、page_size 参数，返回 PaginatedResponse[IterationResponse]','COMPLETED','P2',2,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359647','2026-06-20 16:19:03.444844','2026-06-20 16:47:38.360795');
INSERT INTO tasks VALUES('406ba567-ef3a-4b2c-b880-bda5f130d3be','781e30b7-b8c7-4764-943b-921960cf19c3','后端 — 改造 list_requirements 接口','改造 GET /requirements，启用已有的 page、page_size 参数，返回 PaginatedResponse[RequirementResponse]，保持现有的 project_id、iteration_id、assignee_id、status 筛选能力','COMPLETED','P2',3,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359658','2026-06-20 16:19:03.444853','2026-06-20 16:47:38.360789');
INSERT INTO tasks VALUES('e9447890-0a28-4f66-97db-6345c6d689c1','781e30b7-b8c7-4764-943b-921960cf19c3','前端 — 新增 usePagination Composable','创建 frontend/src/composables/usePagination.ts，封装分页状态管理（items、total、page、pageSize、loading）和分页方法（fetchPage、onPageChange、onSizeChange）','COMPLETED','P2',4,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359669','2026-06-20 16:19:03.444863','2026-06-20 16:47:38.360797');
INSERT INTO tasks VALUES('f54b4dc2-4b3b-4cc8-a2e6-8b70cd54424a','781e30b7-b8c7-4764-943b-921960cf19c3','前端 — 改造 Projects.vue','引入 usePagination，替换 projects ref 为分页 composable，保留前端搜索过滤但移除客户端分页逻辑，添加 el-pagination 组件','COMPLETED','P2',5,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359679','2026-06-20 16:19:03.444872','2026-06-20 16:47:38.360798');
INSERT INTO tasks VALUES('b3702d5e-6540-4c65-ab2e-fb22744fd4ef','781e30b7-b8c7-4764-943b-921960cf19c3','前端 — 改造 Iterations.vue','引入 usePagination，替换 iterations ref 为分页 composable，保留前端搜索/状态筛选但移除客户端分页逻辑，添加 el-pagination 组件','COMPLETED','P2',6,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359689','2026-06-20 16:19:03.444880','2026-06-20 16:47:38.360793');
INSERT INTO tasks VALUES('01c4e5b7-e6c0-4f7b-95cb-9021d2e2388e','781e30b7-b8c7-4764-943b-921960cf19c3','前端 — 改造 Requirements.vue','引入 usePagination，替换 requirements ref 为分页 composable，保留前端搜索/状态筛选但移除客户端分页逻辑，添加 el-pagination 组件','COMPLETED','P2',7,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359699','2026-06-20 16:19:03.444890','2026-06-20 16:47:38.360782');
INSERT INTO tasks VALUES('0d3e7749-5439-4a63-b05f-0f8209d766d3','781e30b7-b8c7-4764-943b-921960cf19c3','前端 — 同步 API 层适配','检查并适配 frontend/src/api/index.ts，确保各 API 方法能正确处理新的 { items: [], total, page, page_size } 响应格式','COMPLETED','P2',8,NULL,1,'pending','pending','pending',NULL,'2026-06-20 16:47:38.359709','2026-06-20 16:19:03.444899','2026-06-20 16:47:38.360787');
INSERT INTO tasks VALUES('768928e2-e59c-4fb9-b3dd-aa8ce725df02','6540e152-1b65-4360-a68e-1270023cf759','Task 1: 创建 RequirementAttachment 模型','在 backend/app/models/models.py 添加 RequirementAttachment model','COMPLETED','P2',0,0,0,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872589','2026-06-21 13:18:53.850548','2026-06-21 14:24:35.873649');
INSERT INTO tasks VALUES('9ba6fc9e-110e-484a-91ee-e7092818a39e','6540e152-1b65-4360-a68e-1270023cf759','Task 2: 实现附件 API 端点','创建 backend/app/api/attachments.py，实现上传/下载/删除/列表 API','COMPLETED','P2',1,2,2,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872615','2026-06-21 13:18:53.850568','2026-06-21 14:24:35.873650');
INSERT INTO tasks VALUES('540b8c68-4708-4fb2-bf1c-f5179cb8e849','6540e152-1b65-4360-a68e-1270023cf759','Task 3: 前端附件 API 客户端','在 frontend/src/api/index.ts 添加 attachmentsApi','COMPLETED','P2',2,0,0,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872626','2026-06-21 13:18:53.850581','2026-06-21 14:24:35.873648');
INSERT INTO tasks VALUES('0fd9dcad-cb6f-4ee6-af86-d4db2bccd5c6','6540e152-1b65-4360-a68e-1270023cf759','Task 4: 扩展 get_requirement 返回附件','修改 mcp_handlers.py 的 _get_requirement_detail 返回 attachments 数组','COMPLETED','P2',3,1,1,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872637','2026-06-21 13:18:53.850594','2026-06-21 14:24:35.873637');
INSERT INTO tasks VALUES('24933a62-0b89-43b8-8ee5-6922c99b660d','6540e152-1b65-4360-a68e-1270023cf759','Task 5: 新增 download_attachment MCP 工具','添加 download_attachment MCP tool 定义和处理器','COMPLETED','P2',4,1,1,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872646','2026-06-21 13:18:53.850607','2026-06-21 14:24:35.873645');
INSERT INTO tasks VALUES('5eb8ac50-4c45-4b3d-92e3-a1acb9199617','6540e152-1b65-4360-a68e-1270023cf759','Task 6: 创建需求页添加附件上传','在 Requirements.vue wizard 第 2 步添加 el-upload 组件','COMPLETED','P2',5,1,1,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872655','2026-06-21 13:18:53.850618','2026-06-21 14:24:35.873648');
INSERT INTO tasks VALUES('3c93cbb0-a464-47d7-b30b-59d71bf706b0','6540e152-1b65-4360-a68e-1270023cf759','Task 7: 需求详情页显示附件','在 RequirementDetail.vue 添加附件 tab 页','COMPLETED','P2',6,1,1,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872663','2026-06-21 13:18:53.850629','2026-06-21 14:24:35.873647');
INSERT INTO tasks VALUES('a814125c-a5b5-43b1-a8c2-7de245d139b3','6540e152-1b65-4360-a68e-1270023cf759','Task 8: 集成测试','编写完整附件流程测试','COMPLETED','P2',7,1,1,'pending','pending','pending',NULL,'2026-06-21 14:24:35.872672','2026-06-21 13:18:53.850641','2026-06-21 14:24:35.873650');

CREATE TABLE IF NOT EXISTS documents (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36),
	module_id VARCHAR(36),
	title VARCHAR(200) NOT NULL,
	document_type VARCHAR(8),
	content TEXT,
	summary TEXT,
	key_points TEXT,
	status VARCHAR(10),
	processing_status VARCHAR(10),
	version INTEGER,
	created_by VARCHAR(36),
	created_at DATETIME,
	updated_at DATETIME,
	archived_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS requirement_phases (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36) NOT NULL,
	phase VARCHAR(13) NOT NULL,
	status VARCHAR(11),
	notes TEXT,
	started_at DATETIME,
	completed_at DATETIME,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS requirement_history (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36) NOT NULL,
	action VARCHAR(18) NOT NULL,
	field_name VARCHAR(100),
	old_value TEXT,
	new_value TEXT,
	actor VARCHAR(100),
	comment TEXT,
	created_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS unit_test_records (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36) NOT NULL,
	task_id VARCHAR(36),
	task_title VARCHAR(200),
	test_type VARCHAR(50),
	total_count INTEGER,
	passed_count INTEGER,
	failed_count INTEGER,
	failed_tests TEXT,
	coverage INTEGER,
	result VARCHAR(10),
	executed_at DATETIME,
	created_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS document_versions (
	id VARCHAR(36) NOT NULL,
	document_id VARCHAR(36) NOT NULL,
	version INTEGER NOT NULL,
	content TEXT,
	summary TEXT,
	change_note VARCHAR(500),
	created_by VARCHAR(36),
	created_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS code_changes (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36),
	task_id VARCHAR(36),
	title VARCHAR(200) NOT NULL,
	files_changed INTEGER,
	lines_added INTEGER,
	lines_deleted INTEGER,
	modules_affected TEXT,
	exceptions TEXT,
	diff_path VARCHAR(500),
	diff_size INTEGER,
	status VARCHAR(7),
	created_by VARCHAR(100),
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS access_tokens (
	id VARCHAR(36) NOT NULL,
	user_id VARCHAR(36) NOT NULL,
	token_hash VARCHAR(64) NOT NULL,
	token_prefix VARCHAR(16) NOT NULL,
	name VARCHAR(100) NOT NULL,
	expires_at DATETIME,
	last_used_at DATETIME,
	is_active BOOLEAN,
	created_at DATETIME,
	PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS requirement_attachments (
	id VARCHAR(36) NOT NULL,
	requirement_id VARCHAR(36) NOT NULL,
	filename VARCHAR(255) NOT NULL,
	file_size INTEGER NOT NULL,
	content_type VARCHAR(100),
	storage_path VARCHAR(500) NOT NULL,
	storage_backend VARCHAR(20),
	created_at DATETIME,
	PRIMARY KEY (id)
);

ALTER TABLE modules ADD FOREIGN KEY (project_id) REFERENCES projects(id);
ALTER TABLE modules ADD FOREIGN KEY (parent_id) REFERENCES modules(id);
ALTER TABLE iterations ADD FOREIGN KEY (project_id) REFERENCES projects(id);
ALTER TABLE webhook_deliveries ADD FOREIGN KEY (webhook_id) REFERENCES webhooks(id);
ALTER TABLE requirements ADD FOREIGN KEY (project_id) REFERENCES projects(id);
ALTER TABLE requirements ADD FOREIGN KEY (iteration_id) REFERENCES iterations(id);
ALTER TABLE tasks ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE documents ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE documents ADD FOREIGN KEY (module_id) REFERENCES modules(id);
ALTER TABLE requirement_phases ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE requirement_history ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE unit_test_records ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE unit_test_records ADD FOREIGN KEY (task_id) REFERENCES tasks(id);
ALTER TABLE document_versions ADD FOREIGN KEY (document_id) REFERENCES documents(id);
ALTER TABLE code_changes ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);
ALTER TABLE code_changes ADD FOREIGN KEY (task_id) REFERENCES tasks(id);
ALTER TABLE access_tokens ADD FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE requirement_attachments ADD FOREIGN KEY (requirement_id) REFERENCES requirements(id);

CREATE UNIQUE INDEX uq_projects_identifier ON projects(identifier);
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE projects (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	status VARCHAR(9), 
	owner_id VARCHAR(36), 
	created_by VARCHAR(36), 
	created_at DATETIME, 
	updated_at DATETIME, identifier VARCHAR(50), 
	PRIMARY KEY (id)
);
INSERT INTO projects VALUES('d165fe30-cedf-4316-b890-a34821cd2b75','CodeSeer',replace('CodeSeer 是一套面向研发团队的 AI 辅助研发平台。产品经理在平台上管理需求，开发者在 Claude Code / OpenCode / Cursor 等 AI\n  编码工具中直接拉取需求、自动完成开发全流程','\n',char(10)),'ACTIVE',NULL,NULL,'2026-06-19 12:19:21.831325','2026-06-19 12:19:21.831331',NULL);
CREATE TABLE modules (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	parent_id VARCHAR(36), 
	path VARCHAR(500), 
	skill_id VARCHAR(36), 
	is_active BOOLEAN, 
	created_by VARCHAR(36), 
	created_at DATETIME, 
	updated_at DATETIME, project_id VARCHAR(36) REFERENCES projects(id), 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES modules (id), 
	FOREIGN KEY(skill_id) REFERENCES skills (id)
);
INSERT INTO modules VALUES('9bcf8fc9-1480-4e1d-8f5b-9300acc577b1','AI Agent 集成',replace('描述\n  定义 CodeSeer 平台与 AI 编码工具（Claude Code、OpenCode 等）的交互协议。\n  通过 MCP（Model Context Protocol）暴露需求拉取、任务同步、文档上传、状态流转等工具，\n  使 AI Agent 能感知研发上下文、自主推进开发流程。\n\n  这样的好处是：\n  - 模块名直接点明职责（AI Agent 集成，不是泛称"MCP"）\n  - 描述涵盖了工具的能力边界（拉需求、同步任务、上传文档、状态流转）\n  - 归档到这个模块的文档（接口规范、工具说明、cs_setup/cs_start 等）生成 Skill 后，AI 能直接读取来了解如何与平台配合','\n',char(10)),NULL,NULL,'e055cfb3-9dd7-4b74-bc9c-96917f297f1d',1,NULL,'2026-06-21 01:30:50.819171','2026-06-21 12:31:42.765138','d165fe30-cedf-4316-b890-a34821cd2b75');
CREATE TABLE skills (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(module_id) REFERENCES modules (id)
);
INSERT INTO skills VALUES('e055cfb3-9dd7-4b74-bc9c-96917f297f1d','CodeSeer_AI Agent 集成_MCP 集成规范','1.0.0','9bcf8fc9-1480-4e1d-8f5b-9300acc577b1','指导 AI Agent 正确使用 CodeSeer MCP 工具协议，涵盖需求拉取、任务同步、文档上传、状态流转的标准调用方式与约束',NULL,NULL,NULL,'MANUAL','ACTIVE',replace('你是 AI Agent 集成 模块的领域专家。\n\n## 知识库文档（1 份）\n\n- ai-agent-integration（id: `d48b03e1-d1cb-4e23-89e8-0caadf852f5e`）\n\n## 使用说明\n\n当你需要查阅某份文档的具体内容时，调用 MCP 工具：\n\n```\nget_document(document_id="<上方对应的 id>")\n```\n\n工具会返回该文档的完整 Markdown 正文，请基于返回内容回答问题。\n\n## 你的职责\n\n当用户处理 AI Agent 集成 模块相关需求时：\n1. 根据问题判断需要查阅哪份文档，调用 get_document 获取内容\n2. 基于文档内容给出准确回答，并引用具体章节\n3. 在代码建议中体现文档中描述的架构规范与约束\n','\n',char(10)),'{"temperature": 0.3, "max_tokens": 4000}','2026-06-21 12:31:42.746836','2026-06-21 12:31:42.746844');
CREATE TABLE state_machine_config (
	id VARCHAR(36) NOT NULL, 
	state VARCHAR(50) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	allowed_transitions TEXT, 
	is_initial BOOLEAN, 
	is_terminal BOOLEAN, 
	"order" INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (state)
);
INSERT INTO state_machine_config VALUES('c6e7c30d-b487-4b8d-bcd1-388b76fc55b6','draft','草稿',NULL,'["pending_analysis"]',1,0,0,'2026-06-14 11:34:42.898222','2026-06-14 11:34:42.898227');
INSERT INTO state_machine_config VALUES('2c026a80-11c0-4722-9df2-180944bee5d0','pending_analysis','待分析',NULL,'["analyzed"]',0,0,1,'2026-06-14 11:34:42.898237','2026-06-14 11:34:42.898238');
INSERT INTO state_machine_config VALUES('c98863a6-e75a-4d2a-be52-ba63db70e9cb','analyzed','已分析',NULL,'["assigned"]',0,0,2,'2026-06-14 11:34:42.898246','2026-06-14 11:34:42.898247');
INSERT INTO state_machine_config VALUES('aa76e017-82c4-4632-8ad9-9957dbbc34d4','assigned','已指派',NULL,'["claimed", "analyzed"]',0,0,3,'2026-06-14 11:34:42.898254','2026-06-14 11:34:42.898256');
INSERT INTO state_machine_config VALUES('da499252-41f5-426f-be5b-5ca558ff7826','claimed','已领取',NULL,'["in_progress"]',0,0,4,'2026-06-14 11:34:42.898262','2026-06-14 11:34:42.898263');
INSERT INTO state_machine_config VALUES('289284b2-252d-4c52-ada0-ad4efe797c00','in_progress','开发中',NULL,'["pending_review"]',0,0,5,'2026-06-14 11:34:42.898270','2026-06-14 11:34:42.898271');
INSERT INTO state_machine_config VALUES('3fbd216c-d60f-48d1-907c-5a1e2a6aa8c0','pending_review','待评审',NULL,'["review_approved", "review_rejected"]',0,0,6,'2026-06-14 11:34:42.898277','2026-06-14 11:34:42.898279');
INSERT INTO state_machine_config VALUES('ba6c6bbf-979b-49e9-861d-a9730adff7f5','review_approved','评审通过',NULL,'["completed"]',0,0,7,'2026-06-14 11:34:42.898285','2026-06-14 11:34:42.898286');
INSERT INTO state_machine_config VALUES('1fb25e95-4e26-41b0-ad4f-8032417c6a45','review_rejected','评审驳回',NULL,'["in_progress"]',0,0,8,'2026-06-14 11:34:42.898292','2026-06-14 11:34:42.898294');
INSERT INTO state_machine_config VALUES('2e7da522-9bbe-46df-b8fb-10e1aca1352c','completed','已完成',NULL,'[]',0,1,9,'2026-06-14 11:34:42.898300','2026-06-14 11:34:42.898301');
CREATE TABLE custom_fields (
	id VARCHAR(36) NOT NULL, 
	field_key VARCHAR(50) NOT NULL, 
	field_name VARCHAR(100) NOT NULL, 
	field_type VARCHAR(11), 
	required BOOLEAN, 
	options TEXT, 
	default_value TEXT, 
	"order" INTEGER, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (field_key)
);
CREATE TABLE webhooks (
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
CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	email VARCHAR(200) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	role VARCHAR(15), 
	avatar_color VARCHAR(20), 
	is_active BOOLEAN, 
	created_at DATETIME, 
	updated_at DATETIME, password_hash VARCHAR(200), 
	PRIMARY KEY (id), 
	UNIQUE (email)
);
INSERT INTO users VALUES('fb32f43f-1755-4041-a6f1-b4e860a54be4','verify@example.com','Verify User','DEVELOPER','#6366f1',1,'2026-06-19 04:03:59.427814','2026-06-19 04:03:59.427816',NULL);
INSERT INTO users VALUES('b7c81bcb-d723-4d19-9f5f-7b19cfa6e9c7','admin','超级管理员','ADMIN','#dc2626',1,NULL,NULL,'$2b$12$a7tMvQhBtryxOKvpR.byz.BPmsmvReRPYIKr.sNRn4pHI89.86d2O');
INSERT INTO users VALUES('6fd46a29-5870-4573-9fee-62904b96a995','liujunbo916@gmail.com','juno','DEVELOPER','#6366f1',1,'2026-06-19 12:11:40.840802','2026-06-19 12:11:40.840808','$2b$12$.hDP/KO.JsrIic4GkO9MK.XWNKZOGQ5KkU36jiHeeiOmj6fE31pHW');
INSERT INTO users VALUES('24d22a77-06ea-4d61-a99b-9b475b2e8f48','luofan0603@gmail.com','luofan','PRODUCT_MANAGER','#6366f1',1,'2026-06-19 12:23:51.995731','2026-06-19 12:23:51.995738','$2b$12$maHXFOGSw4XJkhAFnJJ7v.zUqxYoq1KG8oLeY18olbYEYA8FF02SO');
CREATE TABLE iterations (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id)
);
INSERT INTO iterations VALUES('16f6c007-5d09-458e-830e-1010557d3fd7','d165fe30-cedf-4316-b890-a34821cd2b75','Sprint-1','重构页面','PLANNING','2026-06-30 00:00:00.000000',NULL,NULL,'2026-06-19 13:24:32.446194','2026-06-19 13:24:32.446198');
CREATE TABLE webhook_deliveries (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(webhook_id) REFERENCES webhooks (id)
);
CREATE TABLE requirements (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id), 
	FOREIGN KEY(iteration_id) REFERENCES iterations (id)
);
INSERT INTO requirements VALUES('8d010d0b-0816-4b26-8d02-1fbfda75d753','重构整个项目的基础页面风格',replace('【用户角色】\n注册用户\n\n【我要做什么】\n重构页面风格\n\n【为什么需要这个功能】\n现在页面风格比较AI化\n\n【功能详细描述】\n1、设计项目管理、迭代管理、需求管理的页面\n2、参考腾讯的TAPD风格 https://hook.tapd.cn/','\n',char(10)),'','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','COMPLETED','P2','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,NULL,NULL,'2026-06-19 13:28:28.397020','2026-06-20 12:07:35.822349');
INSERT INTO requirements VALUES('781e30b7-b8c7-4764-943b-921960cf19c3','项目管理、迭代管理、需求管理列表分页展示','平台使用人员，希望平台所有的列表页面采用分页展示','','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','ASSIGNED','P2','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,'2026-06-30 00:00:00.000000',NULL,'2026-06-20 11:48:26.283216','2026-06-20 16:09:21.025405');
INSERT INTO requirements VALUES('6540e152-1b65-4360-a68e-1270023cf759','创建需求支持上传附件',replace('## 背景\n创建需求\n\n## 用户故事\n作为 产品经理，我希望 创建需求的页面支持上传附件，以便 AIAgent能获取更多的信息。\n\n## 功能说明\n1、在需求创建页面增加附件上传的功能\n2、AiAgent 再拉取开发需求的时候 要同时拉去需求和对应的附件 以便能更好的理解需求','\n',char(10)),'','d165fe30-cedf-4316-b890-a34821cd2b75','16f6c007-5d09-458e-830e-1010557d3fd7','ASSIGNED','P1','6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,NULL,NULL,'2026-06-30 00:00:00.000000',NULL,'2026-06-21 01:23:53.385241','2026-06-21 01:24:34.610316');
CREATE TABLE tasks (
	id VARCHAR(36) NOT NULL, 
	requirement_id VARCHAR(36) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	status VARCHAR(11), 
	priority VARCHAR(2), 
	"order" INTEGER, 
	estimated_hours INTEGER, 
	actual_hours INTEGER, 
	tdd_red VARCHAR(20), 
	tdd_green VARCHAR(20), 
	tdd_refactor VARCHAR(20), 
	started_at DATETIME, 
	completed_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id)
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
CREATE TABLE documents (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id), 
	FOREIGN KEY(module_id) REFERENCES modules (id)
);
INSERT INTO documents VALUES('5446f1b9-d3e8-40f9-8540-999f56f5acbb','8d010d0b-0816-4b26-8d02-1fbfda75d753',NULL,'页面风格重构设计方案 v2.0','DESIGN',replace('# 页面风格重构设计方案\n\n**日期**: 2026-06-20\n**需求**: 重构整个项目的基础页面风格\n**参考**: TAPD 腾讯敏捷协作平台风格\n**版本**: v2.0\n\n---\n\n## 1. 设计目标\n\n将现有"AI 化"紫/靛蓝渐变风格重构为腾讯 TAPD 的企业级蓝色系风格，具体目标：\n- 整体配色系统统一为 TAPD 蓝色系\n- 引入 Element Plus 组件库统一 UI\n- 侧边栏改造为 ElMenu 图标模式\n- 所有页面表格/表单/弹窗组件统一\n- 视觉上接近 TAPD 企业协作平台风格\n\n---\n\n## 2. 技术选型\n\n| 类别 | 选择 | 说明 |\n|------|------|------|\n| UI 组件库 | **Element Plus** | Vue 3 原生、企业风格与 TAPD 相近、定制灵活 |\n| 图标库 | @element-plus/icons-vue | Element Plus 官方图标 |\n| 样式方案 | CSS 变量 + Element Plus 主题覆盖 | 保留现有变量系统，补充 el- 变量覆盖 |\n\n---\n\n## 3. 配色系统（扩展现有变量）\n\n```css\n:root {\n  /* 已有变量（保留） */\n  --color-primary: #2d5bff;\n  --color-primary-hover: #1e4ae8;\n  --color-bg: #f5f7ff;\n  --color-success: #00a870;\n  --color-warning: #ff9a2e;\n  --color-error: #ff4533;\n  \n  /* Element Plus 主题覆盖 */\n  --el-color-primary: #2d5bff;\n  --el-color-primary-light-3: #5a7bff;\n  --el-color-primary-light-5: #8aa3ff;\n  --el-color-primary-light-7: #b8cbff;\n  --el-color-primary-light-8: #d0deff;\n  --el-color-primary-light-9: #e8eeff;\n  --el-border-radius-base: 8px;\n  --el-font-family: -apple-system, BlinkMacSystemFont, ''Segoe UI'', Roboto, ''Inter'', ''Helvetica Neue'', Arial, sans-serif;\n}\n```\n\n---\n\n## 4. 侧边栏改造\n\n### 目标形态\n- 宽度：56px（收起） / 200px（展开）\n- 模式：ElMenu vertical 模式，collapse 控制\n- 图标：支持 tooltip 提示\n\n### 组件映射\n| 现有 | 重构后 |\n|------|--------|\n| 纯 CSS nav | ElMenu + ElMenuItem |\n| 文字 label | tooltip 提示 |\n| router-link-active | Element Plus active 机制 |\n\n### 布局结构\n```\n┌─────┬────────────────────────────────────┐\n│ 侧边栏 │          Main Content             │\n│ 56px  │                                    │\n│ ElMenu │  Topbar + RouterView              │\n│        │                                    │\n└─────┴────────────────────────────────────┘\n```\n\n---\n\n## 5. 页面重构清单\n\n### P0 - 核心页面（表格主导）\n| 页面 | 路由 | 核心组件 | 优先级 |\n|------|------|----------|--------|\n| Projects | /projects | ElTable, ElInput, ElButton | P0 |\n| Iterations | /iterations | ElTable, ElSelect, ElButton | P0 |\n| Requirements | /requirements | ElTable, ElSelect, ElButton | P0 |\n| ProjectDetail | /project/:id | ElTabs, ElTable | P0 |\n\n### P1 - 详情页（表单主导）\n| 页面 | 路由 | 核心组件 | 优先级 |\n|------|------|----------|--------|\n| IterationDetail | /iteration/:id | ElForm, ElInput | P1 |\n| RequirementDetail | /requirement/:id | ElForm, ElInput | P1 |\n\n### P2 - 功能页\n| 页面 | 路由 | 核心组件 | 优先级 |\n|------|------|----------|--------|\n| Dashboard | /dashboard | ElCard, ElStatistic | P2 |\n| Standup | /standup | ElDatePicker, ElCard | P2 |\n\n### P3 - 配置页\n| 页面 | 路由 | 核心组件 | 优先级 |\n|------|------|----------|--------|\n| Login | /login | ElForm | P3 |\n| Settings | /settings | ElForm, ElSwitch | P3 |\n| Users | /users | ElTable, ElDialog | P3 |\n| McpConfig | /mcp-config | ElForm, ElInput | P3 |\n| Modules | /modules | ElTable, ElDialog | P3 |\n| Webhooks | /webhooks | ElTable, ElDialog | P3 |\n| Documents | /documents | ElTable, ElUpload | P3 |\n\n---\n\n## 6. 组件统一规范\n\n### 6.1 表格（ElTable）\n```css\n.el-table {\n  --el-table-border-color: #e8e9eb;\n  --el-table-header-bg-color: #f5f7ff;\n  --el-table-row-hover-bg-color: #fafafa;\n  border-radius: 12px;\n  overflow: hidden;\n}\n```\n\n### 6.2 按钮\n```css\n.el-button--primary {\n  --el-button-bg-color: #2d5bff;\n  --el-button-border-color: #2d5bff;\n  --el-button-hover-bg-color: #1e4ae8;\n  --el-button-border-radius: 8px;\n}\n```\n\n### 6.3 弹窗（ElDialog）\n```css\n.el-dialog {\n  --el-dialog-border-radius: 14px;\n}\n```\n\n### 6.4 表单（ElForm）\n```css\n.el-form-item__label {\n  font-weight: 600;\n  color: #1f2329;\n}\n```\n\n### 6.5 输入框（ElInput）\n```css\n.el-input {\n  --el-input-border-radius: 8px;\n}\n```\n\n---\n\n## 7. 实施顺序\n\n### 阶段一：基础设施（1-2 天）\n1. 安装 Element Plus 及图标库\n2. 配置 Element Plus 主题变量覆盖\n3. 重构侧边栏为 ElMenu 组件\n4. 提取公共布局组件（Layout.vue）\n\n### 阶段二：P0 页面（2-3 天）\n5. Projects 页面重构\n6. Iterations 页面重构\n7. Requirements 页面重构\n8. ProjectDetail 页面重构\n\n### 阶段三：P1 页面（1-2 天）\n9. IterationDetail 页面重构\n10. RequirementDetail 页面重构\n\n### 阶段四：P2/P3 页面（1-2 天）\n11. Dashboard/Standup 重构\n12. 配置类页面重构（Settings/Users/McpConfig/Modules/Webhooks/Documents）\n13. Login 页面重构\n\n---\n\n## 8. 验收标准\n\n- [ ] Element Plus 主题变量覆盖完成，整体视觉符合 TAPD 风格\n- [ ] 侧边栏改为 ElMenu 图标模式，支持展开/收起\n- [ ] 所有表格页面统一使用 ElTable（Projects/Iterations/Requirements/Dashboard 等）\n- [ ] 所有表单页面统一使用 ElForm\n- [ ] 所有弹窗统一使用 ElDialog\n- [ ] 14+ 页面全部重构完成\n- [ ] 响应式适配（侧边栏收起时内容区自适应）\n\n---\n\n## 9. 不在范围内\n\n- 后端 API 修改\n- 业务逻辑变更\n- 现有组件库（如 @vueuse）替换\n- 移动端适配','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-20 02:52:41.595088','2026-06-20 02:52:41.595094',NULL);
INSERT INTO documents VALUES('f47890d8-6ae8-4425-88a6-6128370135c1','8d010d0b-0816-4b26-8d02-1fbfda75d753',NULL,'页面风格重构实现计划','ANALYSIS',replace('# 页面风格重构 Implementation Plan\n\n**Goal:** 将 14+ 页面重构为 TAPD 企业蓝色风格，引入 Element Plus 组件库统一 UI\n\n**Tech Stack:** Vue 3, Element Plus, TypeScript, Vite\n\n---\n\n## 实现任务清单\n\n| Task | 任务名称 | 描述 |\n|------|----------|------|\n| 1 | 安装 Element Plus 依赖 | npm install element-plus @element-plus/icons-vue |\n| 2 | 配置 Element Plus 主题变量 | 在 main.css 中添加 el- 变量覆盖 |\n| 3 | 创建公共布局组件 | Layout.vue 包含侧边栏 ElMenu + 主内容区 |\n| 4 | 重构 Projects 页面 | 使用 ElTable/ElInput/ElButton/ElDialog |\n| 5 | 重构 Iterations 页面 | 使用 ElTable/ElSelect |\n| 6 | 重构 Requirements 页面 | 使用 ElTable/ElSelect |\n| 7 | 重构 ProjectDetail 页面 | 使用 ElTabs/ElTable |\n| 8 | 重构 IterationDetail 页面 | 使用 ElForm/ElInput |\n| 9 | 重构 RequirementDetail 页面 | 使用 ElForm/ElSelect |\n| 10 | 重构 Dashboard 页面 | 使用 ElCard/ElStatistic |\n| 11 | 重构 Standup 页面 | 使用 ElDatePicker/ElCard |\n| 12 | 重构 P3 页面 | Settings/Users/McpConfig/Modules/Webhooks/Documents |\n| 13 | 重构 Login 页面 | 使用 ElForm/ElInput |\n| 14 | 全局样式检查与微调 | 统一协调的全局样式 |\n\n---\n\n## 验收标准\n\n- [ ] Element Plus 主题变量覆盖完成\n- [ ] 侧边栏改为 ElMenu 图标模式\n- [ ] 所有表格页面统一使用 ElTable\n- [ ] 所有表单页面统一使用 ElForm\n- [ ] 所有弹窗统一使用 ElDialog\n- [ ] 14+ 页面全部重构完成\n- [ ] 整体视觉符合 TAPD 风格','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-20 02:52:50.166459','2026-06-20 02:52:50.166478',NULL);
INSERT INTO documents VALUES('ccec90b3-d846-4716-b1c1-31eaf75f5cfe','781e30b7-b8c7-4764-943b-921960cf19c3',NULL,'列表分页展示 — 设计文档','DESIGN',replace('# 列表分页展示 — 设计文档\n\n**需求**: 项目管理、迭代管理、需求管理列表分页展示  \n**状态**: 已批准  \n**版本**: 1.0  \n**日期**: 2026-06-21\n\n---\n\n## 1. 概述\n\n为项目管理、迭代管理、需求管理三个列表页面添加后端分页支持，采用基于偏移量的分页方案（`?page=1&page_size=20`），返回统一分页响应结构 `{ items: [], total, page, page_size }`。前端封装 `usePagination` composable，复用 Element Plus `el-pagination` 组件。\n\n---\n\n## 2. 后端改动\n\n### 2.1 统一分页响应结构\n\n```python\nclass PaginatedResponse(BaseModel):\n    items: List[Any]\n    total: int\n    page: int\n    page_size: int\n```\n\n### 2.2 涉及接口\n\n| 接口 | 改动 |\n|------|------|\n| `GET /projects` | 添加 `page`、`page_size` query 参数，返回 `PaginatedResponse[ProjectResponse]` |\n| `GET /iterations` | 添加 `page`、`page_size` query 参数，返回 `PaginatedResponse[IterationResponse]` |\n| `GET /requirements` | 已有 `page`、`page_size` 参数（暂不支持），统一改造 |\n\n**分页默认值**: `page=1`, `page_size=20`\n\n### 2.3 响应格式示例\n\n```json\n{\n  "items": [/* Project objects */],\n  "total": 45,\n  "page": 1,\n  "page_size": 20\n}\n```\n\n---\n\n## 3. 前端改动\n\n### 3.1 `usePagination` Composable\n\n```typescript\n// src/composables/usePagination.ts\nexport function usePagination<T>(fetcher: (page: number, pageSize: number) => Promise<{ items: T[], total: number }>) {\n  const items = ref<T[]>([])\n  const total = ref(0)\n  const page = ref(1)\n  const pageSize = ref(20)\n  const loading = ref(false)\n\n  const fetchPage = async (p: number) => {\n    loading.value = true\n    try {\n      const res = await fetcher(p, pageSize.value)\n      items.value = res.items\n      total.value = res.total\n      page.value = p\n    } finally {\n      loading.value = false\n    }\n  }\n\n  const onPageChange = (p: number) => fetchPage(p)\n  const onSizeChange = (size: number) => { pageSize.value = size; fetchPage(1) }\n\n  return { items, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange }\n}\n```\n\n### 3.2 页面改造\n\n三个页面（Projects、Iterations、Requirements）统一改造：\n\n1. **移除**客户端 computed 过滤逻辑中的分页相关代码\n2. **移除** `displayedRequirements` 等前端分页 computed\n3. **引入** `usePagination` composable\n4. **添加** `el-pagination` 组件，包含：背景色、页码按钮、每页条数选择器、跳转输入框\n5. **保留**搜索/状态筛选功能，筛选时重置到第一页\n\n```vue\n<el-pagination\n  background\n  layout="total, sizes, prev, pager, next, jumper"\n  :total="total"\n  :page-size="pageSize"\n  :current-page="page"\n  @size-change="onSizeChange"\n  @current-change="onPageChange"\n/>\n```\n\n---\n\n## 4. 数据流\n\n```\n用户操作（翻页/筛选）\n    ↓\n前端调用 fetcher(page, pageSize)\n    ↓\n后端 API: GET /projects?page=1&page_size=20\n    ↓\n数据库查询: SELECT ... LIMIT 20 OFFSET 0 + COUNT(*)\n    ↓\n返回 { items: [...], total: 45, page: 1, page_size: 20 }\n    ↓\n前端更新 items、total，el-pagination 自动渲染\n```\n\n---\n\n## 5. 搜索/筛选行为\n\n- 搜索框/筛选器触发时：**重置 page = 1**，重新请求\n- 后端需支持同时传筛选参数 + 分页参数\n\n---\n\n## 6. 测试要点\n\n- 验证分页 total 正确\n- 验证翻页后数据正确加载\n- 验证切换 page_size 后 total 不变\n- 验证筛选 + 翻页组合正确\n- 验证空结果页面展示\n\n---\n\n## 7. 文件清单\n\n| 文件 | 操作 |\n|------|------|\n| `backend/app/schemas/schemas.py` | 新增 `PaginatedResponse` |\n| `backend/app/api/projects.py` | 改造 `list_projects` |\n| `backend/app/api/iterations.py` | 改造 `list_iterations` |\n| `backend/app/api/requirements.py` | 已有 page/size 参数但未用，需启用 |\n| `frontend/src/composables/usePagination.ts` | 新增 |\n| `frontend/src/views/Projects.vue` | 改造 |\n| `frontend/src/views/Iterations.vue` | 改造 |\n| `frontend/src/views/Requirements.vue` | 改造 |\n','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-20 16:18:42.600276','2026-06-20 16:18:42.600280',NULL);
INSERT INTO documents VALUES('21b092f4-b8c4-487c-a9d0-3cc9975cf5d3','781e30b7-b8c7-4764-943b-921960cf19c3',NULL,'列表分页展示 — 实现计划','ANALYSIS',replace('# 列表分页展示 — 实现计划\n\n**Goal:** 为项目管理、迭代管理、需求管理三个列表页面添加后端分页支持，响应格式统一为 `{ items: [], total, page, page_size }`\n\n**Architecture:** 后端新增 `PaginatedResponse` 泛型结构，改写 `list_projects`、`list_iterations`、`list_requirements` 三个接口支持分页参数。前端封装 `usePagination` composable，改造三个列表页添加 `el-pagination` 组件。\n\n**Tech Stack:** Python (FastAPI + SQLAlchemy), Vue 3 + Element Plus, TypeScript\n\n---\n\n## Global Constraints\n\n- 分页默认值: `page=1`, `page_size=20`\n- 响应格式: `{ items: List, total: int, page: int, page_size: int }`\n- 前端使用 Element Plus `el-pagination` 组件\n- 设计文档路径: `docs/cs/codeseer/sprint-1/项目管理迭代管理需求管理列表分页展示/specs/`\n\n---\n\n## Task 1: 后端 — 新增 PaginatedResponse 泛型结构\n\n**Files:**\n- Modify: `backend/app/schemas/schemas.py`\n\n**Interfaces:**\n- Produces: `PaginatedResponse[T]` — 泛型分页响应模型\n\n## Task 2: 后端 — 改造 list_projects 接口\n\n**Files:**\n- Modify: `backend/app/api/projects.py`\n\n**Interfaces:**\n- Consumes: `PaginatedResponse[ProjectResponse]`\n- Produces: `GET /projects?page=1&page_size=20`\n\n## Task 3: 后端 — 改造 list_iterations 接口\n\n**Files:**\n- Modify: `backend/app/api/iterations.py`\n\n**Interfaces:**\n- Consumes: `PaginatedResponse[IterationResponse]`\n- Produces: `GET /iterations?page=1&page_size=20`\n\n## Task 4: 后端 — 改造 list_requirements 接口\n\n**Files:**\n- Modify: `backend/app/api/requirements.py`\n\n**Interfaces:**\n- Consumes: `PaginatedResponse[RequirementResponse]`\n- Produces: `GET /requirements?page=1&page_size=20`\n\n## Task 5: 前端 — 新增 usePagination Composable\n\n**Files:**\n- Create: `frontend/src/composables/usePagination.ts`\n\n**Interfaces:**\n- Produces: `usePagination<T>(fetcher)` — 返回 `{ items, total, page, pageSize, loading, fetchPage, onPageChange, onSizeChange }`\n\n## Task 6: 前端 — 改造 Projects.vue\n\n**Files:**\n- Modify: `frontend/src/views/Projects.vue`\n\n**Interfaces:**\n- Consumes: `usePagination`, `projectsApi`\n- Produces: 分页后的项目列表\n\n## Task 7: 前端 — 改造 Iterations.vue\n\n**Files:**\n- Modify: `frontend/src/views/Iterations.vue`\n\n## Task 8: 前端 — 改造 Requirements.vue\n\n**Files:**\n- Modify: `frontend/src/views/Requirements.vue`\n\n## Task 9: 前端 — 同步 API 层适配\n\n**Files:**\n- Modify: `frontend/src/api/index.ts`\n\n**Interfaces:**\n- Consumes: `PaginatedResponse` 格式\n- Produces: API 调用适配器\n','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-20 16:18:52.673076','2026-06-20 16:18:52.673080',NULL);
INSERT INTO documents VALUES('d48b03e1-d1cb-4e23-89e8-0caadf852f5e',NULL,'9bcf8fc9-1480-4e1d-8f5b-9300acc577b1','ai-agent-integration','ANALYSIS',replace('# AI Agent 集成\n\n## 背景\n\nCodeSeer 平台通过 MCP（Model Context Protocol）协议与 AI 编码工具（Claude Code、OpenCode 等）建立双向通信。AI Agent 作为开发者的代理，能够感知平台上的需求上下文、自主推进开发流程，并将执行结果同步回平台。\n\n## 用户故事\n\n作为开发者，我希望 AI 编码工具能直接从平台拉取需求、同步任务进度、上传文档，以便无需在平台和 IDE 之间手动切换，AI 完整代理整个开发流程。\n\n## 架构概述\n\n```\nAI 编码工具（Claude Code / OpenCode）\n        │\n        │  MCP HTTP Transport (JSON-RPC 2.0)\n        ▼\nCodeSeer MCP Server（/api/mcp/...）\n        │\n        │  SQLAlchemy Async\n        ▼\nCodeSeer 业务数据库（SQLite）\n```\n\nMCP Server 以独立路由挂载在 FastAPI 主应用下，通过 Bearer Token 鉴权，每个 AI 工具实例对应一个开发者身份。\n\n## MCP 工具清单\n\n### 需求相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `get_my_requirements` | 拉取指派给当前开发者的待开发需求列表 |\n| `get_requirement` | 获取单条需求的完整详情（描述、验收标准、现有任务） |\n| `update_requirement_status` | 触发需求状态流转（如 `assigned → in_progress`） |\n\n### 任务相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `sync_tasks` | 按标题 upsert 任务列表；不删除平台已有任务 |\n\n`sync_tasks` 支持字段：\n- `title`：任务标题（匹配键）\n- `description`：任务描述\n- `status`：`pending` / `in_progress` / `completed` / `blocked`\n- `estimated_hours`：预估工时\n- `actual_hours`：实际工时\n\n### 测试相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `submit_test_record` | 上传单元测试执行结果 |\n\n### 文档相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `create_document` | 上传设计文档（Markdown），关联到指定需求 |\n\n### 环境配置\n\n| 工具名 | 说明 |\n|--------|------|\n| `setup_dev_environment` | 安装 superpowers 技能包及 CodeSeer 专属 Skill 到本地 AI 工具 |\n\n## 状态流转\n\n简化后的需求状态机：\n\n```\n草稿(draft)\n  └─ 已指派(assigned)      ← 平台 PM 操作\n       └─ 开发中(in_progress)   ← AI 开始开发时调用\n            └─ 待评审(pending_review)  ← AI 提交评审时调用\n                 ├─ 评审通过(review_approved)\n                 │    └─ 已完成(completed)\n                 └─ 评审驳回(review_rejected)\n                      └─ 开发中(in_progress)  ← 重新开发\n```\n\nAI Agent 典型调用顺序：\n1. `get_my_requirements` → 选择需求\n2. `get_requirement` → 读取详情\n3. `update_requirement_status(action="in_progress")` → 标记开始\n4. `sync_tasks(tasks=[...])` → 同步任务拆解\n5. 开发执行...\n6. `submit_test_record(...)` → 上传测试结果\n7. `create_document(...)` → 上传设计文档\n8. `sync_tasks(tasks=[{status: "completed", actual_hours: N}, ...])` → 终态同步\n9. `update_requirement_status(action="pending_review")` → 提交评审\n\n## 鉴权\n\nMCP Token 通过平台"MCP 配置"页面生成，格式为 Bearer JWT。AI 工具在 `.opencode.json` 或 MCP 配置文件中配置：\n\n```json\n{\n  "mcpServers": {\n    "codeseer": {\n      "type": "http",\n      "url": "http://localhost:8000/mcp",\n      "headers": {\n        "Authorization": "Bearer <TOKEN>"\n      }\n    }\n  }\n}\n```\n\n## Skill 安装\n\n通过 `setup_dev_environment` 工具，AI 会将以下内容安装到项目根目录：\n\n- `superpowers/` — Superpowers 技能包（TDD、代码审查等）\n- `skills/cs_integration/` — CodeSeer 专属 Skill（cs_setup、cs_start 命令）\n\n安装路径使用 `git rev-parse --show-toplevel` 确定项目根目录，**不安装到全局 `~/.opencode/`**。\n\n## 关键约束\n\n- `sync_tasks` 按 `title` 匹配做 upsert，不删除平台已有任务\n- `status` 更新时自动维护 `started_at` / `completed_at` 时间戳\n- 文档上传后为草稿状态，需在平台手动"挂载模块"并"归档"才能纳入模块知识库\n- MCP Token 与用户身份绑定，`get_my_requirements` 只返回该用户被指派的需求\n','\n',char(10)),replace('# AI Agent 集成\n\n## 背景\n\nCodeSeer 平台通过 MCP（Model Context Protocol）协议与 AI 编码工具（Claude Code、OpenCode 等）建立双向通信。AI Agent 作为开发者的代理，能够感知平台上的需求上下文、自主推进开发流程，并将执行结果同步回平台。\n\n## 用户故事\n\n作为开发者，我希望 AI 编码工具能直接从平台拉取需求、同步任...','\n',char(10)),replace('`title`：任务标题（匹配键）\n`description`：任务描述\n`status`：`pending` / `in_progress` / `completed` / `blocked`\n`estimated_hours`：预估工时\n`actual_hours`：实际工时\n`get_my_requirements` → 选择需求\n`get_requirement` → 读取详情\n`update_requirement_status(action="in_progress")` → 标记开始\n`sync_tasks(tasks=[...])` → 同步任务拆解\n开发执行...','\n',char(10)),'ARCHIVED','COMPLETED',1,NULL,'2026-06-21 11:34:09.680440','2026-06-21 11:37:54.647856','2026-06-21 11:34:17.970515');
INSERT INTO documents VALUES('a57119f0-e9bc-40a7-9f79-93cb5605a342','6540e152-1b65-4360-a68e-1270023cf759',NULL,'设计文档：创建需求支持上传附件','DESIGN',replace('# 设计文档：创建需求支持上传附件\n\n## 1. 背景\n\n作为产品经理，在创建需求时需要上传附件（如需求文档、截图等），以便 AIAgent 能获取更丰富的信息来理解需求。\n\nAIAgent 在拉取开发需求时，需要同时获取需求及对应的附件，以便更好地理解需求内容。\n\n## 2. 架构设计\n\n### 2.1 技术选型\n\n- **存储后端**：本地文件系统（`/tmp/codeforge/attachments/`）\n- **数据库**：SQLite（现有）\n- **文件大小限制**：100MB\n\n### 2.2 数据库模型\n\n新建 `RequirementAttachment` 表：\n\n| 字段 | 类型 | 说明 |\n|------|------|------|\n| id | String(36) | 主键 UUID |\n| requirement_id | String(36) | 外键关联 Requirement |\n| filename | String(255) | 原始文件名 |\n| file_size | Integer | 文件大小（字节） |\n| content_type | String(100) | MIME 类型 |\n| storage_path | String(500) | 存储路径 |\n| storage_backend | String(20) | 存储后端：local |\n| created_at | DateTime | 上传时间 |\n\n## 3. API 设计\n\n### 3.1 上传附件\n\n```\nPOST /requirements/{requirement_id}/attachments\nContent-Type: multipart/form-data\n\nBody:\n  - file: 二进制文件\n\nResponse 201:\n{\n  "id": "uuid",\n  "filename": "需求文档.pdf",\n  "file_size": 102400,\n  "content_type": "application/pdf"\n}\n```\n\n### 3.2 列出附件\n\n```\nGET /requirements/{requirement_id}/attachments\n\nResponse 200:\n{\n  "items": [\n    {\n      "id": "uuid",\n      "filename": "需求文档.pdf",\n      "file_size": 102400,\n      "content_type": "application/pdf",\n      "created_at": "2026-06-21T10:00:00Z"\n    }\n  ]\n}\n```\n\n### 3.3 下载附件\n\n```\nGET /requirements/{requirement_id}/attachments/{attachment_id}/download\n\nResponse 200:\n  Content-Type: application/pdf\n  Content-Disposition: attachment; filename="需求文档.pdf"\n  [二进制文件内容]\n```\n\n### 3.4 删除附件\n\n```\nDELETE /requirements/{requirement_id}/attachments/{attachment_id}\n\nResponse 200:\n{\n  "message": "附件已删除"\n}\n```\n\n## 4. AIAgent 集成\n\n### 4.1 扩展 `get_requirement` 响应\n\n在现有 `get_requirement` 响应中增加 `attachments` 字段：\n\n```json\n{\n  "id": "xxx",\n  "title": "需求标题",\n  "description": "...",\n  "attachments": [\n    {\n      "id": "aid",\n      "filename": "需求文档.pdf",\n      "file_size": 102400,\n      "content_type": "application/pdf"\n    }\n  ]\n}\n```\n\n### 4.2 新增 `download_attachment` MCP 工具\n\n```\n工具名：download_attachment\n输入：requirement_id, attachment_id\n输出：二进制文件内容（base64 编码）\n```\n\n### 4.3 AIAgent 调用流程\n\n1. AIAgent 调用 `get_requirement` → 获取附件列表\n2. AIAgent 调用 `download_attachment(requirement_id, attachment_id)` → 获取附件内容\n3. AIAgent 基于附件内容更好地理解需求\n\n## 5. 前端设计\n\n### 5.1 创建需求页面\n\n- 文件选择器（支持多选）\n- 上传进度条\n- 已上传附件列表（可预览/删除）\n- 附件与需求一并提交\n\n## 6. 存储路径\n\n```\n/tmp/codeforge/attachments/{requirement_id}/{uuid}_{original_filename}\n```\n\n## 7. 约束\n\n- 单个文件大小限制：100MB\n- 支持的文件类型：任意（不限制 MIME 类型）\n- 存储后端：local（后续可扩展 OSS/FTP）','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-21 13:18:34.301258','2026-06-21 13:18:34.301261',NULL);
INSERT INTO documents VALUES('668d4d65-2dbe-4428-b3b3-aed28fa2c58e','6540e152-1b65-4360-a68e-1270023cf759',NULL,'实现计划：创建需求支持上传附件','ANALYSIS',replace('# 创建需求支持上传附件 - Implementation Plan\n\n**Goal:** 在创建需求时支持上传附件，AIAgent 能获取附件内容\n\n**Architecture:** 附件存储在本地文件系统 `/tmp/codeforge/attachments/`，元数据存 SQLite 独立表 `requirement_attachments`。MCP 工具扩展 `get_requirement` 返回附件列表，新增 `download_attachment` 工具获取附件内容。\n\n**Tech Stack:** FastAPI (Python), SQLAlchemy, Vue 3 + Element Plus, SQLite\n\n## Global Constraints\n\n- 文件大小限制：100MB\n- 存储路径：`/tmp/codeforge/attachments/{requirement_id}/{uuid}_{filename}`\n- AIAgent 集成：扩展现有 `get_requirement` + 新增 `download_attachment` MCP 工具\n\n---\n\n## Task 1: 创建 RequirementAttachment 模型\n\n**Files:**\n- Modify: `backend/app/models/models.py` — 添加 `RequirementAttachment` model\n\n**TDD 步骤:**\n- RED: 写测试确认模型不存在\n- GREEN: 添加模型类\n- REFACTOR: 无需重构\n\n---\n\n## Task 2: 实现附件 API 端点\n\n**Files:**\n- Create: `backend/app/api/attachments.py`\n- Modify: `backend/app/main.py`\n\n**API Endpoints:**\n- `POST /requirements/{id}/attachments` — 上传\n- `GET /requirements/{id}/attachments` — 列表\n- `GET /requirements/{id}/attachments/{aid}/download` — 下载\n- `DELETE /requirements/{id}/attachments/{aid}` — 删除\n\n**TDD 步骤:**\n- RED: 写测试端点不存在\n- GREEN: 实现完整 API\n- REFACTOR: 无需重构\n\n---\n\n## Task 3: 前端附件 API 客户端\n\n**Files:**\n- Modify: `frontend/src/api/index.ts`\n\n**TDD 步骤:**\n- RED: 写测试 `attachmentsApi` 方法不存在\n- GREEN: 实现 `attachmentsApi` 对象\n- REFACTOR: 无需重构\n\n---\n\n## Task 4: 扩展 AIAgent MCP 工具 — get_requirement 返回附件\n\n**Files:**\n- Modify: `backend/app/api/mcp_handlers.py`\n\n**TDD 步骤:**\n- RED: 写测试确认 `get_requirement_detail` 不返回 attachments\n- GREEN: 扩展函数查询并返回 attachments\n- REFACTOR: 无需重构\n\n---\n\n## Task 5: 新增 download_attachment MCP 工具\n\n**Files:**\n- Modify: `backend/app/api/mcp_tools.py`\n- Modify: `backend/app/api/mcp_handlers.py`\n\n**TDD 步骤:**\n- RED: 写测试确认 `download_attachment` 工具不存在\n- GREEN: 添加工具定义和处理器\n- REFACTOR: 无需重构\n\n---\n\n## Task 6: 前端 — 创建需求页面添加附件上传\n\n**Files:**\n- Modify: `frontend/src/views/Requirements.vue`\n\n**UI Elements:**\n- `el-upload` 组件（第 2 步向导）\n- 已上传文件列表\n- 提交时一并上传附件\n\n**TDD 步骤:**\n- RED: 写测试确认无上传 UI\n- GREEN: 添加文件上传组件和方法\n- REFACTOR: 无需重构\n\n---\n\n## Task 7: 前端 — 需求详情页显示附件\n\n**Files:**\n- Modify: `frontend/src/views/RequirementDetail.vue`\n\n**UI Elements:**\n- "附件" tab 页\n- 附件列表展示\n- 下载按钮\n\n**TDD 步骤:**\n- RED: 写测试确认无附件 tab\n- GREEN: 添加附件 tab 和下载功能\n- REFACTOR: 无需重构\n\n---\n\n## Task 8: 集成测试\n\n**Files:**\n- Create: `backend/tests/test_attachments_integration.py`\n\n**TDD 步骤:**\n- RED: 写测试\n- GREEN: 确保所有端点工作\n- REFACTOR: 无需重构\n\n---\n\n## 实施顺序\n\n1. Task 1 — RequirementAttachment 模型\n2. Task 2 — Attachment API 端点\n3. Task 3 — Frontend API client\n4. Task 4 — MCP get_requirement 扩展\n5. Task 5 — MCP download_attachment\n6. Task 6 — 创建需求页面上传 UI\n7. Task 7 — 需求详情展示附件\n8. Task 8 — 集成测试','\n',char(10)),NULL,NULL,'DRAFT','PENDING',1,'6fd46a29-5870-4573-9fee-62904b96a995','2026-06-21 13:18:46.733841','2026-06-21 13:18:46.733848',NULL);
CREATE TABLE requirement_phases (
	id VARCHAR(36) NOT NULL, 
	requirement_id VARCHAR(36) NOT NULL, 
	phase VARCHAR(13) NOT NULL, 
	status VARCHAR(11), 
	notes TEXT, 
	started_at DATETIME, 
	completed_at DATETIME, 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id)
);
INSERT INTO requirement_phases VALUES('3333c396-4edb-4e80-be7e-27b2af544395','e2b240b8-f319-46ea-8e83-1f2c0ce40329','CLARIFICATION','PENDING',NULL,NULL,NULL,'2026-06-14 11:32:59.386785','2026-06-14 11:32:59.386788');
INSERT INTO requirement_phases VALUES('c172cbd5-addc-4402-815e-b5431e72bfd5','e2b240b8-f319-46ea-8e83-1f2c0ce40329','PLANNING','PENDING',NULL,NULL,NULL,'2026-06-14 11:32:59.386794','2026-06-14 11:32:59.386795');
INSERT INTO requirement_phases VALUES('ef08b8db-d216-4d18-89f1-9dd3a46dfa79','e2b240b8-f319-46ea-8e83-1f2c0ce40329','EXECUTION','PENDING',NULL,NULL,NULL,'2026-06-14 11:32:59.386799','2026-06-14 11:32:59.386800');
INSERT INTO requirement_phases VALUES('7e09fd30-dc6d-4bea-b0de-1053136d145b','e2b240b8-f319-46ea-8e83-1f2c0ce40329','REVIEW','PENDING',NULL,NULL,NULL,'2026-06-14 11:32:59.386804','2026-06-14 11:32:59.386805');
INSERT INTO requirement_phases VALUES('0902a5a2-d990-4603-a593-6826846853f9','e2b240b8-f319-46ea-8e83-1f2c0ce40329','TESTING','PENDING',NULL,NULL,NULL,'2026-06-14 11:32:59.386809','2026-06-14 11:32:59.386809');
INSERT INTO requirement_phases VALUES('2d3414e0-f598-48d9-83e6-88fd3f21cbb0','387f63c2-72db-40b0-8d76-d589162befe2','CLARIFICATION','PENDING',NULL,NULL,NULL,'2026-06-14 11:33:09.063100','2026-06-14 11:33:09.063104');
INSERT INTO requirement_phases VALUES('13343e8e-31fb-495d-8ff1-5a6b9eaceee9','387f63c2-72db-40b0-8d76-d589162befe2','PLANNING','PENDING',NULL,NULL,NULL,'2026-06-14 11:33:09.063111','2026-06-14 11:33:09.063112');
INSERT INTO requirement_phases VALUES('d1f1f891-fc25-476c-9c1b-7425d6b3869e','387f63c2-72db-40b0-8d76-d589162befe2','EXECUTION','PENDING',NULL,NULL,NULL,'2026-06-14 11:33:09.063117','2026-06-14 11:33:09.063118');
INSERT INTO requirement_phases VALUES('95fa9a40-4b63-45c0-9f95-d9e865d13105','387f63c2-72db-40b0-8d76-d589162befe2','REVIEW','PENDING',NULL,NULL,NULL,'2026-06-14 11:33:09.063123','2026-06-14 11:33:09.063124');
INSERT INTO requirement_phases VALUES('9ab03722-4b18-4685-9aaf-308aecb75e9e','387f63c2-72db-40b0-8d76-d589162befe2','TESTING','PENDING',NULL,NULL,NULL,'2026-06-14 11:33:09.063130','2026-06-14 11:33:09.063131');
INSERT INTO requirement_phases VALUES('065cf841-3777-4fb5-b0ef-e08d9498a970','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','CLARIFICATION','PENDING',NULL,NULL,NULL,'2026-06-14 11:34:07.458916','2026-06-14 11:34:07.458921');
INSERT INTO requirement_phases VALUES('0c11a356-30ab-4ade-b202-bed987e6f867','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','PLANNING','PENDING',NULL,NULL,NULL,'2026-06-14 11:34:07.458931','2026-06-14 11:34:07.458932');
INSERT INTO requirement_phases VALUES('aa125f49-d051-43bb-8f57-9dbc859cb7b4','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','EXECUTION','PENDING',NULL,NULL,NULL,'2026-06-14 11:34:07.458941','2026-06-14 11:34:07.458942');
INSERT INTO requirement_phases VALUES('e7c853bc-815e-4109-8586-322bb83a91f8','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','REVIEW','PENDING',NULL,NULL,NULL,'2026-06-14 11:34:07.458950','2026-06-14 11:34:07.458951');
INSERT INTO requirement_phases VALUES('fc6631bb-f922-48c0-93b9-8b9fddf9af14','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','TESTING','PENDING',NULL,NULL,NULL,'2026-06-14 11:34:07.458959','2026-06-14 11:34:07.458960');
INSERT INTO requirement_phases VALUES('b127ad92-4b21-4947-b13b-cef6a747d0a1','5ec8b277-30fe-400a-b800-95a01a5ac42b','CLARIFICATION','PENDING',NULL,NULL,NULL,'2026-06-19 01:20:25.877981','2026-06-19 01:20:25.877983');
INSERT INTO requirement_phases VALUES('df4f1d30-ace0-44bd-ac6f-4e762c1293e7','5ec8b277-30fe-400a-b800-95a01a5ac42b','PLANNING','PENDING',NULL,NULL,NULL,'2026-06-19 01:20:25.877991','2026-06-19 01:20:25.877992');
INSERT INTO requirement_phases VALUES('7ccdd5e1-10a6-430e-8826-0f28c2d1fff4','5ec8b277-30fe-400a-b800-95a01a5ac42b','EXECUTION','PENDING',NULL,NULL,NULL,'2026-06-19 01:20:25.877997','2026-06-19 01:20:25.877998');
INSERT INTO requirement_phases VALUES('52139953-2f28-43be-8570-2274ba205f18','5ec8b277-30fe-400a-b800-95a01a5ac42b','REVIEW','PENDING',NULL,NULL,NULL,'2026-06-19 01:20:25.878003','2026-06-19 01:20:25.878003');
INSERT INTO requirement_phases VALUES('a2435930-3828-47f6-812b-c29d34416757','5ec8b277-30fe-400a-b800-95a01a5ac42b','TESTING','PENDING',NULL,NULL,NULL,'2026-06-19 01:20:25.878008','2026-06-19 01:20:25.878008');
INSERT INTO requirement_phases VALUES('5b780ab5-0fe4-4a03-a9dc-75f651f14474','8d010d0b-0816-4b26-8d02-1fbfda75d753','CLARIFICATION','COMPLETED',NULL,'2026-06-20 04:24:12.044189','2026-06-20 12:08:24.315916','2026-06-19 13:29:32.875150','2026-06-20 12:08:24.318404');
INSERT INTO requirement_phases VALUES('08269136-9ece-4677-a0c4-a0f677f1e708','8d010d0b-0816-4b26-8d02-1fbfda75d753','PLANNING','COMPLETED',NULL,'2026-06-20 04:24:10.124148','2026-06-20 04:24:13.528395','2026-06-19 13:29:32.875160','2026-06-20 04:24:13.530416');
INSERT INTO requirement_phases VALUES('3ea42cc9-4f78-4627-bf08-c69c6eafa1e1','8d010d0b-0816-4b26-8d02-1fbfda75d753','EXECUTION','COMPLETED',NULL,'2026-06-20 03:12:35.244650','2026-06-20 11:45:29.680568','2026-06-19 13:29:32.875166','2026-06-20 11:45:29.683395');
INSERT INTO requirement_phases VALUES('c25ea2e9-6804-45d1-9a03-b27363d5a420','8d010d0b-0816-4b26-8d02-1fbfda75d753','REVIEW','COMPLETED',NULL,'2026-06-20 04:24:16.157432','2026-06-20 12:08:22.668114','2026-06-19 13:29:32.875172','2026-06-20 12:08:22.672347');
INSERT INTO requirement_phases VALUES('527be0e8-5372-4a09-8ff3-d608425a8643','8d010d0b-0816-4b26-8d02-1fbfda75d753','TESTING','COMPLETED',NULL,'2026-06-20 11:45:31.441614','2026-06-20 11:45:32.277687','2026-06-19 13:29:32.875177','2026-06-20 11:45:32.280108');
INSERT INTO requirement_phases VALUES('c9e41769-1423-44ef-b032-44628c783c3e','781e30b7-b8c7-4764-943b-921960cf19c3','CLARIFICATION','COMPLETED',NULL,'2026-06-20 16:14:29.024710','2026-06-20 16:18:42.602647','2026-06-20 11:48:52.656816','2026-06-20 16:18:42.603158');
INSERT INTO requirement_phases VALUES('01ad9ebb-80e0-4cd0-b66c-15f9953f0764','781e30b7-b8c7-4764-943b-921960cf19c3','PLANNING','COMPLETED',NULL,'2026-06-20 16:18:52.674811','2026-06-20 16:19:03.447321','2026-06-20 11:48:52.656835','2026-06-20 16:19:03.447563');
INSERT INTO requirement_phases VALUES('ca1d8673-21f5-4b73-a3a9-9569a9014cb4','781e30b7-b8c7-4764-943b-921960cf19c3','EXECUTION','COMPLETED',NULL,'2026-06-20 16:19:08.186411','2026-06-20 16:47:30.678609','2026-06-20 11:48:52.656847','2026-06-20 16:47:30.678834');
INSERT INTO requirement_phases VALUES('5caba6b5-6eeb-4424-a3ca-9b6dc6c1a1c1','781e30b7-b8c7-4764-943b-921960cf19c3','REVIEW','COMPLETED',NULL,'2026-06-21 01:20:24.697893','2026-06-21 01:20:25.759611','2026-06-20 11:48:52.656859','2026-06-21 01:20:25.763005');
INSERT INTO requirement_phases VALUES('a2b04553-4b03-4f1c-b316-d8eb8e2721cb','781e30b7-b8c7-4764-943b-921960cf19c3','TESTING','COMPLETED',NULL,'2026-06-20 16:21:34.954588','2026-06-20 16:47:26.716373','2026-06-20 11:48:52.656871','2026-06-20 16:47:26.716625');
INSERT INTO requirement_phases VALUES('5733c11b-9bc7-4d8a-9410-4c16857c82d0','6540e152-1b65-4360-a68e-1270023cf759','CLARIFICATION','COMPLETED',NULL,'2026-06-21 13:01:36.595809','2026-06-21 13:18:34.303702','2026-06-21 12:58:42.352450','2026-06-21 13:18:34.304183');
INSERT INTO requirement_phases VALUES('9b7afcfc-af6c-49ef-a786-04b8cb606527','6540e152-1b65-4360-a68e-1270023cf759','PLANNING','PENDING',NULL,'2026-06-21 13:18:46.736254','2026-06-21 13:18:53.853305','2026-06-21 12:58:42.352465','2026-06-21 14:26:45.799738');
INSERT INTO requirement_phases VALUES('592824ba-ffc6-4ac7-a8d1-b02ca18850a3','6540e152-1b65-4360-a68e-1270023cf759','EXECUTION','COMPLETED',NULL,'2026-06-21 13:19:01.633202','2026-06-21 14:24:26.587420','2026-06-21 12:58:42.352473','2026-06-21 14:24:26.587921');
INSERT INTO requirement_phases VALUES('5ac1f978-3989-461f-9aaa-5eb8e2984ba7','6540e152-1b65-4360-a68e-1270023cf759','TESTING','IN_PROGRESS',NULL,'2026-06-21 13:21:41.430409',NULL,'2026-06-21 12:58:42.352481','2026-06-21 13:21:41.430822');
INSERT INTO requirement_phases VALUES('8a3c9fc8-0889-4e88-9434-212ebcbc0053','6540e152-1b65-4360-a68e-1270023cf759','REVIEW','PENDING',NULL,NULL,NULL,'2026-06-21 12:58:42.352488','2026-06-21 12:58:42.352489');
CREATE TABLE requirement_history (
	id VARCHAR(36) NOT NULL, 
	requirement_id VARCHAR(36) NOT NULL, 
	action VARCHAR(18) NOT NULL, 
	field_name VARCHAR(100), 
	old_value TEXT, 
	new_value TEXT, 
	actor VARCHAR(100), 
	comment TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id)
);
INSERT INTO requirement_history VALUES('bd8a7861-3563-4e52-a619-b5fae0edf31a','e42d3e17-4ae2-4a45-9a6f-db78fcaeae71','CREATED','title',NULL,'用户登录功能',NULL,NULL,'2026-06-14 11:32:21.802983');
INSERT INTO requirement_history VALUES('3d7c0cdb-d9cd-4aee-a88e-23807463e606','e2b240b8-f319-46ea-8e83-1f2c0ce40329','CREATED','title',NULL,'订单创建功能',NULL,NULL,'2026-06-14 11:32:30.479631');
INSERT INTO requirement_history VALUES('68e178a9-d39c-4660-8fac-866539774971','387f63c2-72db-40b0-8d76-d589162befe2','CREATED','title',NULL,'用户头像上传',NULL,NULL,'2026-06-14 11:32:30.496669');
INSERT INTO requirement_history VALUES('7dc52fdf-794e-48ce-ace3-3b39bb345346','387f63c2-72db-40b0-8d76-d589162befe2','STATUS_CHANGED','status','draft','pending_analysis',NULL,NULL,'2026-06-18 04:25:33.494526');
INSERT INTO requirement_history VALUES('2dfd6227-7f20-4447-b414-1fd540a03532','5d1422c4-832d-4705-ae36-d1261f4c1121','CREATED','title',NULL,'测试需求',NULL,NULL,'2026-06-19 00:48:26.179002');
INSERT INTO requirement_history VALUES('49e7a72e-8aaf-471a-8612-e3d0a4e1f6af','5411b43d-d06d-4089-8a9b-c5bd03d2f531','CREATED','title',NULL,'测试需求',NULL,NULL,'2026-06-19 00:48:52.021175');
INSERT INTO requirement_history VALUES('2a7a1422-802d-4e3d-a544-2b672490f0ea','5ec8b277-30fe-400a-b800-95a01a5ac42b','CREATED','title',NULL,'测试需求',NULL,NULL,'2026-06-19 00:48:57.899065');
INSERT INTO requirement_history VALUES('f0f14446-a2e5-4125-a782-5ea69aa5e890','8d010d0b-0816-4b26-8d02-1fbfda75d753','CREATED','title',NULL,'重构整个项目的基础页面风格',NULL,NULL,'2026-06-19 13:28:28.408162');
INSERT INTO requirement_history VALUES('b17b4fcb-802d-4172-893b-08cc3e5c435e','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','draft','pending_analysis',NULL,NULL,'2026-06-19 13:35:59.484423');
INSERT INTO requirement_history VALUES('2dcc28b1-376d-484b-8645-2d977827b92e','8d010d0b-0816-4b26-8d02-1fbfda75d753','ASSIGNED','assignee_id',NULL,'6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,'2026-06-19 14:04:32.533104');
INSERT INTO requirement_history VALUES('9c3d8764-386c-448d-affa-8fd05cb7afbf','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','claimed','in_progress',NULL,NULL,'2026-06-19 14:56:51.450189');
INSERT INTO requirement_history VALUES('882a68d0-7974-4386-ac4d-6b389eb6ea82','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','in_progress','pending_review',NULL,NULL,'2026-06-19 14:57:14.481879');
INSERT INTO requirement_history VALUES('4ae7d26f-fe8b-4a81-8d08-e2a008980aff','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','pending_review','review_rejected',NULL,NULL,'2026-06-19 14:57:17.697980');
INSERT INTO requirement_history VALUES('7eac6531-9a1e-4a5a-ac11-6b92a6183100','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','review_rejected','in_progress',NULL,NULL,'2026-06-19 14:57:19.317849');
INSERT INTO requirement_history VALUES('cd9d37bf-19e8-4334-b933-72a4e547412a','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.planning','completed','pending',NULL,NULL,'2026-06-20 04:24:06.467595');
INSERT INTO requirement_history VALUES('ae37904d-0cf1-4f91-89ca-60e6dd47ef09','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.execution','in_progress','completed',NULL,NULL,'2026-06-20 04:24:08.124592');
INSERT INTO requirement_history VALUES('034ecadf-2317-4a45-b4b3-adc6fdeeb05e','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.planning','pending','in_progress',NULL,NULL,'2026-06-20 04:24:10.124621');
INSERT INTO requirement_history VALUES('8223d4d8-f140-47c3-ae3d-86206569ec76','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.clarification','pending','in_progress',NULL,NULL,'2026-06-20 04:24:12.045018');
INSERT INTO requirement_history VALUES('3f329a3b-22e2-4c79-8ce3-1c30787e6764','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.planning','in_progress','completed',NULL,NULL,'2026-06-20 04:24:13.529041');
INSERT INTO requirement_history VALUES('cf9fe0b4-7985-453a-bfb5-6dce1c094a63','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.execution','completed','pending',NULL,NULL,'2026-06-20 04:24:14.793580');
INSERT INTO requirement_history VALUES('9c228f79-da14-45da-b45e-a40be1b9f142','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.review','pending','in_progress',NULL,NULL,'2026-06-20 04:24:16.157928');
INSERT INTO requirement_history VALUES('7c2a3fd3-e828-4f82-8468-44ef2e72def8','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.execution','pending','in_progress',NULL,NULL,'2026-06-20 11:45:23.696198');
INSERT INTO requirement_history VALUES('9c82c120-8628-46d6-b9f5-eba8cfbecb92','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.review','in_progress','completed',NULL,NULL,'2026-06-20 11:45:28.101717');
INSERT INTO requirement_history VALUES('c9011cbf-5c6a-4095-a79c-4b907d3c3354','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.execution','in_progress','completed',NULL,NULL,'2026-06-20 11:45:29.681496');
INSERT INTO requirement_history VALUES('9388800c-ec40-40d2-bd7a-a2d6070f0d84','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.testing','pending','in_progress',NULL,NULL,'2026-06-20 11:45:31.442062');
INSERT INTO requirement_history VALUES('320985a5-669d-4ad2-8562-19f953c5f41e','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.testing','in_progress','completed',NULL,NULL,'2026-06-20 11:45:32.278575');
INSERT INTO requirement_history VALUES('7c636009-c5f7-403c-807a-fe01438e1979','781e30b7-b8c7-4764-943b-921960cf19c3','CREATED','title',NULL,'项目管理、迭代管理、需求管理列表分页展示',NULL,NULL,'2026-06-20 11:48:26.295212');
INSERT INTO requirement_history VALUES('72cb598f-e543-44a1-8d5a-c5d88445cd77','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','pending_review','review_approved',NULL,NULL,'2026-06-20 12:07:34.406757');
INSERT INTO requirement_history VALUES('6c4b8a90-5da6-4628-b72c-c8619745d244','8d010d0b-0816-4b26-8d02-1fbfda75d753','STATUS_CHANGED','status','review_approved','completed',NULL,NULL,'2026-06-20 12:07:35.825154');
INSERT INTO requirement_history VALUES('34b2634d-07f2-491a-8ca8-ac1b620239e2','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.review','in_progress','completed',NULL,NULL,'2026-06-20 12:08:22.668945');
INSERT INTO requirement_history VALUES('cf8d454a-e499-4dc6-b6d4-cbba8015b05e','8d010d0b-0816-4b26-8d02-1fbfda75d753','UPDATED','phase.clarification','in_progress','completed',NULL,NULL,'2026-06-20 12:08:24.316740');
INSERT INTO requirement_history VALUES('aa6fe78a-124c-46f7-bb23-06938d71ee58','781e30b7-b8c7-4764-943b-921960cf19c3','ASSIGNED','assignee_id',NULL,'6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,'2026-06-20 16:09:21.029655');
INSERT INTO requirement_history VALUES('9f5569f5-bf4d-43d0-87f7-579cbfa5fa5f','781e30b7-b8c7-4764-943b-921960cf19c3','UPDATED','phase.review','pending','in_progress',NULL,NULL,'2026-06-21 01:20:24.701599');
INSERT INTO requirement_history VALUES('52728411-ad78-4a00-b7f0-5d143bd7c791','781e30b7-b8c7-4764-943b-921960cf19c3','UPDATED','phase.review','in_progress','completed',NULL,NULL,'2026-06-21 01:20:25.760623');
INSERT INTO requirement_history VALUES('f3a247d8-93e5-4e53-b180-7bfd47caadbb','6540e152-1b65-4360-a68e-1270023cf759','CREATED','title',NULL,'创建需求支持上传附件',NULL,NULL,'2026-06-21 01:23:53.399626');
INSERT INTO requirement_history VALUES('94bf059c-f168-41ef-b767-53733ae2e243','6540e152-1b65-4360-a68e-1270023cf759','ASSIGNED','assignee_id',NULL,'6fd46a29-5870-4573-9fee-62904b96a995',NULL,NULL,'2026-06-21 01:24:34.612771');
INSERT INTO requirement_history VALUES('ce4970c4-2bad-4d45-bdac-253ef7c12ab4','6540e152-1b65-4360-a68e-1270023cf759','UPDATED','phase.planning','completed','pending',NULL,NULL,'2026-06-21 14:26:45.795991');
CREATE TABLE unit_test_records (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);
INSERT INTO unit_test_records VALUES('5426c09a-564e-4e69-aafd-c26fd91f760a','781e30b7-b8c7-4764-943b-921960cf19c3','06eb63eb-2ec3-4aab-b861-464a185a9964','后端 — 新增 PaginatedResponse 泛型结构','unit',2,0,2,replace('test_paginated_response_structure\ntest_paginated_response_with_items','\n',char(10)),NULL,'FAILED','2026-06-20 16:21:34.951154','2026-06-20 16:21:34.951158');
INSERT INTO unit_test_records VALUES('171be9a5-e78f-4fa7-957a-c0c594215892','781e30b7-b8c7-4764-943b-921960cf19c3','06eb63eb-2ec3-4aab-b861-464a185a9964','后端 — 新增 PaginatedResponse 泛型结构','unit',2,2,0,NULL,100,'ALL_PASSED','2026-06-20 16:21:40.029820','2026-06-20 16:21:40.029825');
INSERT INTO unit_test_records VALUES('73cd3dbf-da00-4a31-94d7-5c87674d7148','781e30b7-b8c7-4764-943b-921960cf19c3','06eb63eb-2ec3-4aab-b861-464a185a9964','后端 — 新增 PaginatedResponse 泛型结构','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:21:43.625967','2026-06-20 16:21:43.625972');
INSERT INTO unit_test_records VALUES('bfac6096-cdc0-4c95-9f01-5cec00fbcc50','781e30b7-b8c7-4764-943b-921960cf19c3','a3a5b017-d118-448b-9aea-e273ee08f407','后端 — 改造 list_projects 接口','unit',2,0,2,replace('test_list_projects_pagination\ntest_list_projects_pagination_second_page','\n',char(10)),NULL,'FAILED','2026-06-20 16:30:51.364962','2026-06-20 16:30:51.364965');
INSERT INTO unit_test_records VALUES('4471b9ff-3f5f-4cdf-bfdd-46d3c9eeb56b','781e30b7-b8c7-4764-943b-921960cf19c3','a3a5b017-d118-448b-9aea-e273ee08f407','后端 — 改造 list_projects 接口','unit',2,2,0,NULL,100,'ALL_PASSED','2026-06-20 16:30:55.645146','2026-06-20 16:30:55.645150');
INSERT INTO unit_test_records VALUES('b749a75a-06d3-4a0c-9f50-11d941a1a621','781e30b7-b8c7-4764-943b-921960cf19c3','a3a5b017-d118-448b-9aea-e273ee08f407','后端 — 改造 list_projects 接口','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:30:59.541865','2026-06-20 16:30:59.541869');
INSERT INTO unit_test_records VALUES('ced84818-34fb-4251-958e-31f7ac1cec49','781e30b7-b8c7-4764-943b-921960cf19c3','e72fee35-9cf7-47d5-85c0-55154b2f53ec','后端 — 改造 list_iterations 接口','unit',2,0,2,replace('test_list_iterations_pagination\ntest_list_iterations_pagination_second_page','\n',char(10)),NULL,'FAILED','2026-06-20 16:35:39.364885','2026-06-20 16:35:39.364887');
INSERT INTO unit_test_records VALUES('63cf2eb1-37c5-4929-9900-c6fd9b85e35a','781e30b7-b8c7-4764-943b-921960cf19c3','e72fee35-9cf7-47d5-85c0-55154b2f53ec','后端 — 改造 list_iterations 接口','unit',2,2,0,NULL,100,'ALL_PASSED','2026-06-20 16:35:43.373055','2026-06-20 16:35:43.373058');
INSERT INTO unit_test_records VALUES('369e9caf-8e08-4a7f-b01f-33c8e84bb7d5','781e30b7-b8c7-4764-943b-921960cf19c3','e72fee35-9cf7-47d5-85c0-55154b2f53ec','后端 — 改造 list_iterations 接口','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:35:47.518361','2026-06-20 16:35:47.518366');
INSERT INTO unit_test_records VALUES('f3924152-008e-4857-8262-4e12956c5008','781e30b7-b8c7-4764-943b-921960cf19c3','406ba567-ef3a-4b2c-b880-bda5f130d3be','后端 — 改造 list_requirements 接口','unit',2,0,2,replace('test_list_requirements_pagination\ntest_list_requirements_pagination_second_page','\n',char(10)),NULL,'FAILED','2026-06-20 16:40:30.446129','2026-06-20 16:40:30.446132');
INSERT INTO unit_test_records VALUES('11fef83f-7fec-48b0-8964-0c713c768160','781e30b7-b8c7-4764-943b-921960cf19c3','406ba567-ef3a-4b2c-b880-bda5f130d3be','后端 — 改造 list_requirements 接口','unit',2,2,0,NULL,100,'ALL_PASSED','2026-06-20 16:40:34.890487','2026-06-20 16:40:34.890494');
INSERT INTO unit_test_records VALUES('757d4d63-c4c9-433d-991d-afc88a06be89','781e30b7-b8c7-4764-943b-921960cf19c3','406ba567-ef3a-4b2c-b880-bda5f130d3be','后端 — 改造 list_requirements 接口','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:40:39.007548','2026-06-20 16:40:39.007554');
INSERT INTO unit_test_records VALUES('98848a7b-ba4e-41df-ab6f-5e09e64e5945','781e30b7-b8c7-4764-943b-921960cf19c3','e9447890-0a28-4f66-97db-6345c6d689c1','前端 — 新增 usePagination Composable','unit',2,0,2,replace('should initialize with correct defaults\nshould return required properties','\n',char(10)),NULL,'FAILED','2026-06-20 16:41:17.491561','2026-06-20 16:41:17.491564');
INSERT INTO unit_test_records VALUES('b67b0bb5-95e8-49b3-b2af-472c0e8f0e82','781e30b7-b8c7-4764-943b-921960cf19c3','e9447890-0a28-4f66-97db-6345c6d689c1','前端 — 新增 usePagination Composable','unit',2,2,0,NULL,100,'ALL_PASSED','2026-06-20 16:41:22.015358','2026-06-20 16:41:22.015362');
INSERT INTO unit_test_records VALUES('109db0a2-6c1c-4800-aa62-9fab91c3adba','781e30b7-b8c7-4764-943b-921960cf19c3','e9447890-0a28-4f66-97db-6345c6d689c1','前端 — 新增 usePagination Composable','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:41:26.708294','2026-06-20 16:41:26.708298');
INSERT INTO unit_test_records VALUES('522268d5-8034-49d5-80a7-8869ec402407','781e30b7-b8c7-4764-943b-921960cf19c3','f54b4dc2-4b3b-4cc8-a2e6-8b70cd54424a','前端 — 改造 Projects.vue','unit',1,0,1,'Projects pagination test',NULL,'FAILED','2026-06-20 16:43:11.323994','2026-06-20 16:43:11.323998');
INSERT INTO unit_test_records VALUES('3d027458-6a22-4166-8382-bf2c70c39282','781e30b7-b8c7-4764-943b-921960cf19c3','f54b4dc2-4b3b-4cc8-a2e6-8b70cd54424a','前端 — 改造 Projects.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:43:16.135380','2026-06-20 16:43:16.135385');
INSERT INTO unit_test_records VALUES('956e09f0-ce2d-43c8-94ef-535b64d0f3e7','781e30b7-b8c7-4764-943b-921960cf19c3','f54b4dc2-4b3b-4cc8-a2e6-8b70cd54424a','前端 — 改造 Projects.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:43:20.915717','2026-06-20 16:43:20.915722');
INSERT INTO unit_test_records VALUES('433f9f6a-df59-44d2-9e39-b9d3e90673df','781e30b7-b8c7-4764-943b-921960cf19c3','b3702d5e-6540-4c65-ab2e-fb22744fd4ef','前端 — 改造 Iterations.vue','unit',1,0,1,'Iterations pagination test',NULL,'FAILED','2026-06-20 16:44:42.863155','2026-06-20 16:44:42.863159');
INSERT INTO unit_test_records VALUES('38455956-d56a-4a85-8fed-4dbe36aa5207','781e30b7-b8c7-4764-943b-921960cf19c3','b3702d5e-6540-4c65-ab2e-fb22744fd4ef','前端 — 改造 Iterations.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:44:46.886556','2026-06-20 16:44:46.886561');
INSERT INTO unit_test_records VALUES('9e7710ee-a895-4698-b7c9-dfa2732c8db6','781e30b7-b8c7-4764-943b-921960cf19c3','b3702d5e-6540-4c65-ab2e-fb22744fd4ef','前端 — 改造 Iterations.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:44:50.772792','2026-06-20 16:44:50.772796');
INSERT INTO unit_test_records VALUES('d4d82905-75c4-46bf-b629-4a085b0bec31','781e30b7-b8c7-4764-943b-921960cf19c3','01c4e5b7-e6c0-4f7b-95cb-9021d2e2388e','前端 — 改造 Requirements.vue','unit',1,0,1,'Requirements pagination test',NULL,'FAILED','2026-06-20 16:46:32.820476','2026-06-20 16:46:32.820481');
INSERT INTO unit_test_records VALUES('4e9b9122-4388-477b-8f14-fcda5f54f86f','781e30b7-b8c7-4764-943b-921960cf19c3','01c4e5b7-e6c0-4f7b-95cb-9021d2e2388e','前端 — 改造 Requirements.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:46:38.093688','2026-06-20 16:46:38.093691');
INSERT INTO unit_test_records VALUES('082527a2-e1e8-4de3-886c-7c35aa2903ee','781e30b7-b8c7-4764-943b-921960cf19c3','01c4e5b7-e6c0-4f7b-95cb-9021d2e2388e','前端 — 改造 Requirements.vue','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:46:43.154073','2026-06-20 16:46:43.154080');
INSERT INTO unit_test_records VALUES('23e4fcc0-6b5a-4d1d-b881-b0d8be0da53f','781e30b7-b8c7-4764-943b-921960cf19c3','0d3e7749-5439-4a63-b05f-0f8209d766d3','前端 — 同步 API 层适配','unit',1,0,1,'API pagination smoke test',NULL,'FAILED','2026-06-20 16:47:18.019162','2026-06-20 16:47:18.019167');
INSERT INTO unit_test_records VALUES('f1da1c07-2348-45b3-a5fb-0d5e16a5afc6','781e30b7-b8c7-4764-943b-921960cf19c3','0d3e7749-5439-4a63-b05f-0f8209d766d3','前端 — 同步 API 层适配','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:47:22.346453','2026-06-20 16:47:22.346460');
INSERT INTO unit_test_records VALUES('302ba663-4cb5-4a2b-b15d-4c3f1439c0b7','781e30b7-b8c7-4764-943b-921960cf19c3','0d3e7749-5439-4a63-b05f-0f8209d766d3','前端 — 同步 API 层适配','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-20 16:47:26.714596','2026-06-20 16:47:26.714600');
INSERT INTO unit_test_records VALUES('62cdd68f-9d91-4fd2-9cee-138b8293efbf','6540e152-1b65-4360-a68e-1270023cf759','768928e2-e59c-4fb9-b3dd-aa8ce725df02','Task 1: 创建 RequirementAttachment 模型','unit',2,2,0,NULL,NULL,'ALL_PASSED','2026-06-21 13:21:41.427357','2026-06-21 13:21:41.427360');
INSERT INTO unit_test_records VALUES('a6b942e3-4712-4d4e-b6d5-109d4357b4a5','6540e152-1b65-4360-a68e-1270023cf759','9ba6fc9e-110e-484a-91ee-e7092818a39e','Task 2: 实现附件 API 端点','unit',7,7,0,NULL,NULL,'ALL_PASSED','2026-06-21 13:30:58.517015','2026-06-21 13:30:58.517018');
INSERT INTO unit_test_records VALUES('ce02492d-6622-47c4-b50b-2ab4360dec32','6540e152-1b65-4360-a68e-1270023cf759','540b8c68-4708-4fb2-bf1c-f5179cb8e849','Task 3: 前端附件 API 客户端','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-21 13:31:38.584076','2026-06-21 13:31:38.584082');
INSERT INTO unit_test_records VALUES('7899b553-3a6e-410f-ac9d-17ab901761f5','6540e152-1b65-4360-a68e-1270023cf759','0fd9dcad-cb6f-4ee6-af86-d4db2bccd5c6','Task 4: 扩展 get_requirement 返回附件','unit',3,3,0,NULL,NULL,'ALL_PASSED','2026-06-21 13:35:37.782790','2026-06-21 13:35:37.782793');
INSERT INTO unit_test_records VALUES('44318321-3c7f-4d7a-b119-0ad2c01d2d1c','6540e152-1b65-4360-a68e-1270023cf759','24933a62-0b89-43b8-8ee5-6922c99b660d','Task 5: 新增 download_attachment MCP 工具','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-21 13:41:10.849633','2026-06-21 13:41:10.849636');
INSERT INTO unit_test_records VALUES('e23df30a-c386-4015-a79c-af299b8c3e8d','6540e152-1b65-4360-a68e-1270023cf759','5eb8ac50-4c45-4b3d-92e3-a1acb9199617','Task 6: 创建需求页添加附件上传','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-21 14:18:01.076398','2026-06-21 14:18:01.076402');
INSERT INTO unit_test_records VALUES('f24703a3-35ca-4f6b-acf8-00ea28003de5','6540e152-1b65-4360-a68e-1270023cf759','3c93cbb0-a464-47d7-b30b-59d71bf706b0','Task 7: 需求详情页显示附件','unit',1,1,0,NULL,NULL,'ALL_PASSED','2026-06-21 14:19:10.212512','2026-06-21 14:19:10.212515');
INSERT INTO unit_test_records VALUES('a92fcb59-5e4d-4dc7-90ad-c6de39b95797','6540e152-1b65-4360-a68e-1270023cf759','a814125c-a5b5-43b1-a8c2-7de245d139b3','Task 8: 集成测试','integration',5,5,0,NULL,NULL,'ALL_PASSED','2026-06-21 14:24:12.556092','2026-06-21 14:24:12.556095');
CREATE TABLE document_versions (
	id VARCHAR(36) NOT NULL, 
	document_id VARCHAR(36) NOT NULL, 
	version INTEGER NOT NULL, 
	content TEXT, 
	summary TEXT, 
	change_note VARCHAR(500), 
	created_by VARCHAR(36), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id)
);
INSERT INTO document_versions VALUES('1df9141f-9bdf-4c5f-a094-abab909de70e','d48b03e1-d1cb-4e23-89e8-0caadf852f5e',1,replace('# AI Agent 集成\n\n## 背景\n\nCodeSeer 平台通过 MCP（Model Context Protocol）协议与 AI 编码工具（Claude Code、OpenCode 等）建立双向通信。AI Agent 作为开发者的代理，能够感知平台上的需求上下文、自主推进开发流程，并将执行结果同步回平台。\n\n## 用户故事\n\n作为开发者，我希望 AI 编码工具能直接从平台拉取需求、同步任务进度、上传文档，以便无需在平台和 IDE 之间手动切换，AI 完整代理整个开发流程。\n\n## 架构概述\n\n```\nAI 编码工具（Claude Code / OpenCode）\n        │\n        │  MCP HTTP Transport (JSON-RPC 2.0)\n        ▼\nCodeSeer MCP Server（/api/mcp/...）\n        │\n        │  SQLAlchemy Async\n        ▼\nCodeSeer 业务数据库（SQLite）\n```\n\nMCP Server 以独立路由挂载在 FastAPI 主应用下，通过 Bearer Token 鉴权，每个 AI 工具实例对应一个开发者身份。\n\n## MCP 工具清单\n\n### 需求相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `get_my_requirements` | 拉取指派给当前开发者的待开发需求列表 |\n| `get_requirement` | 获取单条需求的完整详情（描述、验收标准、现有任务） |\n| `update_requirement_status` | 触发需求状态流转（如 `assigned → in_progress`） |\n\n### 任务相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `sync_tasks` | 按标题 upsert 任务列表；不删除平台已有任务 |\n\n`sync_tasks` 支持字段：\n- `title`：任务标题（匹配键）\n- `description`：任务描述\n- `status`：`pending` / `in_progress` / `completed` / `blocked`\n- `estimated_hours`：预估工时\n- `actual_hours`：实际工时\n\n### 测试相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `submit_test_record` | 上传单元测试执行结果 |\n\n### 文档相关\n\n| 工具名 | 说明 |\n|--------|------|\n| `create_document` | 上传设计文档（Markdown），关联到指定需求 |\n\n### 环境配置\n\n| 工具名 | 说明 |\n|--------|------|\n| `setup_dev_environment` | 安装 superpowers 技能包及 CodeSeer 专属 Skill 到本地 AI 工具 |\n\n## 状态流转\n\n简化后的需求状态机：\n\n```\n草稿(draft)\n  └─ 已指派(assigned)      ← 平台 PM 操作\n       └─ 开发中(in_progress)   ← AI 开始开发时调用\n            └─ 待评审(pending_review)  ← AI 提交评审时调用\n                 ├─ 评审通过(review_approved)\n                 │    └─ 已完成(completed)\n                 └─ 评审驳回(review_rejected)\n                      └─ 开发中(in_progress)  ← 重新开发\n```\n\nAI Agent 典型调用顺序：\n1. `get_my_requirements` → 选择需求\n2. `get_requirement` → 读取详情\n3. `update_requirement_status(action="in_progress")` → 标记开始\n4. `sync_tasks(tasks=[...])` → 同步任务拆解\n5. 开发执行...\n6. `submit_test_record(...)` → 上传测试结果\n7. `create_document(...)` → 上传设计文档\n8. `sync_tasks(tasks=[{status: "completed", actual_hours: N}, ...])` → 终态同步\n9. `update_requirement_status(action="pending_review")` → 提交评审\n\n## 鉴权\n\nMCP Token 通过平台"MCP 配置"页面生成，格式为 Bearer JWT。AI 工具在 `.opencode.json` 或 MCP 配置文件中配置：\n\n```json\n{\n  "mcpServers": {\n    "codeseer": {\n      "type": "http",\n      "url": "http://localhost:8000/mcp",\n      "headers": {\n        "Authorization": "Bearer <TOKEN>"\n      }\n    }\n  }\n}\n```\n\n## Skill 安装\n\n通过 `setup_dev_environment` 工具，AI 会将以下内容安装到项目根目录：\n\n- `superpowers/` — Superpowers 技能包（TDD、代码审查等）\n- `skills/cs_integration/` — CodeSeer 专属 Skill（cs_setup、cs_start 命令）\n\n安装路径使用 `git rev-parse --show-toplevel` 确定项目根目录，**不安装到全局 `~/.opencode/`**。\n\n## 关键约束\n\n- `sync_tasks` 按 `title` 匹配做 upsert，不删除平台已有任务\n- `status` 更新时自动维护 `started_at` / `completed_at` 时间戳\n- 文档上传后为草稿状态，需在平台手动"挂载模块"并"归档"才能纳入模块知识库\n- MCP Token 与用户身份绑定，`get_my_requirements` 只返回该用户被指派的需求\n','\n',char(10)),NULL,'初版',NULL,'2026-06-21 11:34:09.695619');
CREATE TABLE code_changes (
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
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);
INSERT INTO code_changes VALUES('283667d2-1b15-452e-af0a-3451c7da67d7',NULL,NULL,'用户登录功能',5,100,20,'[{"module": "user", "files": 3}]','[{"file": "temp.py", "reason": "\u4e34\u65f6\u8c03\u8bd5"}]','diff/2026-06-14/283667d2-1b15-452e-af0a-3451c7da67d7.diff',75,'STORED',NULL,'2026-06-14 11:22:16.367845','2026-06-14 11:22:16.373389');
CREATE TABLE access_tokens (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	token_prefix VARCHAR(16) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	expires_at DATETIME, 
	last_used_at DATETIME, 
	is_active BOOLEAN, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
INSERT INTO access_tokens VALUES('5707ae58-d799-4259-987c-bb7f6ff124a6','fb32f43f-1755-4041-a6f1-b4e860a54be4','298ce78e55fae41cae4044d98651751450896bbfad963a80ebaa2cdd6159b465','codeseer_k0z','CI Token','2026-07-19 04:04:36.793959','2026-06-19 04:05:46.620853',0,'2026-06-19 04:04:36.794710');
INSERT INTO access_tokens VALUES('203b9a7a-34f6-462a-9e02-e184ab86448b','b7c81bcb-d723-4d19-9f5f-7b19cfa6e9c7','a15ab2189a7500b5629c687c91db5e9999e97f60baffe530f2939c42600fdd8a','codeseer_gg9','opencode','2026-07-19 06:37:42.901953','2026-06-19 12:08:47.313784',1,'2026-06-19 06:37:42.904384');
INSERT INTO access_tokens VALUES('688621ef-094b-4c50-b961-bd9f277750d9','6fd46a29-5870-4573-9fee-62904b96a995','84539972a6db2173fc7e79969ac72f5ea1f4cb74ad5c519b49b370d16358e94c','codeseer_pjl','opencode-developer','2026-07-19 12:12:07.968712','2026-06-21 14:48:58.288547',1,'2026-06-19 12:12:07.970134');
CREATE TABLE requirement_attachments (
	id VARCHAR(36) NOT NULL, 
	requirement_id VARCHAR(36) NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	file_size INTEGER NOT NULL, 
	content_type VARCHAR(100), 
	storage_path VARCHAR(500) NOT NULL, 
	storage_backend VARCHAR(20), 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES requirements (id)
);
CREATE UNIQUE INDEX uq_projects_identifier ON projects(identifier) WHERE identifier IS NOT NULL;
COMMIT;

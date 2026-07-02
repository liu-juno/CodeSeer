-- CodeSeer Database Schema
-- MySQL 5.7+ | Charset: utf8mb4 | Engine: InnoDB
-- Generated: 2026-07-02
-- Database: codeseer

-- ============================================================
-- Table: users
-- ============================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` varchar(36) NOT NULL,
  `email` varchar(200) NOT NULL,
  `name` varchar(100) NOT NULL,
  `role` varchar(15) DEFAULT NULL COMMENT 'admin|product_manager|project_manager|developer|viewer',
  `avatar_color` varchar(20) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `password_hash` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: projects
-- ============================================================
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects` (
  `id` varchar(36) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `status` varchar(9) DEFAULT NULL COMMENT 'active|archived|completed',
  `owner_id` varchar(36) DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `identifier` varchar(50) DEFAULT NULL COMMENT '项目标识，如 code-seer',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: project_members
-- ============================================================
DROP TABLE IF EXISTS `project_members`;
CREATE TABLE `project_members` (
  `id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `role` varchar(20) NOT NULL DEFAULT 'dev',
  `status` varchar(20) NOT NULL DEFAULT 'approved' COMMENT 'pending|approved|rejected',
  `invited_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_project_user` (`project_id`,`user_id`),
  KEY `idx_project_members_project_id` (`project_id`),
  KEY `idx_project_members_user_id` (`user_id`),
  KEY `fk_project_members_invited_by` (`invited_by`),
  CONSTRAINT `fk_project_members_invited_by` FOREIGN KEY (`invited_by`) REFERENCES `users` (`id`),
  CONSTRAINT `fk_project_members_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
  CONSTRAINT `fk_project_members_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: iterations
-- ============================================================
DROP TABLE IF EXISTS `iterations`;
CREATE TABLE `iterations` (
  `id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `status` varchar(11) DEFAULT NULL COMMENT 'planning|development|testing|released|archived',
  `planned_release_date` datetime DEFAULT NULL,
  `actual_release_date` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_iterations_project_id` (`project_id`),
  CONSTRAINT `fk_iterations_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: requirements
-- ============================================================
DROP TABLE IF EXISTS `requirements`;
CREATE TABLE `requirements` (
  `id` varchar(36) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text,
  `acceptance_criteria` text,
  `project_id` varchar(36) NOT NULL,
  `iteration_id` varchar(36) DEFAULT NULL,
  `status` varchar(16) DEFAULT NULL COMMENT 'draft|assigned|in_progress|pending_review|review_approved|review_rejected|completed',
  `priority` varchar(2) DEFAULT NULL COMMENT 'P0|P1|P2|P3',
  `assignee_id` varchar(36) DEFAULT NULL,
  `creator_id` varchar(36) DEFAULT NULL,
  `estimated_hours_min` int(11) DEFAULT NULL,
  `estimated_hours_max` int(11) DEFAULT NULL,
  `actual_hours` int(11) DEFAULT NULL,
  `due_date` datetime DEFAULT NULL,
  `custom_fields` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_requirements_project_id` (`project_id`),
  KEY `idx_requirements_iteration_id` (`iteration_id`),
  CONSTRAINT `fk_requirements_iteration` FOREIGN KEY (`iteration_id`) REFERENCES `iterations` (`id`),
  CONSTRAINT `fk_requirements_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: tasks
-- ============================================================
DROP TABLE IF EXISTS `tasks`;
CREATE TABLE `tasks` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text,
  `status` varchar(11) DEFAULT NULL COMMENT 'pending|in_progress|completed|blocked',
  `priority` varchar(2) DEFAULT NULL,
  `order_index` int(11) DEFAULT NULL,
  `estimated_hours` int(11) DEFAULT NULL,
  `actual_hours` int(11) DEFAULT NULL,
  `tdd_red` varchar(20) DEFAULT NULL,
  `tdd_green` varchar(20) DEFAULT NULL,
  `tdd_refactor` varchar(20) DEFAULT NULL,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_tasks_requirement_id` (`requirement_id`),
  CONSTRAINT `fk_tasks_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: unit_test_records
-- ============================================================
DROP TABLE IF EXISTS `unit_test_records`;
CREATE TABLE `unit_test_records` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) NOT NULL,
  `task_id` varchar(36) DEFAULT NULL,
  `task_title` varchar(200) DEFAULT NULL,
  `test_type` varchar(50) DEFAULT NULL COMMENT 'unit|integration',
  `total_count` int(11) DEFAULT NULL,
  `passed_count` int(11) DEFAULT NULL,
  `failed_count` int(11) DEFAULT NULL,
  `failed_tests` text,
  `coverage` int(11) DEFAULT NULL,
  `result` varchar(10) DEFAULT NULL COMMENT 'all_passed|failed|partial',
  `executed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_unit_test_records_requirement_id` (`requirement_id`),
  KEY `idx_unit_test_records_task_id` (`task_id`),
  CONSTRAINT `fk_unit_test_records_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`),
  CONSTRAINT `fk_unit_test_records_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: documents
-- ============================================================
DROP TABLE IF EXISTS `documents`;
CREATE TABLE `documents` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) DEFAULT NULL,
  `module_id` varchar(36) DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `document_type` varchar(8) DEFAULT NULL COMMENT 'analysis|design|diagram|api|other',
  `content` text,
  `summary` text,
  `key_points` text,
  `status` varchar(10) DEFAULT NULL COMMENT 'draft|archived|deprecated',
  `processing_status` varchar(10) DEFAULT NULL COMMENT 'pending|processing|completed|failed',
  `version` int(11) DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `archived_at` datetime DEFAULT NULL,
  `source_document_ids` text COMMENT 'JSON list, 合并文档来源',
  PRIMARY KEY (`id`),
  KEY `idx_documents_requirement_id` (`requirement_id`),
  KEY `idx_documents_module_id` (`module_id`),
  CONSTRAINT `fk_documents_module` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`),
  CONSTRAINT `fk_documents_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: document_versions
-- ============================================================
DROP TABLE IF EXISTS `document_versions`;
CREATE TABLE `document_versions` (
  `id` varchar(36) NOT NULL,
  `document_id` varchar(36) NOT NULL,
  `version` int(11) NOT NULL,
  `content` text,
  `summary` text,
  `change_note` varchar(500) DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_document_versions_document_id` (`document_id`),
  CONSTRAINT `fk_document_versions_document` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: modules
-- ============================================================
DROP TABLE IF EXISTS `modules`;
CREATE TABLE `modules` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `parent_id` varchar(36) DEFAULT NULL,
  `path` varchar(500) DEFAULT NULL,
  `skill_id` varchar(36) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `project_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_modules_skill_id` (`skill_id`),
  KEY `idx_modules_project_id` (`project_id`),
  KEY `fk_modules_parent` (`parent_id`),
  CONSTRAINT `fk_modules_parent` FOREIGN KEY (`parent_id`) REFERENCES `modules` (`id`),
  CONSTRAINT `fk_modules_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
  CONSTRAINT `fk_modules_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: skills
-- ============================================================
DROP TABLE IF EXISTS `skills`;
CREATE TABLE `skills` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `version` varchar(20) DEFAULT NULL,
  `module_id` varchar(36) DEFAULT NULL,
  `description` text,
  `summary` text,
  `project_id` varchar(36) DEFAULT NULL,
  `knowledge_base_url` varchar(500) DEFAULT NULL,
  `source` varchar(14) DEFAULT NULL COMMENT 'auto_generated|manual',
  `status` varchar(10) DEFAULT NULL COMMENT 'generating|draft|active|deprecated',
  `prompt_template` text,
  `parameters` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: requirement_phases
-- ============================================================
DROP TABLE IF EXISTS `requirement_phases`;
CREATE TABLE `requirement_phases` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) NOT NULL,
  `phase` varchar(13) NOT NULL COMMENT 'clarification|planning|execution|testing|review',
  `status` varchar(11) DEFAULT NULL COMMENT 'pending|in_progress|completed',
  `notes` text,
  `started_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_requirement_phases_requirement_id` (`requirement_id`),
  CONSTRAINT `fk_requirement_phases_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4_unicode_ci;

-- ============================================================
-- Table: requirement_history
-- ============================================================
DROP TABLE IF EXISTS `requirement_history`;
CREATE TABLE `requirement_history` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) NOT NULL,
  `action` varchar(18) NOT NULL,
  `field_name` varchar(100) DEFAULT NULL,
  `old_value` text,
  `new_value` text,
  `actor` varchar(100) DEFAULT NULL,
  `comment` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_requirement_history_requirement_id` (`requirement_id`),
  CONSTRAINT `fk_requirement_history_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: requirement_attachments
-- ============================================================
DROP TABLE IF EXISTS `requirement_attachments`;
CREATE TABLE `requirement_attachments` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) NOT NULL,
  `filename` varchar(255) NOT NULL,
  `file_size` int(11) NOT NULL,
  `content_type` varchar(100) DEFAULT NULL,
  `storage_path` varchar(500) NOT NULL,
  `storage_backend` varchar(20) DEFAULT NULL COMMENT 'local|ftp|oss',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_requirement_attachments_requirement_id` (`requirement_id`),
  CONSTRAINT `fk_requirement_attachments_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: defects
-- ============================================================
DROP TABLE IF EXISTS `defects`;
CREATE TABLE `defects` (
  `id` varchar(36) NOT NULL,
  `title` varchar(200) NOT NULL,
  `description` text,
  `severity` enum('FATAL','CRITICAL','MAJOR','MINOR') DEFAULT NULL,
  `priority` enum('P0','P1','P2','P3') DEFAULT NULL,
  `status` enum('NEW','CONFIRMED','FIXING','VERIFYING','CLOSED') DEFAULT NULL,
  `project_id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) DEFAULT NULL,
  `module_id` varchar(36) DEFAULT NULL,
  `iteration_id` varchar(36) DEFAULT NULL,
  `assignees` text,
  `labels` text,
  `steps_to_reproduce` text,
  `environment` text,
  `creator_id` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `project_id` (`project_id`),
  KEY `requirement_id` (`requirement_id`),
  KEY `module_id` (`module_id`),
  KEY `iteration_id` (`iteration_id`),
  CONSTRAINT `defects_ibfk_1` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`),
  CONSTRAINT `defects_ibfk_2` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`),
  CONSTRAINT `defects_ibfk_3` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`),
  CONSTRAINT `defects_ibfk_4` FOREIGN KEY (`iteration_id`) REFERENCES `iterations` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: defect_comments
-- ============================================================
DROP TABLE IF EXISTS `defect_comments`;
CREATE TABLE `defect_comments` (
  `id` varchar(36) NOT NULL,
  `defect_id` varchar(36) NOT NULL,
  `user_id` varchar(36) DEFAULT NULL,
  `content` text NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `defect_id` (`defect_id`),
  CONSTRAINT `defect_comments_ibfk_1` FOREIGN KEY (`defect_id`) REFERENCES `defects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: defect_logs
-- ============================================================
DROP TABLE IF EXISTS `defect_logs`;
CREATE TABLE `defect_logs` (
  `id` varchar(36) NOT NULL,
  `defect_id` varchar(36) NOT NULL,
  `user_id` varchar(36) DEFAULT NULL,
  `action` varchar(50) NOT NULL,
  `old_value` text,
  `new_value` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `defect_id` (`defect_id`),
  CONSTRAINT `defect_logs_ibfk_1` FOREIGN KEY (`defect_id`) REFERENCES `defects` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: state_machine_config
-- ============================================================
DROP TABLE IF EXISTS `state_machine_config`;
CREATE TABLE `state_machine_config` (
  `id` varchar(36) NOT NULL,
  `state` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `allowed_transitions` text COMMENT 'JSON array',
  `is_initial` tinyint(1) DEFAULT NULL,
  `is_terminal` tinyint(1) DEFAULT NULL,
  `order_index` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: custom_fields
-- ============================================================
DROP TABLE IF EXISTS `custom_fields`;
CREATE TABLE `custom_fields` (
  `id` varchar(36) NOT NULL,
  `field_key` varchar(50) NOT NULL,
  `field_name` varchar(100) NOT NULL,
  `field_type` varchar(11) DEFAULT NULL COMMENT 'text|number|date|select|multiselect|user|module',
  `required` tinyint(1) DEFAULT NULL,
  `options` text COMMENT 'JSON array',
  `default_value` text,
  `order_index` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_field_key` (`field_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: code_changes
-- ============================================================
DROP TABLE IF EXISTS `code_changes`;
CREATE TABLE `code_changes` (
  `id` varchar(36) NOT NULL,
  `requirement_id` varchar(36) DEFAULT NULL,
  `task_id` varchar(36) DEFAULT NULL,
  `title` varchar(200) NOT NULL,
  `files_changed` int(11) DEFAULT NULL,
  `lines_added` int(11) DEFAULT NULL,
  `lines_deleted` int(11) DEFAULT NULL,
  `modules_affected` text COMMENT 'JSON',
  `exceptions` text COMMENT 'JSON',
  `diff_path` varchar(500) DEFAULT NULL,
  `diff_size` int(11) DEFAULT NULL,
  `status` varchar(7) DEFAULT NULL COMMENT 'pending|stored|failed',
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_code_changes_requirement_id` (`requirement_id`),
  KEY `idx_code_changes_task_id` (`task_id`),
  CONSTRAINT `fk_code_changes_requirement` FOREIGN KEY (`requirement_id`) REFERENCES `requirements` (`id`),
  CONSTRAINT `fk_code_changes_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: webhooks
-- ============================================================
DROP TABLE IF EXISTS `webhooks`;
CREATE TABLE `webhooks` (
  `id` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `url` varchar(500) NOT NULL,
  `secret` varchar(100) DEFAULT NULL,
  `events` text COMMENT 'JSON array',
  `enabled` tinyint(1) DEFAULT NULL,
  `max_retries` int(11) DEFAULT NULL,
  `retry_interval` int(11) DEFAULT NULL,
  `timeout` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: webhook_deliveries
-- ============================================================
DROP TABLE IF EXISTS `webhook_deliveries`;
CREATE TABLE `webhook_deliveries` (
  `id` varchar(36) NOT NULL,
  `webhook_id` varchar(36) NOT NULL,
  `event` varchar(100) NOT NULL,
  `payload` text,
  `response_status` int(11) DEFAULT NULL,
  `response_body` text,
  `attempt` int(11) DEFAULT NULL,
  `success` tinyint(1) DEFAULT NULL,
  `error` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_webhook_deliveries_webhook_id` (`webhook_id`),
  CONSTRAINT `fk_webhook_deliveries_webhook` FOREIGN KEY (`webhook_id`) REFERENCES `webhooks` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Table: access_tokens
-- ============================================================
DROP TABLE IF EXISTS `access_tokens`;
CREATE TABLE `access_tokens` (
  `id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `token_hash` varchar(64) NOT NULL,
  `token_prefix` varchar(16) NOT NULL,
  `name` varchar(100) NOT NULL,
  `expires_at` datetime DEFAULT NULL,
  `last_used_at` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_access_tokens_user_id` (`user_id`),
  CONSTRAINT `fk_access_tokens_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- ============================================================
-- Table: api_endpoints
-- ============================================================
DROP TABLE IF EXISTS `api_endpoints`;
CREATE TABLE `api_endpoints` (
  `id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `module_id` varchar(36) DEFAULT NULL,
  `method` varchar(10) NOT NULL COMMENT 'GET|POST|PUT|DELETE|PATCH',
  `path` varchar(200) NOT NULL,
  `summary` varchar(200) DEFAULT NULL,
  `description` text,
  `request_schema` text COMMENT 'JSON Schema',
  `response_schema` text COMMENT 'JSON Schema',
  `headers` text COMMENT 'JSON',
  `status` varchar(10) DEFAULT 'draft' COMMENT 'draft|published|deprecated',
  `version` int(11) DEFAULT 1,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_api_endpoints_project` (`project_id`),
  KEY `idx_api_endpoints_module` (`module_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: api_endpoint_versions
-- ============================================================
DROP TABLE IF EXISTS `api_endpoint_versions`;
CREATE TABLE `api_endpoint_versions` (
  `id` varchar(36) NOT NULL,
  `endpoint_id` varchar(36) NOT NULL,
  `version` int(11) NOT NULL,
  `request_schema` text,
  `response_schema` text,
  `change_note` varchar(500) DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_versions_endpoint` (`endpoint_id`),
  CONSTRAINT `fk_versions_endpoint` FOREIGN KEY (`endpoint_id`) REFERENCES `api_endpoints` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: api_environments
-- ============================================================
DROP TABLE IF EXISTS `api_environments`;
CREATE TABLE `api_environments` (
  `id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `name` varchar(50) NOT NULL,
  `base_url` varchar(200) NOT NULL,
  `variables` text COMMENT 'JSON',
  `is_default` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_envs_project` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: api_test_cases
-- ============================================================
DROP TABLE IF EXISTS `api_test_cases`;
CREATE TABLE `api_test_cases` (
  `id` varchar(36) NOT NULL,
  `endpoint_id` varchar(36) NOT NULL,
  `name` varchar(200) NOT NULL,
  `request_params` text COMMENT 'JSON',
  `expected_status` int(11) DEFAULT NULL,
  `expected_response` text COMMENT 'JSON',
  `created_by` varchar(36) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_cases_endpoint` (`endpoint_id`),
  CONSTRAINT `fk_cases_endpoint` FOREIGN KEY (`endpoint_id`) REFERENCES `api_endpoints` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table: api_test_records
-- ============================================================
DROP TABLE IF EXISTS `api_test_records`;
CREATE TABLE `api_test_records` (
  `id` varchar(36) NOT NULL,
  `endpoint_id` varchar(36) NOT NULL,
  `test_case_id` varchar(36) DEFAULT NULL,
  `environment_id` varchar(36) DEFAULT NULL,
  `request_params` text,
  `response_status` int(11) DEFAULT NULL,
  `response_body` text,
  `response_time_ms` int(11) DEFAULT NULL,
  `result` varchar(10) DEFAULT NULL COMMENT 'pass|fail|error',
  `error_message` text,
  `executed_by` varchar(36) DEFAULT NULL,
  `executed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_records_endpoint` (`endpoint_id`),
  CONSTRAINT `fk_records_endpoint` FOREIGN KEY (`endpoint_id`) REFERENCES `api_endpoints` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `audit_log` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int,
	`action` varchar(100) NOT NULL,
	`resource` varchar(100) NOT NULL,
	`resource_id` varchar(64),
	`details` text,
	`ip_address` varchar(45),
	`user_agent` text,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `audit_log_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `data_products` (
	`id` int AUTO_INCREMENT NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text,
	`category` enum('portfolio','esg','market','risk','performance') NOT NULL,
	`s3_path` varchar(500) NOT NULL,
	`format` varchar(50) NOT NULL,
	`schema` text,
	`row_count` int,
	`size_bytes` int,
	`owner` varchar(100),
	`status` enum('active','deprecated','archived') NOT NULL DEFAULT 'active',
	`last_updated` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `data_products_id` PRIMARY KEY(`id`),
	CONSTRAINT `data_products_name_unique` UNIQUE(`name`)
);
--> statement-breakpoint
CREATE TABLE `esg_data` (
	`id` int AUTO_INCREMENT NOT NULL,
	`ticker` varchar(20) NOT NULL,
	`name` varchar(255) NOT NULL,
	`esg_rating` varchar(10),
	`esg_score` int,
	`environment_score` int,
	`social_score` int,
	`governance_score` int,
	`carbon_intensity` decimal(10,2),
	`controversy_score` int,
	`provider` varchar(50),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `esg_data_id` PRIMARY KEY(`id`),
	CONSTRAINT `esg_data_ticker_unique` UNIQUE(`ticker`)
);
--> statement-breakpoint
CREATE TABLE `kafka_topics` (
	`id` int AUTO_INCREMENT NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text,
	`partitions` int NOT NULL DEFAULT 1,
	`replication_factor` int NOT NULL DEFAULT 1,
	`enabled` boolean NOT NULL DEFAULT true,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `kafka_topics_id` PRIMARY KEY(`id`),
	CONSTRAINT `kafka_topics_name_unique` UNIQUE(`name`)
);
--> statement-breakpoint
CREATE TABLE `loan_payments` (
	`id` int AUTO_INCREMENT NOT NULL,
	`loan_id` varchar(64) NOT NULL,
	`amount` decimal(15,2) NOT NULL,
	`principal` decimal(15,2) NOT NULL,
	`fee` decimal(15,2) NOT NULL,
	`due_date` timestamp NOT NULL,
	`paid_date` timestamp,
	`status` enum('pending','paid','late','missed') NOT NULL DEFAULT 'pending',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `loan_payments_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `loans` (
	`id` varchar(64) NOT NULL,
	`portfolio_id` varchar(64) NOT NULL,
	`investor_id` int NOT NULL,
	`amount` decimal(15,2) NOT NULL,
	`portfolio_value` decimal(15,2) NOT NULL,
	`ltv` decimal(5,4) NOT NULL,
	`term_months` int NOT NULL,
	`fee_rate` decimal(5,4) NOT NULL,
	`monthly_payment` decimal(15,2) NOT NULL,
	`remaining_balance` decimal(15,2) NOT NULL,
	`status` enum('pending','active','paid','defaulted','liquidated') NOT NULL DEFAULT 'pending',
	`approved_by` int,
	`approved_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `loans_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `mcp_executions` (
	`id` int AUTO_INCREMENT NOT NULL,
	`tool_id` int NOT NULL,
	`tool_name` varchar(255) NOT NULL,
	`input` text NOT NULL,
	`output` text,
	`status` enum('success','error','timeout') NOT NULL,
	`duration` int,
	`executed_by` varchar(100),
	`executed_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `mcp_executions_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `mcp_tools` (
	`id` int AUTO_INCREMENT NOT NULL,
	`name` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`category` enum('portfolio','esg','loan','agent','data','system') NOT NULL,
	`input_schema` text NOT NULL,
	`enabled` boolean NOT NULL DEFAULT true,
	`execution_count` int NOT NULL DEFAULT 0,
	`last_executed` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	CONSTRAINT `mcp_tools_id` PRIMARY KEY(`id`),
	CONSTRAINT `mcp_tools_name_unique` UNIQUE(`name`)
);
--> statement-breakpoint
CREATE TABLE `portfolio_holdings` (
	`id` int AUTO_INCREMENT NOT NULL,
	`portfolio_id` varchar(64) NOT NULL,
	`ticker` varchar(20) NOT NULL,
	`weight` decimal(8,6) NOT NULL,
	`value` decimal(15,2) NOT NULL,
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `portfolio_holdings_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `portfolios` (
	`id` varchar(64) NOT NULL,
	`investor_id` int NOT NULL,
	`investor_name` varchar(255) NOT NULL,
	`agent` enum('alpha','beta','gamma','delta','epsilon') NOT NULL,
	`value` decimal(15,2) NOT NULL,
	`initial_investment` decimal(15,2) NOT NULL,
	`return_30d` decimal(8,4),
	`return_1y` decimal(8,4),
	`sharpe_ratio` decimal(8,4),
	`volatility` decimal(8,4),
	`max_drawdown` decimal(8,4),
	`status` enum('active','paused','closed') NOT NULL DEFAULT 'active',
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `portfolios_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE TABLE `rl_agents` (
	`id` int AUTO_INCREMENT NOT NULL,
	`name` enum('alpha','beta','gamma','delta','epsilon') NOT NULL,
	`display_name` varchar(100) NOT NULL,
	`objective` text NOT NULL,
	`model_version` varchar(50) NOT NULL,
	`status` enum('training','deployed','paused','deprecated') NOT NULL DEFAULT 'deployed',
	`episodes_trained` int NOT NULL DEFAULT 0,
	`avg_reward` decimal(10,4),
	`last_trained_at` timestamp,
	`deployed_at` timestamp,
	`created_at` timestamp NOT NULL DEFAULT (now()),
	`updated_at` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `rl_agents_id` PRIMARY KEY(`id`),
	CONSTRAINT `rl_agents_name_unique` UNIQUE(`name`)
);
--> statement-breakpoint
CREATE TABLE `training_runs` (
	`id` int AUTO_INCREMENT NOT NULL,
	`agent_name` enum('alpha','beta','gamma','delta','epsilon') NOT NULL,
	`episodes` int NOT NULL,
	`avg_reward` decimal(10,4),
	`final_reward` decimal(10,4),
	`duration` int,
	`status` enum('running','completed','failed') NOT NULL DEFAULT 'running',
	`started_at` timestamp NOT NULL DEFAULT (now()),
	`completed_at` timestamp,
	CONSTRAINT `training_runs_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
ALTER TABLE `users` MODIFY COLUMN `role` enum('user','admin','operations','analyst') NOT NULL DEFAULT 'user';
ALTER TABLE `data_products` MODIFY COLUMN `category` enum('australian_equities','us_equities','international','asia_pacific','technology','healthcare','financials','energy','commodities','fixed_income','dividend_income','esg_sustainable','broad_market','other') NOT NULL;--> statement-breakpoint
ALTER TABLE `data_products` ADD `ticker` varchar(20);--> statement-breakpoint
ALTER TABLE `data_products` ADD `expense_ratio` varchar(20);--> statement-breakpoint
ALTER TABLE `data_products` ADD `aum` varchar(50);
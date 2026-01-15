-- Database schema for AiTravelAssistant
-- Notes:
-- - `decision_unit.rule_set_ids` stores multiple rule_set_id values separated by commas, per requirement.
-- - Prefer a join table for normalization if/when possible.

-- MySQL 8+ recommended

CREATE TABLE IF NOT EXISTS `rule_set` (
  `rule_set_id` VARCHAR(64) NOT NULL,
  `meta` VARCHAR(5120) NULL,
  `rules_order` VARCHAR(1024) NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`rule_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `decision_unit` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `rule_set_ids` VARCHAR(256) NOT NULL,
  `app_name` VARCHAR(128) NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_decision_unit_app_name` (`app_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


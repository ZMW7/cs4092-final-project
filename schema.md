# Schema

## Tables
### Customers

| name                 | type           | constraints   |
| -------------------- | -------------- | ------------- |
| `id`                 | `uuid`         | `primary key` |
| `created_at`         | `datetime`     | `not null`    |
| `primary_address_id` | `uuid`         | `foreign key` |
| `default_payment_id` | `uuid`         | `foreign key` |
| `email_address`      | `varchar(255)` | `not null`    |
| `password_hash`      | `char(60)`     | `not null`    |

### Addresses

| name                      | type      | constraints   |
| ------------------------- | --------- | ------------- |
| `id`                      | `uuid`    | `primary key` |
| `country`                 | `varchar` | `not null`    |
| `administrative_division` | `varchar` | `not null`    |
| `city`                    | `varchar` | `not null`    |
| `line1`                   | `varchar` | `not null`    |
| `line2`                   | `varchar` | `not null`    |
| `postal_code`             | `varchar` | `not null`    |
| `customer_id`             | `uuid`    | `foreign key` |

### Payment Methods

| name                 | type      | constraints               |
| -------------------- | --------- | ------------------------- |
| `id`                 | `uuid`    | `primary key`             |
| `card_number`        | `varchar` | `not null`                |
| `card_expiration`    | `date`    | `not null`                |
| `card_code`          | `tinyint` | `not null`                |
| `billing_address_id` | `uuid`    | `not null`, `foreign key` |
| `customer_id`        | `uuid`    | `not null`, `foreign key` |

### Products

| name         | type       | constraints               |
| ------------ | ---------- | ------------------------- |
| `id`         | `uuid`     | `primary key`             |
| `stock`      | `integer`  | `not null`                |
| `seller_id`  | `uuid`     | `not null`, `foreign key` |
| `created_at` | `datetime` | `not null`                |

### Ratings

| name          | type       | constraints |
| ------------- | ---------- | ----------- |
| `customer_id` | `uuid`     | `not null`  |
| `product_id`  | `uuid`     | `not null`  |
| `rating`      | `smallint` | `not null`  |
| `created_at`  | `datetime` | `not null`  |

### Sellers

| name         | type       | constraints   |
| ------------ | ---------- | ------------- |
| `id`         | `uuid`     | `primary key` |
| `created_at` | `datetime` | `not null`    |

### Moderators

| name            | type       | constraints   |
| --------------- | ---------- | ------------- |
| `id`            | `uuid`     | `primary key` |
| `created_at`    | `datetime` | `not null`    |
| `first_name`    | `varchar`  | `not null`    |
| `last_name`     | `varchar`  | `not null`    |
| `email`         | `varchar`  | `not null`    |
| `password_hash` | `varchar`  | `not null`    |

### Reports

| name          | type       | constraints               |
| ------------- | ---------- | ------------------------- |
| `id`          | `uuid`     | `primary key`             |
| `customer_id` | `uuid`     | `not null`, `foreign key` |
| `reviewed_by` | `uuid`     | `not null`, `foreign key` |
| `reason`      | `varchar`  | `not null`                |
| `created_at`  | `datetime` | `not null`                |

### Product Removals

| name         | type       | constraints               |
| ------------ | ---------- | ------------------------- |
| `reviewer`   | `uuid`     | `not null`, `foreign key` |
| `product_id` | `uuid`     | `not null`, `foreign key` |
| `removed_at` | `datetime` | `not null`                |

### Seller Removals

| name         | type       | constraints               |
| ------------ | ---------- | ------------------------- |
| `reviewer`   | `uuid`     | `not null`, `foreign key` |
| `seller_id`  | `uuid`     | `not null`, `foreign key` |
| `removed_at` | `datetime` | `not null`                |

### Purchases

| id                  | type       | constraints               |
| ------------------- | ---------- | ------------------------- |
| `id`                | `uuid`     | `primary key`             |
| `created_at`        | `datetime` | `not null`                |
| `customer_id`       | `uuid`     | `not null`, `foreign key` |
| `payment_method_id` | `uuid`     | `not null`, `foreign key` |

### Product Sales

| id            | type   | constraints               |
| ------------- | ------ | ------------------------- |
| `id`          | `uuid` | `primary key`             |
| `purchase_id` | `uuid` | `not null`, `foreign key` |
| `product_id`  | `uuid` | `not null`, `foriegn key` |

### Deliveries

| id                        | type       | constraints               |
| ------------------------- | ---------- | ------------------------- |
| `id`                      | `uuid`     | `primary key`             |
| `purchase_id`             | `uuid`     | `not null`, `foreign key` |
| `address_id`              | `uuid`     | `not null`, `foreign key` |
| `status`                  | `varchar`  |                           |
| `shipped_on`              | `date`     |                           |
| `estimated_delivery_time` | `datetime` |                           |

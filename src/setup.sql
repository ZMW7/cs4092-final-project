CREATE DATABASE company_db;

-- Switching active session to newly created database
\c company_db

CREATE TABLE customers (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    primary_address_id INTEGER,
    preferred_payment_id INTEGER,
    email_address VARCHAR(255) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE addresses (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country VARCHAR(56) NOT NULL,
    administrative_division VARCHAR(24),
    city VARCHAR(127) NOT NULL,
    line1 VARCHAR(127) NOT NULL,
    line2 VARCHAR(127),
    postal_code VARCHAR(10) NOT NULL,
    customer_id INTEGER
);

CREATE TABLE payment_methods (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    card_number VARCHAR(20) NOT NULL,
    card_expiration DATE NOT NULL,
    card_code SMALLINT NOT NULL,
    billing_address_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL
);

CREATE TABLE products (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    stock INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ratings (
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating > 0 AND rating <= 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id, product_id)
);

CREATE TABLE sellers (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_name VARCHAR(63) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE moderators (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(30) NOT NULL,
    email_address VARCHAR(255) NOT NULL UNIQUE,
    password_hash CHAR(60) NOT NULL
);

CREATE TABLE reports (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    reviewed_by INTEGER NOT NULL,
    reason VARCHAR(60) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_removals (
    removed_by INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    removed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, removed_at)
);

CREATE TABLE seller_removals (
    removed_by INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    removed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (seller_id, removed_at)
);

CREATE TABLE purchases (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    customer_id INTEGER NOT NULL,
    payment_method_id INTEGER NOT NULL
);

CREATE TABLE product_sales (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    purchase_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    price_per_item NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE deliveries (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    purchase_id INTEGER NOT NULL,
    address_id INTEGER NOT NULL,
    delivery_status varchar(63),
    shipped_on DATE,
    estimated_delivery_time TIMESTAMPTZ
);

/*
 * Table alterations
*/

ALTER TABLE customers
ADD CONSTRAINT fk_primary_address
    FOREIGN KEY (primary_address_id)
    REFERENCES addresses(id);
ALTER TABLE customers
ADD CONSTRAINT fk_preferred_payment_id
    FOREIGN KEY (preferred_payment_id)
    REFERENCES payment_methods(id);

ALTER TABLE addresses
ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id) 
    REFERENCES customers (id);

ALTER TABLE payment_methods
ADD CONSTRAINT fk_address
    FOREIGN KEY (billing_address_id)
    REFERENCES addresses (id);
ALTER TABLE payment_methods
ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers (id);

ALTER TABLE products
ADD CONSTRAINT fk_seller
    FOREIGN KEY (seller_id)
    REFERENCES sellers (id);

ALTER TABLE ratings
ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers (id);
ALTER TABLE ratings
ADD CONSTRAINT fk_product
    FOREIGN KEY (product_id)
    REFERENCES products (id);

ALTER TABLE reports
ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers (id);
ALTER TABLE reports
ADD CONSTRAINT fk_moderator
    FOREIGN KEY (reviewed_by)
    REFERENCES moderators (id);

ALTER TABLE product_removals
ADD CONSTRAINT fk_moderator
    FOREIGN KEY (removed_by)
    REFERENCES moderators (id);
ALTER TABLE product_removals
ADD CONSTRAINT fk_product
    FOREIGN KEY (product_id)
    REFERENCES products (id);

ALTER TABLE seller_removals
ADD CONSTRAINT fk_moderator
    FOREIGN KEY (removed_by)
    REFERENCES moderators (id);
ALTER TABLE seller_removals
ADD CONSTRAINT fk_seller
    FOREIGN KEY (seller_id)
    REFERENCES sellers (id);

ALTER TABLE purchases
ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id)
    REFERENCES customers (id);
ALTER TABLE purchases
ADD CONSTRAINT fk_payment_method
    FOREIGN KEY (payment_method_id)
    REFERENCES payment_methods (id);

ALTER TABLE product_sales
ADD CONSTRAINT fk_purchase
    FOREIGN KEY (purchase_id)
    REFERENCES purchases (id);
ALTER TABLE product_sales
ADD CONSTRAINT fk_product
    FOREIGN KEY (product_id)
    REFERENCES products (id);

ALTER TABLE deliveries
ADD CONSTRAINT fk_purchase
    FOREIGN KEY (purchase_id)
    REFERENCES purchases (id);
ALTER TABLE deliveries
ADD CONSTRAINT fk_address
    FOREIGN KEY (address_id)
    REFERENCES addresses (id);

/*
 * Inserting sample data
*/

INSERT INTO customers       (email_address,          password_hash) 
VALUES                      ('john.doe@example.com', '$2a$12$FcNaZPOzMCGLr.wOzAEb/uPxpvO3ZC0/6TyzlJ8ZqnWrPNqQnRHWG');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'jane.doe@example.com', '$2a$12$dCf5F65DsnKEbDZoWfUZY.auLmH0xnZ3y4EacLIM1/.jczhUjR36.');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'jane.doe@example.com', '$2a$12$dCf5F65DsnKEbDZoWfUZY.auLmH0xnZ3y4EacLIM1/.jczhUjR36.');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'grant@example.com',    '$2a$12$/8aF7hGx0mjL9Uk4j2VpEO7Smkr8MnxXWoy.E327y2qXueYMr8ove');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'governor@ohio.gov',    '$2a$12$5GlVmholEAkJ1D8dMPNxLeOVQioEdDU463.qukzNMK/X40h3UeYUO');

INSERT INTO customers   (email_address,                         password_hash)
VALUES                  ('masayoshi.takanaka@takanaka.com',     '$2a$12$JqlCLqHJtIoJKZHoHg6y9eCBdcUxH0b7hz9oxswuNTkjBYfuH2ete');

INSERT INTO customers   (email_address,                         password_hash)
VALUES                  ('masayoshi.takanaka@takanaka.com',     '$2a$12$JqlCLqHJtIoJKZHoHg6y9eCBdcUxH0b7hz9oxswuNTkjBYfuH2ete');

INSERT INTO addresses       (   country,                administrative_division,    city,           line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'United Kingdom',                                   London,         '10 Downing Street',                        'SWA1A 2AA',    SELECT(
    INSERT INTO customers       (   email_address,          password_hash) 
    VALUES                      (   'primeminister@uk.gov', '$2a$12$gxPPc.V/70vD9ZkuykgB6uJyxct68nBkb8kVBATDmsiPlKwY4Zqra')
    RETURNING id;
));

INSERT INTO addresses       (   country,                    administrative_division,    city,           line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'United States of America', 'Ohio'                      Bexley,         '358 N. Parkview',                          '43209',        SELECT UNIQUE id FROM customers WHERE customers.email_address = 'governor@ohio.gov');

INSERT INTO addresses       (   country,                    administrative_division,    city,                   line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'Japan',                    'Nagano',                   '767-3 Karuizawa',      'Kitasaku District',    'PO Box 232',       '389-0199',     SELECT UNIQUE id FROM customers WHERE customers.email_address = 'masayoshi.takanaka@takanaka.com');

INSERT INTO payment_methods (   card_number,        card_expiration,    card_code,  billing_address_id, customer_id) VALUES
(                               '4111111111111111', '2028-05-01',       123,        1,                  1),
(                               '5500000000000004', '2027-11-01',       456,        2,                  2),
(                               '340000000000009',  '2029-02-01',       789,        3,                  3),
(                               '6011000000000004', '2026-09-01',       321,        4,                  4),
(                               '4012888888881881', '2030-03-01',       654,        5,                  5),
(                               '5105105105105100', '2027-07-01',       987,        6,                  6),
(                               '4222222222222',    '2028-12-01',       111,        7,                  7);

UPDATE customers SET primary_address_id = 1, prefered_payment_id = 1 WHERE id = 1;
UPDATE customers SET primary_address_id = 2, prefered_payment_id = 2 WHERE id = 2;
UPDATE customers SET primary_address_id = 3, prefered_payment_id = 3 WHERE id = 3;
UPDATE customers SET primary_address_id = 4, prefered_payment_id = 4 WHERE id = 4;
UPDATE customers SET primary_address_id = 7, prefered_payment_id = 7 WHERE id = 7;

-- Sellers
INSERT INTO sellers (seller_name)
VALUES              ('Crest'),
                    ('Vita Coco'),
                    ('Half Priced Books')

-- Products
INSERT INTO products (  stock,  seller_id,  price) 
VALUES              (   1500,   1,          9.99),
                    (   4000,   1,          20.00),
                    (   0,      2,          12.50),
                    (   85,     2,          6.00),
                    (   300,    3,          6.99),
                    (   300,    3,          12.00),
                    (   12,     1,          1000.00);


-- Moderators
INSERT INTO moderators (first_name, last_name,      email_address,                  password_hash) VALUES
                       ('Jim',      'Bob',          'jim.bob@jimbob.com',           '$2a$12$BDiZ4hcX7JSscaXz4PZCkO3f0fbK42K3.oRIGwljBCnL5IoyZX2..'),
                       ('Adams',    'Auditor',      'adams.audit@gmail.com',        '$2a$12$HBCmkCli.zgE3.md7P7zpOWChjQKkHsrSEJKagZ1fFjVu.TVabLSe'),
                       ('Zachary',  'W',            'Zachary.W@example.com',        '$2a$12$DiooaYFiMGFxG/NEnjNMD.dCk3qaePdVrLKA2U8k6uwfuEnaLANEK');

-- Ratings
INSERT INTO ratings (   customer_id,    product_id, rating)
VALUES              (   1,              1,          9),
                    (   1,              5,          6),
                    (   2,              2,          8),
                    (   3,              3,          3),
                    (   4,              4,          10),
                    (   5,              6,          7);


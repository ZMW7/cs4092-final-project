CREATE DATABASE company_db;

-- Switching active session to newly created database
\c company_db

CREATE TABLE customers (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    primary_address_id INTEGER UNIQUE,
    preferred_payment_id INTEGER,
    email_address VARCHAR(320) NOT NULL UNIQUE,
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
    product_name VARCHAR(50) NOT NULL,
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
    reviewed_by INTEGER,
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
    delivery_status varchar(63) DEFAULT 'processing',
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
VALUES                      (   'jim.joe@example.com', '$2a$12$dCf5F65DsnKEbDZoWfUZY.auLmH0xnZ3y4EacLIM1/.jczhUjR36.');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'grant@example.com',    '$2a$12$/8aF7hGx0mjL9Uk4j2VpEO7Smkr8MnxXWoy.E327y2qXueYMr8ove');

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'governor@ohio.gov',    '$2a$12$5GlVmholEAkJ1D8dMPNxLeOVQioEdDU463.qukzNMK/X40h3UeYUO');

INSERT INTO customers   (email_address,                         password_hash)
VALUES                  ('masayoshi.takanaka@takanaka.com',     '$2a$12$UEykOXseO3UtE5L29NuaE.cfJLVJpzRFDeWJkY/i9VLki0lyBLFxG'); -- Password: takanaka

INSERT INTO customers   (email_address,                         password_hash)
VALUES                  ('minecraftiscool@gmail.com',           '$2a$12$JqlCLqHJtIoJKZHoHg6y9eCBdcUxH0b7hz9oxswuNTkjBYfuH2ete'),
                        ('amongusiscool@gmail.com',             '$2a$12$fUNEeYsGvcdP5vQ3Sw/N2Owu52oMB0g5vNSs02kuzUIsgrV5vlpuq'),
                        ('friendlygreeter@gmail.com',           '$2a$12$KWA.ucO/YKflNcOJeCAPMOniKk0Y/K0xrLz7U/nuK4xkFIo0TiUI.'),
                        ('a@b.com',                             '$2a$12$peD6mdrsmjhdFpgDjx9B9uDtuISlAc9uarS3v2xqYUlsadHWYdhem'); -- Pasword: test

INSERT INTO customers       (   email_address,          password_hash) 
VALUES                      (   'primeminister@uk.gov', '$2a$12$gxPPc.V/70vD9ZkuykgB6uJyxct68nBkb8kVBATDmsiPlKwY4Zqra')
RETURNING id;

-- Addresses
INSERT INTO addresses       (   country,                administrative_division,    city,           line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'United Kingdom',       NULL,                       'London',       '10 Downing Street',    NULL,                'SWA1A 2AA',    (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'primeminister@uk.gov'));

INSERT INTO addresses       (   country,                    administrative_division,    city,           line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'United States of America', 'Ohio',                     'Bexley',       '358 N. Parkview',      NULL,                '43209',        (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'governor@ohio.gov'));

INSERT INTO addresses       (   country,                    administrative_division,    city,                   line1,                  line2,              postal_code,    customer_id)
VALUES                      (   'Japan',                    'Nagano',                   '767-3 Karuizawa',      'Kitasaku District',    'PO Box 232',       '389-0199',     (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'masayoshi.takanaka@takanaka.com'));

INSERT INTO addresses       (   country,                    administrative_division,    city,                   line1,                      line2,              postal_code,    customer_id) VALUES
                            (   'United States of America', 'Illinois',                 'Chicago',              '7949 S Essex Ave',         'APT 1',            '60617-1395',   (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'minecraftiscool@gmail.com')),
                            (   'India',                    'Telangana',                'Hyderabad',            'Building No. 3-6-276/1 & 277/1 University, Road, Himayatnagar', NULL, '500029', (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'jane.doe@example.com')),
                            (   'United States of America', 'Wisconsin',                'Milwaukee',            '220 W Fond Du Lac Ave',    NULL,               '53208-4092',   (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'jim.joe@example.com')),
                            (   'Hungary',                  NULL,                       'Budapest',             'Kossuth Lajos',            'u. 14-16',         '1053',         (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'friendlygreeter@gmail.com')),
                            (   'United States of America', 'Colorado',                 'Aurora',               '14132 E Colorado Dr',      NULL,               '80012-5912',   (SELECT DISTINCT id FROM customers WHERE customers.email_address = 'grant@example.com'));


INSERT INTO payment_methods (   card_number,        card_expiration,    card_code,  billing_address_id, customer_id) VALUES
(                               '4111111111111111', '2028-05-01',       123,        1,                  1),
(                               '5500000000000004', '2027-11-01',       456,        2,                  2),
(                               '340000000000009',  '2029-02-01',       789,        3,                  3),
(                               '6011000000000004', '2026-09-01',       321,        8,                  4),
(                               '4012888888881881', '2030-03-01',       654,        5,                  5),
(                               '5105105105105100', '2027-07-01',       987,        6,                  6),
(                               '4222222222222',    '2028-12-01',       111,        7,                  7),
(                               '4222852222222',    '2028-12-01',       111,        7,                  7),
(                               '422275917622',     '2026-12-01',       111,        7,                  8),
(                               '3812058397691758', '2029-03-01',       111,        7,                  6);

UPDATE customers SET primary_address_id = 1, preferred_payment_id = 1 WHERE id = 1;
UPDATE customers SET primary_address_id = 2, preferred_payment_id = 2 WHERE id = 2;
UPDATE customers SET primary_address_id = 3, preferred_payment_id = 3 WHERE id = 3;
UPDATE customers SET primary_address_id = 4, preferred_payment_id = 4 WHERE id = 4;
UPDATE customers SET primary_address_id = 7, preferred_payment_id = 7 WHERE id = 7;

-- Sellers
INSERT INTO sellers (seller_name)
VALUES              ('Crest'),
                    ('Vita Coco'),
                    ('Half Priced Books'),
                    ('Illegal Products LLC'),
                    ('False Advertising LLC'),
                    ('Cool Guitars LLC');

-- Products
INSERT INTO products (  product_name,                   stock,  seller_id,  price) 
VALUES              (   'Small toothpaste tube',        1500,   1,          9.99),
                    (   'Lots of toothpaste',           4000,   1,          20.00),
                    (   '2L Coconut Water',             0,      2,          12.50),
                    (   '1L Coconut Water',             85,     2,          6.00),
                    (   'Dune',                         300,    3,          6.99),
                    (   'The Power Broker',             300,    3,          13.99),
                    (   'Some illegal product',         300,    (SELECT DISTINCT id FROM sellers WHERE seller_name = 'Illegal Products LLC'),   123.45),
                    (   'Some other illegal product',   22,     (SELECT DISTINCT id FROM sellers WHERE seller_name = 'Illegal Products LLC'),   5.00),
                    (   'Some 12 dollar product',       300,    3,          12.00),
                    (   'Some 1000 dollar product',     12,     1,          1000.00),
                    (   'Cool Guitar 1',                2,      (SELECT DISTINCT id FROM sellers WHERE seller_name = 'Cool Guitars LLC'),       500.00);


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
                    (   2,              1,          8),
                    (   5,              6,          7);

-- Product removals
INSERT INTO product_removals (  removed_by, product_id)
VALUES                       (  1,          7),
                             (  2,          8);

-- Seller removals
INSERT INTO seller_removals (   removed_by, seller_id)
VALUES                      (   3,          (SELECT DISTINCT id FROM sellers WHERE seller_name = 'Illegal Products LLC'));

-- Purchases
INSERT INTO purchases   (   customer_id,                                                    payment_method_id)
VALUES                  (   (SELECT DISTINCT id 
                            FROM customers 
                            WHERE email_address = 'masayoshi.takanaka@takanaka.com'),       6),
                        (   (SELECT DISTINCT id
                            FROM customers
                            WHERE email_address = 'grant@example.com'),                     7),
                        (   (SELECT DISTINCT id
                            FROM customers
                            WHERE email_address = 'grant@example.com'),                     7),
                        (   (SELECT DISTINCT id
                            FROM customers
                            WHERE email_address = 'grant@example.com'),                     7),
                        (   (SELECT DISTINCT id
                            FROM customers
                            WHERE email_address = 'grant@example.com'),                     7),
                        (   (SELECT DISTINCT id
                            FROM customers
                            WHERE email_address = 'grant@example.com'),                     7)
                            ;
-- VALUES (6, 6);

-- Product sales
INSERT INTO product_sales   (   purchase_id,    product_id, price_per_item, quantity) VALUES
                            (   1,              11,         500.00,         1       ),
                            (   1,              1,          9.99,           4       ),
                            (   2,              2,          20.00,          1       ),
                            (   3,              3,          12.50,          2       ),
                            (   4,              4,          6.00,           1       ),
                            (   5,              5,          6.99,           12      ),
                            (   6,              6,          13.99,          2       );

-- Deliveries
INSERT INTO deliveries  (   purchase_id,    address_id,     delivery_status,    shipped_on,     estimated_delivery_time     ) VALUES
                        (   1,              1,              'delivered',        '2026-06-01',   '2026-06-04 17:00:00+00'    ),
                        (   2,              8,              'lost',             '2026-06-23',   NULL                        ),
                        (   4,              8,              'shipping',         '2026-06-23',   '2026-06-30 12:00:00+00'    ),
                        (   3,              8,              'delivered',        '2026-06-23',   '2026-06-23 17:00:00+00'    );

-- Reports
INSERT INTO reports     (   customer_id,    reviewed_by,    reason                      )   VALUES
                        (   1,              1,              'false advertising'         );
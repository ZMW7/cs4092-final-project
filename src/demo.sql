
-- Getting the email addresses of all customers in the United States who have rated at least two products.
SELECT C.email_address
FROM customers as C
INNER JOIN ratings as R ON C.id = R.customer_id
GROUP BY C.id, C.email_address
HAVING COUNT(R.customer_id) > 1;

-- Getting the names and ratings of all products with an average rating greater than 7
SELECT P.product_name, AVG(R.rating)
FROM products as P
INNER JOIN ratings as R on P.id = R.product_id
GROUP BY P.id, P.product_name
HAVING AVG(R.rating) > 7;

-- Getting all deliveries that have been lost
SELECT *
FROM deliveries as D
WHERE D.delivery_status = 'lost';

-- Getting all deliveries that are currently being shipped
SELECT *
FROM deliveries as D
WHERE D.delivery_status = 'shipping';
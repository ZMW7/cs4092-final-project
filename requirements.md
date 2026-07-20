# Requirements
This system will be used as a backend for an e-commerce platform.
The e-commerce site will have three primary user-roles: customers, moderators, and sellers. Customers purchase products that are listed on the site by sellers. Moderators review reports made by customers and can remove both products and sellers.

- Each customer shall have an ID, several addresses (one of which is to be marked as the "primary address,"), and credit / debit cards on file that can be used as payment (one of these cards should be desginated the 'prefered' payment method). Each payment method should have an associated billing address. Each customer should have an email address so that receipts or important announcements can be sent to them.
- Every address should have a country, city, state / province, address line 1, address line 2, and postal code. Note that multiple customers can share the same address.
- Customers use the website to find and purchase products. Every product is listed by a seller, and should have information related to the number of items in stock.
- Each purchase can involve multiple products, and uses one form of payment. The date of purchase should be recorded.
- Every purchase is associated with a delivery to an address. Every delivery should have a status, as well as an estimated time of delivery. Each purchase should have a unique ID. The price of each purchased product at time of purchase should be recorded.
- Customers should be able to rate products that they have purchased. The date of the rating should be stored.
- Products are listed on the online marketplace by sellers. When a customer makes a purchase, payment (except for the service's cut) is sent to the seller. A seller should be able to update the 'stock' information of their products.
- Customers should be able to report products for breaking the site's terms of service (for example, the e-commerce site prohibits false advertising). Each report should be given a unique ID and date.
- Reports are reviewed by moderators. Moderators review reports, and can remove products or sellers from the platform.
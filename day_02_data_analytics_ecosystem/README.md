# Data Analytics Ecosystem

## Data Sources, Databases, Data Warehouses, Data Lakes, APIs, Spreadsheets, Business Applications, Transactional vs Analytical Systems, and Data Types

---

## 1. Introduction to the Data Analytics Ecosystem

A data analytics ecosystem is the complete environment through which an organization collects, stores, processes, integrates, analyzes, governs, and consumes data.

Data analytics is not limited to SQL queries, dashboards, or statistical models. Before data can be analyzed, it has to exist somewhere, arrive from somewhere, be stored in an appropriate form, be transformed when necessary, and become accessible to people or systems that need it.

A typical organization may generate data from:

- Websites
- Mobile applications
- Point-of-sale systems
- Banking systems
- ERP systems
- CRM systems
- HR systems
- Manufacturing equipment
- IoT devices
- Social media
- Customer support platforms
- Spreadsheets
- Databases
- APIs
- External data providers
- Government datasets
- Log files
- Documents
- Images
- Audio
- Video

These sources do not necessarily store information in the same format.

A sales application may store transactions in a relational database.

A marketing platform may expose customer campaign information through an API.

An employee may maintain a manually updated Excel spreadsheet.

A website may generate JSON events.

A server may generate text-based log files.

A security system may generate millions of events per day.

An analytics platform therefore needs an ecosystem rather than a single database.

A simplified data analytics ecosystem can be represented as:

    Data Sources
         |
         v
    Data Collection
         |
         v
    Data Integration
         |
         v
    Data Storage
         |
         v
    Data Processing
         |
         v
    Data Modeling
         |
         v
    Data Analytics
         |
         v
    Reports / Dashboards / Models / Decisions

The important point is that each layer solves a different problem.

---

# 2. What Is Data?

Data is a representation of facts, observations, events, measurements, transactions, or other information that can be stored and processed.

Examples include:

    Customer ID: 10245
    Product: Laptop
    Quantity: 2
    Price: 75000
    Purchase Date: 2026-08-21

A dataset may contain:

    Customer_ID | Product | Quantity | Price
    ------------|---------|----------|-------
    101         | Laptop  | 1        | 75000
    102         | Phone   | 2        | 30000
    103         | Tablet  | 1        | 45000

The individual values are data.

When data is organized and interpreted to answer a business question, it becomes useful information.

For example:

    "Customer 102 purchased two phones."

This is meaningful information derived from raw data.

Analytics goes one step further by using information to identify patterns, relationships, trends, anomalies, and possible explanations.

---

# 3. Data Sources

A data source is any system, application, file, device, service, or external location from which data originates or can be retrieved.

A source can be internal or external.

## Internal Data Sources

Internal sources are generated within an organization.

Examples:

- Sales databases
- Customer databases
- Employee systems
- ERP systems
- CRM systems
- Inventory systems
- Accounting systems
- Website logs
- Application databases
- Operational spreadsheets
- Internal APIs

## External Data Sources

External sources originate outside the organization.

Examples:

- Government datasets
- Public APIs
- Market research providers
- Financial data providers
- Weather services
- Social media platforms
- Industry databases
- Partner organizations
- Public websites

---

# 4. Primary and Secondary Data

## Primary Data

Primary data is collected directly for a particular purpose.

Examples:

- Customer surveys
- Interviews
- Experiments
- Sensor measurements
- Direct observations
- Transaction records

## Secondary Data

Secondary data was originally collected by another person or organization and is reused for another purpose.

Examples:

- Government census data
- Public financial datasets
- Research datasets
- Industry reports
- Published statistics

The distinction matters because the analyst should understand how the data was originally collected.

---

# 5. Operational and Analytical Data

One of the most important distinctions in a data analytics ecosystem is between operational data and analytical data.

Operational data supports day-to-day business operations.

Analytical data supports analysis, reporting, and decision-making.

For example, an e-commerce application needs to record:

    Customer places order
    Payment is processed
    Inventory is reduced
    Shipment is created

These are operational activities.

A business analyst may instead ask:

    Which products generated the highest revenue?
    Which region has the highest growth?
    What was monthly revenue for the last three years?
    Which customer segment has the highest retention?

These are analytical questions.

The systems optimized for these two types of workloads are usually different.

---

# 6. Transactional Systems

A transactional system is designed to process business transactions reliably.

These systems are commonly called OLTP systems.

OLTP means:

    Online Transaction Processing

Examples:

- Banking transaction systems
- E-commerce order systems
- Reservation systems
- Payroll systems
- Point-of-sale systems
- Inventory systems

A transaction could be:

    INSERT a new order
    UPDATE an account balance
    DELETE a cancelled reservation
    UPDATE inventory quantity

The primary requirements are usually:

- Correctness
- Consistency
- Reliability
- Concurrency
- Fast transaction processing
- Data integrity

---

# 7. Characteristics of OLTP Systems

An OLTP database typically has:

- Many small transactions
- Frequent INSERT operations
- Frequent UPDATE operations
- Frequent DELETE operations
- Strong consistency requirements
- Many concurrent users
- Highly normalized schemas

Example:

    Customer
       |
       +---- Orders
                |
                +---- Order_Items
                              |
                              +---- Products

Instead of storing everything in one large table, information is divided into related tables.

This reduces unnecessary duplication and helps maintain data integrity.

---

# 8. ACID Properties

Transactional systems often rely heavily on ACID properties.

ACID stands for:

- Atomicity
- Consistency
- Isolation
- Durability

## Atomicity

A transaction should be treated as a single unit.

Suppose a bank transfer moves ₹10,000 from Account A to Account B.

Two operations are required:

    Deduct ₹10,000 from A
    Add ₹10,000 to B

If the first operation succeeds but the second fails, the system should not leave the accounts in an invalid state.

Either the complete transaction succeeds or it is rolled back.

## Consistency

A transaction should move the database from one valid state to another valid state.

For example, an account should not violate rules such as:

    balance >= 0

when such a constraint exists.

## Isolation

Concurrent transactions should not incorrectly interfere with one another.

If two customers purchase the last available item simultaneously, the database must handle concurrency correctly.

## Durability

Once a transaction has been committed, the result should survive system failures.

---

# 9. Analytical Systems

Analytical systems are designed to answer questions about data.

They are commonly associated with OLAP.

OLAP means:

    Online Analytical Processing

Typical analytical queries include:

    SELECT region, SUM(revenue)
    FROM sales
    GROUP BY region;

or:

    SELECT
        month,
        product_category,
        SUM(revenue)
    FROM sales
    GROUP BY month, product_category;

Analytical workloads often involve:

- Large datasets
- Aggregations
- Historical analysis
- Complex joins
- Scanning many records
- Grouping
- Filtering
- Statistical calculations

---

# 10. OLTP vs OLAP

| Feature | OLTP | OLAP |
|---|---|---|
| Primary purpose | Run business operations | Analyze data |
| Example | Order processing | Sales analysis |
| Data | Current operational data | Historical and integrated data |
| Queries | Short and frequent | Complex and analytical |
| Transactions | Many | Relatively fewer |
| Writes | Frequent | Usually less frequent |
| Reads | Small targeted reads | Large scans |
| Schema | Often normalized | Often dimensional/denormalized |
| Users | Applications and operational users | Analysts, managers, data scientists |
| Typical result | Individual records | Aggregated insights |

Example:

OLTP question:

    "What is the status of order 100245?"

OLAP question:

    "What was the average order value by region for every quarter over the last five years?"

These are fundamentally different workloads.

---

# 11. Databases

A database is an organized system for storing and retrieving data.

Databases can use different models.

Major database categories include:

- Relational databases
- Document databases
- Key-value databases
- Graph databases
- Column-family databases
- Time-series databases

---

# 12. Relational Databases

Relational databases organize data into tables.

A table contains:

- Rows
- Columns

Example:

    customers

    customer_id | name        | city
    ------------|-------------|--------
    101         | Rahul       | Delhi
    102         | Priya       | Mumbai
    103         | Arjun       | Pune

A relational database generally provides:

- SQL
- Constraints
- Transactions
- Relationships
- Indexes
- Referential integrity

Examples include:

- PostgreSQL
- MySQL
- Microsoft SQL Server
- Oracle Database
- SQLite

---

# 13. Tables, Rows, and Columns

A table represents a logical entity or relationship.

A row represents an individual record.

A column represents an attribute.

Example:

    employees

    employee_id | name | department | salary

One row:

    101 | Amit | Finance | 85000

Here:

    employee_id = attribute
    name        = attribute
    department  = attribute
    salary      = attribute

The complete row represents one employee record.

---

# 14. Primary Keys

A primary key uniquely identifies a record.

Example:

    employee_id

If:

    employee_id = 101

then another employee should not have the same primary key value.

Primary keys are important for:

- Uniqueness
- Record identification
- Relationships
- Referential integrity

---

# 15. Foreign Keys

A foreign key connects one table to another.

Example:

    customers

    customer_id | name
    ------------|-------
    101         | Amit
    102         | Priya

    orders

    order_id | customer_id | amount
    ---------|-------------|-------
    5001     | 101         | 5000
    5002     | 102         | 7000

Here:

    orders.customer_id

references:

    customers.customer_id

This establishes a relationship between orders and customers.

---

# 16. Database Indexes

An index improves the speed of certain database operations.

Without an index, a database may need to scan many rows to find a record.

For example:

    SELECT *
    FROM customers
    WHERE customer_id = 101;

An index on customer_id can make this lookup much faster.

Indexes are useful for read performance, but they are not free.

They:

- Consume storage
- Require maintenance
- Can slow INSERT operations
- Can slow UPDATE operations
- Can slow DELETE operations

Therefore, indexing is a trade-off.

---

# 17. Database Normalization

Normalization organizes relational data to reduce unnecessary duplication and improve integrity.

Consider:

    order_id | customer_name | customer_city | product | price

If the same customer places 1,000 orders, customer information may be repeated 1,000 times.

A normalized design might separate:

    Customers
    Orders
    Products
    Order_Items

Normalization helps prevent anomalies.

Important anomaly types include:

- Insert anomaly
- Update anomaly
- Delete anomaly

---

# 18. Denormalization

Denormalization intentionally introduces some duplication to improve analytical or read performance.

For example, an analytical table might contain:

    order_id
    customer_name
    customer_city
    product_name
    product_category
    order_date
    revenue

Although some information is repeated, analytical queries may become simpler and faster.

The correct design depends on workload.

---

# 19. Database Management Systems

A DBMS is software that manages databases.

It provides functionality such as:

- Data storage
- Query execution
- Transactions
- Security
- Concurrency control
- Backup
- Recovery
- Index management

Examples:

    PostgreSQL
    MySQL
    Oracle
    SQL Server

A database is the data environment.

A DBMS is the software managing that environment.

---

# 20. Data Warehouses

A data warehouse is a system designed primarily for analytical workloads.

A warehouse usually stores integrated, structured data from multiple sources.

For example:

    CRM
       \
    ERP -----> Data Warehouse
       /
    Sales

The warehouse can provide a consistent analytical view of the organization.

---

# 21. Why Data Warehouses Exist

Operational systems are optimized for running applications.

Analytical systems are optimized for asking questions.

Suppose an organization has:

    CRM database
    ERP database
    Sales database
    Marketing database

Management wants:

    Revenue by customer segment
    Marketing cost by product
    Profit by region

Running large analytical queries directly against operational systems can interfere with business operations.

A warehouse separates analytical workloads from operational workloads.

---

# 22. Data Warehouse Characteristics

A traditional data warehouse commonly has:

- Structured data
- Historical data
- Integrated data
- Analytical schemas
- ETL or ELT pipelines
- SQL-based querying
- Business-oriented models

Common warehouse technologies include:

- Snowflake
- Google BigQuery
- Amazon Redshift
- Microsoft Fabric / Azure-based analytical services
- Databricks SQL
- Oracle data warehouse technologies

---

# 23. Fact and Dimension Tables

A common warehouse design is the star schema.

It contains:

    Fact Table
       |
       +---- Dimension
       +---- Dimension
       +---- Dimension

Example:

    Fact_Sales

    date_id
    customer_id
    product_id
    store_id
    quantity
    revenue

Dimensions:

    Dim_Date
    Dim_Customer
    Dim_Product
    Dim_Store

The fact table contains measurable business events.

Dimensions provide descriptive context.

---

# 24. Fact Tables

A fact table represents measurable events.

Examples:

- Sales
- Purchases
- Shipments
- Payments
- Website interactions

Measures may include:

    quantity
    revenue
    discount
    cost
    profit

A fact table can contain millions or billions of records.

---

# 25. Dimension Tables

Dimension tables describe business entities.

Examples:

    Customer
    Product
    Store
    Employee
    Date
    Geography

A product dimension might contain:

    product_id
    product_name
    category
    subcategory
    brand

The dimensions make facts understandable.

---

# 26. Star Schema

A star schema typically looks like:

                  Dim_Customer
                       |
                       |
    Dim_Product -- Fact_Sales -- Dim_Date
                       |
                       |
                   Dim_Store

The fact table sits in the center.

Dimensions surround it.

This structure is popular because analytical queries are straightforward.

---

# 27. Snowflake Schema

A snowflake schema normalizes dimensions.

For example:

    Fact_Sales
        |
    Dim_Product
        |
    Dim_Category
        |
    Dim_Department

This reduces duplication but introduces additional joins.

Star schemas generally prioritize analytical simplicity.

Snowflake schemas generally introduce more normalization.

---

# 28. Data Marts

A data mart is a smaller analytical data store focused on a particular business function.

Examples:

    Sales Data Mart
    Finance Data Mart
    Marketing Data Mart
    HR Data Mart

A data mart can be:

- Department-specific
- Subject-specific
- Enterprise-wide but limited in scope

---

# 29. Data Lakes

A data lake is a storage environment designed to hold large amounts of data in its original or near-original form.

A lake can store:

- Structured data
- Semi-structured data
- Unstructured data

Examples:

    CSV
    JSON
    Parquet
    XML
    Logs
    Images
    Audio
    Video
    Documents

The defining idea is flexibility.

The data does not necessarily need to be transformed into a rigid relational structure before being stored.

---

# 30. Schema-on-Write vs Schema-on-Read

This distinction is fundamental.

## Schema-on-Write

The structure is defined before or during ingestion.

Typical example:

    Source Data
       |
       v
    Transform
       |
       v
    Validate
       |
       v
    Store according to schema

Traditional data warehouses commonly emphasize schema-on-write.

## Schema-on-Read

Data can be stored first and interpreted when it is queried.

Conceptually:

    Raw Data
       |
       v
    Store
       |
       v
    Apply interpretation during analysis

This approach is common in data lake environments.

---

# 31. Data Lake vs Data Warehouse

| Feature | Data Lake | Data Warehouse |
|---|---|---|
| Data types | Structured, semi-structured, unstructured | Primarily structured |
| Storage approach | Raw/flexible | Curated/structured |
| Schema | Often schema-on-read | Often schema-on-write |
| Main users | Engineers, data scientists, analysts | Analysts, BI users |
| Flexibility | High | Lower |
| Governance challenge | High if unmanaged | Usually easier |
| Typical purpose | Broad data storage and exploration | Reliable analytics and reporting |

A data lake is not simply a cheap warehouse.

It addresses a different set of requirements.

---

# 32. Data Lakehouse

A lakehouse attempts to combine some properties of data lakes and data warehouses.

Conceptually:

    Data Lake Flexibility
            +
    Warehouse Reliability
            =
        Lakehouse

A lakehouse may provide:

- Low-cost scalable storage
- Structured tables
- ACID transactions
- Schema management
- Analytical SQL
- Batch processing
- Machine learning support

Technologies associated with lakehouse architectures include:

- Delta Lake
- Apache Iceberg
- Apache Hudi
- Databricks lakehouse architectures

---

# 33. Data Swamp

A poorly managed data lake can become a data swamp.

A data swamp may have:

- Poor documentation
- Duplicate data
- Unknown ownership
- Inconsistent formats
- Missing metadata
- Poor quality
- No retention policies
- Difficult discovery

Simply storing more data does not create more analytical value.

---

# 34. APIs as Data Sources

API stands for:

    Application Programming Interface

An API allows software systems to communicate.

For analytics, APIs are often used to retrieve data from external or internal systems.

Example:

    Analytics System
          |
          | HTTP Request
          v
       API Server
          |
          v
       JSON Response

A typical API response might be:

    {
        "customer_id": 101,
        "name": "Amit",
        "city": "Delhi"
    }

---

# 35. REST APIs

REST is a commonly used architectural style for web APIs.

Typical HTTP methods include:

    GET
    POST
    PUT
    PATCH
    DELETE

GET is commonly used to retrieve data.

POST is commonly used to create data.

PUT and PATCH are commonly used to modify data.

DELETE is used to remove data.

Analytics pipelines frequently use GET requests to retrieve data.

---

# 36. API Pagination

APIs often limit how many records are returned in a single response.

For example:

    GET /customers?page=1

might return 100 records.

The next request might be:

    GET /customers?page=2

This is pagination.

Common pagination methods include:

- Page number
- Offset and limit
- Cursor-based pagination
- Token-based pagination

An analytics pipeline must understand the API's pagination mechanism or it may collect incomplete data.

---

# 37. API Rate Limits

An API may restrict the number of requests allowed during a time period.

Example:

    1000 requests per hour

If the limit is exceeded, the API may reject requests.

A robust ingestion system therefore considers:

- Rate limits
- Retries
- Backoff
- Authentication
- Pagination
- Timeouts
- API failures
- Duplicate responses

---

# 38. API Authentication

Common authentication approaches include:

- API keys
- OAuth
- Bearer tokens
- Basic authentication
- Signed requests

Credentials should not be hard-coded into analytics scripts.

They should normally be managed using secure configuration mechanisms such as:

- Environment variables
- Secret managers
- Credential vaults

---

# 39. Spreadsheets as Data Sources

Spreadsheets are often underestimated as data sources.

Organizations frequently store business information in:

- Microsoft Excel
- Google Sheets
- CSV files

Examples:

    Sales targets
    Employee lists
    Budgets
    Vendor information
    Product mappings
    Forecasts

A spreadsheet can be valuable operational data.

It can also introduce significant data-quality risks.

---

# 40. Spreadsheet Data Problems

Common problems include:

- Manual entry errors
- Duplicate rows
- Inconsistent formatting
- Missing values
- Different date formats
- Hidden columns
- Merged cells
- Formulas instead of values
- Multiple versions of the same file
- Unknown ownership
- Accidental modifications

Example:

    01/02/2026

Could mean:

    1 February 2026

or:

    January 2, 2026

depending on the locale and convention.

---

# 41. Business Applications

Business applications generate enormous amounts of organizational data.

Important categories include:

## CRM

Customer Relationship Management.

Examples of information:

    Customer
    Lead
    Opportunity
    Sales activity
    Communication history

## ERP

Enterprise Resource Planning.

Examples:

    Finance
    Procurement
    Inventory
    Manufacturing
    Human resources

## HR Systems

Examples:

    Employees
    Attendance
    Payroll
    Recruitment
    Performance

## E-commerce

Examples:

    Customers
    Products
    Orders
    Payments
    Shipments
    Returns

---

# 42. Enterprise Application Data Flow

A typical organization might have:

    CRM
      |
      |
    ERP --------\
                 \
    E-commerce -----> Data Integration -----> Warehouse
                 /
    HR ----------/
      |
    Marketing

Each system may have:

- Different identifiers
- Different formats
- Different update frequencies
- Different definitions
- Different data owners

Data integration attempts to create a coherent analytical view.

---

# 43. Structured Data

Structured data follows a predefined schema.

Example:

    employee_id | name | salary | department
    ------------|------|--------|------------
    101         | Amit | 80000  | Finance
    102         | Priya| 90000  | HR

Relational database tables are classic examples.

Structured data generally has:

- Clearly defined fields
- Defined data types
- Consistent records
- A predictable schema

---

# 44. Semi-Structured Data

Semi-structured data does not necessarily follow a rigid relational table structure, but contains organizational elements such as keys, tags, or nested objects.

Examples:

- JSON
- XML
- YAML
- Some event formats

Example JSON:

    {
        "customer": {
            "id": 101,
            "name": "Amit"
        },
        "orders": [
            {
                "id": 5001,
                "amount": 5000
            },
            {
                "id": 5002,
                "amount": 7000
            }
        ]
    }

The structure is present, but it is not a simple flat table.

---

# 45. Nested Data

Nested data contains objects inside objects or arrays inside objects.

Example:

    customer
       |
       +--- id
       +--- name
       +--- address
       |      |
       |      +--- city
       |      +--- country
       |
       +--- orders
              |
              +--- order 1
              +--- order 2

Relational systems can represent this structure using multiple tables.

Document-oriented systems can often store it directly.

---

# 46. Unstructured Data

Unstructured data does not follow a predefined tabular schema.

Examples:

- Images
- Audio
- Video
- PDFs
- Word documents
- Free-form text
- Scanned documents

For example, an image file contains pixels rather than rows and columns.

A video contains frames and audio streams.

A PDF may contain text, images, tables, and layout information.

---

# 47. Unstructured Data Is Still Data

Unstructured does not mean unusable.

For example:

    Customer support recordings
             |
             v
        Speech-to-text
             |
             v
       Transcribed text
             |
             v
       Sentiment analysis
             |
             v
        Business insight

A photograph can be processed using computer vision.

A document can be processed using OCR and document extraction.

An audio recording can be transcribed.

Unstructured data can therefore become structured or semi-structured data after processing.

---

# 48. Data Classification by Format

| Type | Examples |
|---|---|
| Structured | SQL tables, relational records |
| Semi-structured | JSON, XML, YAML |
| Unstructured | Images, video, audio, documents |
| Text | Logs, emails, articles |
| Binary | Images, compressed files, videos |

The classification is not always absolute.

A PDF containing a table has internal structure, but the document itself is not necessarily a relational dataset.

---

# 49. CSV

CSV means:

    Comma-Separated Values

Example:

    id,name,city
    101,Amit,Delhi
    102,Priya,Mumbai

CSV is simple and widely supported.

Problems can include:

- Commas inside text
- Quoting
- Encoding
- Missing values
- Type inference
- Date interpretation
- Large file size
- Lack of schema metadata

Example:

    "Delhi, India"

requires proper quoting because the value contains a comma.

---

# 50. JSON

JSON means:

    JavaScript Object Notation

Example:

    {
        "id": 101,
        "name": "Amit",
        "skills": ["Python", "SQL"]
    }

JSON is particularly common in:

- APIs
- Web applications
- Event systems
- Configuration files
- Modern data pipelines

It supports nested structures.

---

# 51. Parquet

Apache Parquet is a columnar storage format commonly used in analytical systems.

Instead of organizing data primarily row by row, Parquet stores data in a column-oriented structure.

This is useful for analytical workloads because queries often select only certain columns.

Suppose a dataset has:

    customer_id
    name
    city
    salary
    department

If a query only needs:

    department
    salary

a columnar format can avoid reading unnecessary columns.

Parquet also supports compression and efficient analytical processing.

---

# 52. Row-Oriented vs Column-Oriented Storage

## Row-Oriented

Data is stored conceptually like:

    Row 1:
    id, name, city, salary

    Row 2:
    id, name, city, salary

This is useful for transactional workloads where complete records are frequently accessed.

## Column-Oriented

Data is organized conceptually like:

    id column
    name column
    city column
    salary column

This is useful when analytical queries scan selected columns across many records.

---

# 53. Data Integration

Data integration combines data from multiple sources.

Suppose:

    CRM
    ERP
    Marketing
    Sales

all use different formats.

Integration may involve:

- Extraction
- Transformation
- Validation
- Standardization
- Matching
- Deduplication
- Loading

The objective is to make data usable together.

---

# 54. ETL

ETL means:

    Extract
    Transform
    Load

The process is:

    Source
      |
      v
    Extract
      |
      v
    Transform
      |
      v
    Load
      |
      v
    Destination

Example:

    Extract sales data
           |
           v
    Convert currencies
           |
           v
    Clean customer IDs
           |
           v
    Load warehouse

---

# 55. ELT

ELT means:

    Extract
    Load
    Transform

The data is loaded first and transformed later.

    Source
      |
      v
    Extract
      |
      v
    Load
      |
      v
    Data Platform
      |
      v
    Transform

Cloud analytical platforms make this approach practical because storage and computation can scale independently.

---

# 56. ETL vs ELT

| ETL | ELT |
|---|---|
| Transform before loading | Transform after loading |
| Traditional approach | Common modern approach |
| Destination receives curated data | Destination may receive raw data |
| Useful when target has strict requirements | Useful with scalable cloud platforms |

Neither approach is universally superior.

The appropriate design depends on:

- Data volume
- Data quality
- Compliance
- Cost
- Infrastructure
- Query requirements
- Transformation complexity

---

# 57. Batch Processing

Batch processing handles data in groups.

Example:

    Every night at 2 AM

the system processes:

    Yesterday's sales
    Yesterday's transactions
    Yesterday's website events

Batch processing is suitable when immediate results are unnecessary.

---

# 58. Streaming Data

Streaming processes data continuously or in very small increments.

Example:

    Transaction occurs
          |
          v
    Event generated
          |
          v
    Streaming platform
          |
          v
    Processing
          |
          v
    Dashboard / alert / storage

Streaming is useful for:

- Fraud detection
- Real-time monitoring
- IoT
- Financial markets
- Recommendation systems
- Operational alerts

---

# 59. Batch vs Streaming

| Batch | Streaming |
|---|---|
| Processes groups | Processes continuous events |
| Higher latency | Low latency |
| Easier to operate | More complex |
| Suitable for periodic reports | Suitable for real-time use cases |
| Example: daily sales report | Example: fraud detection |

---

# 60. Data Pipelines

A data pipeline moves data from sources to destinations.

Example:

    PostgreSQL
        |
        v
    Extraction
        |
        v
    Validation
        |
        v
    Transformation
        |
        v
    Warehouse
        |
        v
    BI Dashboard

A pipeline can be simple or highly distributed.

---

# 61. Data Pipeline Failures

Pipelines can fail because of:

- Network problems
- Authentication failures
- API rate limits
- Schema changes
- Missing files
- Corrupted records
- Database downtime
- Invalid values
- Duplicate records
- Unexpected nulls
- Insufficient storage

Reliable pipelines therefore need:

- Monitoring
- Logging
- Alerts
- Retry mechanisms
- Validation
- Error handling
- Observability

---

# 62. Data Quality

Data quality describes how suitable data is for its intended purpose.

Important dimensions include:

- Accuracy
- Completeness
- Consistency
- Timeliness
- Validity
- Uniqueness

Example:

A customer dataset contains:

    customer_id = 101
    email = amit@example.com

If the email is wrong, the data is inaccurate.

If the email is missing for half the customers, the data may be incomplete.

If the same customer appears five times, uniqueness is a problem.

---

# 63. Missing Data

Missing values occur frequently.

Reasons include:

- Optional fields
- Collection failures
- Integration errors
- Human mistakes
- Privacy restrictions
- System limitations

Missing data should not automatically be replaced with zero.

For example:

    salary = NULL

does not necessarily mean:

    salary = 0

NULL means the value is unknown, missing, or not available depending on the context.

---

# 64. Duplicate Data

Duplicates can appear because of:

- Repeated API calls
- Multiple file uploads
- Retry operations
- Human entry
- System migration
- Poor identity matching

Example:

    customer_id | name
    ------------|-----
    101         | Amit
    101         | Amit

Whether this is an error depends on the business meaning.

Two records with the same customer ID may be duplicates.

Two transactions from the same customer are not necessarily duplicates.

Context matters.

---

# 65. Data Lineage

Data lineage describes where data came from and how it changed.

Example:

    CRM.customer_email
            |
            v
    Raw CRM dataset
            |
            v
    Cleaned customer table
            |
            v
    Customer dimension
            |
            v
    Executive dashboard

Lineage helps answer:

    Where did this number come from?

    Which source produced this field?

    Which transformations changed it?

    Which reports depend on it?

---

# 66. Metadata

Metadata is information about data.

Examples:

    Column name
    Data type
    Source system
    Owner
    Creation date
    Update frequency
    Description
    Sensitivity classification

For example:

    column: customer_id
    type: integer
    source: CRM
    description: Unique customer identifier

Metadata makes large data environments understandable.

---

# 67. Data Catalog

A data catalog helps users discover and understand available datasets.

A catalog may provide:

- Dataset names
- Column descriptions
- Owners
- Lineage
- Quality information
- Business definitions
- Access information

Without a catalog, analysts may waste significant time searching for the correct data.

---

# 68. Data Governance

Data governance defines how data should be managed.

It covers areas such as:

- Ownership
- Access
- Security
- Privacy
- Quality
- Retention
- Classification
- Compliance
- Data definitions

Governance becomes especially important as organizations accumulate large amounts of data.

---

# 69. Data Ownership

Every important dataset should have clear ownership.

A data owner may be responsible for:

- Definition
- Quality expectations
- Access rules
- Business meaning
- Compliance requirements

Technical teams may operate the infrastructure, while business teams may own the meaning and responsibility of the data.

---

# 70. Master Data

Master data represents important business entities.

Examples:

- Customers
- Products
- Suppliers
- Employees
- Locations

Different systems may contain different versions of the same entity.

For example:

    CRM:
    Customer ID = C101

    ERP:
    Customer Number = 50101

    Marketing:
    Contact ID = 9981

Data integration may need to determine that all three represent the same customer.

---

# 71. Reference Data

Reference data contains standardized values used for classification.

Examples:

    Country codes
    Currency codes
    Product categories
    Department codes
    Status codes

Example:

    INR
    USD
    EUR
    GBP

Reference data supports consistency across systems.

---

# 72. Data Transformation

Transformation changes data from one representation into another.

Examples:

    Convert text to date
    Convert currency
    Standardize country names
    Remove unwanted spaces
    Split full name
    Combine fields
    Calculate revenue
    Aggregate transactions

Example:

    first_name = "Amit"
    last_name = "Pandey"

may become:

    full_name = "Amit Pandey"

---

# 73. Business Rules

Data transformations often implement business rules.

Example:

    revenue = quantity * unit_price

Another rule:

    profit = revenue - cost

Another:

    customer_segment =
        "Premium" if annual_spend >= 100000
        else "Standard"

The analytical output depends not only on technical processing but also on correct business definitions.

---

# 74. Business Definitions

Different departments may use the same word differently.

For example:

    "Customer"

could mean:

    Anyone registered

or:

    Anyone who completed a purchase

or:

    Anyone with an active account

Similarly:

    "Revenue"

may have specific accounting definitions.

Analytics becomes unreliable when metrics lack consistent definitions.

---

# 75. Single Source of Truth

A single source of truth means there is an authoritative location or definition for important information.

For example:

    Revenue
        |
        v
    Official Finance Dataset

Instead of:

    Sales spreadsheet
    Finance spreadsheet
    Marketing spreadsheet
    Analyst spreadsheet

all containing different numbers.

A single source of truth reduces conflicting reports.

It does not necessarily mean that every piece of data must physically exist in one database.

---

# 76. Data Silos

A data silo occurs when information is isolated within a department, application, or system.

Example:

    Marketing ---> Spreadsheet

    Sales -------> CRM

    Finance -----> ERP

    Operations --> Database

If these systems cannot easily exchange information, analysts may struggle to obtain a complete picture.

---

# 77. Data Federation

Data federation allows users or systems to query multiple data sources without necessarily physically copying all data into one location.

Conceptually:

    Source A ----\
    Source B ----- Federation Layer ---> Query
    Source C ----/

This can be useful when data movement is expensive or undesirable.

---

# 78. Data Virtualization

Data virtualization provides a logical access layer over multiple physical data sources.

The user may query data without knowing exactly where each dataset physically resides.

It can simplify access to distributed data.

---

# 79. Data Storage Layers

A modern analytics architecture may separate storage into multiple layers.

Example:

    Source Systems
          |
          v
    Raw Layer
          |
          v
    Cleaned Layer
          |
          v
    Curated Layer
          |
          v
    Semantic Layer
          |
          v
    BI / Analytics

---

# 80. Raw Data Layer

The raw layer attempts to preserve source data with minimal transformation.

Its purposes include:

- Reprocessing
- Auditing
- Historical preservation
- Debugging
- Traceability

Raw data should still have appropriate security and governance.

Raw does not mean uncontrolled.

---

# 81. Cleaned Data Layer

The cleaned layer may contain:

- Standardized types
- Corrected formats
- Removed duplicates
- Validated records
- Standardized identifiers

Example:

    " Delhi "
    "DELHI"
    "delhi"

may be standardized to:

    "Delhi"

depending on the organization's rules.

---

# 82. Curated Data Layer

The curated layer is designed for business use.

It may contain:

- Business metrics
- Aggregations
- Dimensional models
- Standard definitions
- Trusted datasets

Example:

    Monthly_Sales_By_Region

might contain:

    month
    region
    revenue
    units_sold
    profit

---

# 83. Semantic Layer

A semantic layer translates technical structures into business-friendly concepts.

Instead of asking users to understand:

    fact_sales
    dim_customer
    dim_date
    revenue_net

the semantic layer can expose:

    Sales
    Customers
    Revenue
    Profit
    Orders

It can also standardize calculations.

---

# 84. Business Intelligence

Business intelligence systems allow users to explore and visualize analytical data.

Common outputs include:

- Dashboards
- Reports
- Charts
- KPIs
- Scorecards
- Drill-downs

A BI system generally sits near the consumption layer of an analytics ecosystem.

---

# 85. Analytical Consumers

Different users consume data differently.

## Business Executives

Need:

- KPIs
- Trends
- Performance indicators
- High-level comparisons

## Business Analysts

Need:

- SQL
- Dashboards
- Ad hoc analysis
- Detailed datasets

## Data Scientists

Need:

- Large datasets
- Feature data
- Statistical information
- Experimental data

## Data Engineers

Need:

- Pipelines
- Storage
- Infrastructure
- Data quality
- Reliability

---

# 86. Data Analytics Ecosystem Example

Consider an e-commerce company.

Sources:

    Website
    Mobile app
    Payment system
    CRM
    ERP
    Marketing platforms
    Customer support
    Excel files

Operational systems:

    PostgreSQL
    CRM database
    ERP database

Integration:

    APIs
    ETL/ELT pipelines
    Batch files
    Event streams

Storage:

    Data lake
    Data warehouse

Transformation:

    Cleaning
    Deduplication
    Standardization
    Aggregation

Consumption:

    BI dashboards
    SQL analysis
    Machine learning
    Executive reporting

---

# 87. Example End-to-End Architecture

A conceptual architecture can be:

    +-----------------------------+
    |         Data Sources        |
    +-----------------------------+
       |       |       |       |
       v       v       v       v
     CRM     ERP     APIs   Excel
       \       |       /       /
        \      |      /       /
         +-------------------+
         | Data Integration  |
         +-------------------+
                  |
                  v
         +-------------------+
         |     Data Lake     |
         +-------------------+
                  |
                  v
         +-------------------+
         | Transformation    |
         +-------------------+
                  |
                  v
         +-------------------+
         | Data Warehouse    |
         +-------------------+
                  |
          +-------+-------+
          |               |
          v               v
       BI Tools       Data Science
          |
          v
      Decisions

---

# 88. Operational Database to Warehouse

Suppose an order database contains:

    order_id
    customer_id
    product_id
    quantity
    price
    created_at

The pipeline may:

    1. Extract records
    2. Validate timestamps
    3. Remove duplicates
    4. Standardize identifiers
    5. Calculate revenue
    6. Load fact tables
    7. Connect dimensions
    8. Expose analytical views

The final warehouse structure may become:

    Fact_Sales
        |
        +--- Dim_Customer
        +--- Dim_Product
        +--- Dim_Date

---

# 89. Source System of Record

A system of record is an authoritative operational source for a particular type of information.

Examples:

    HR system -> employee records
    ERP -> financial transactions
    CRM -> customer relationships

The system of record is not necessarily the best place for analytics.

The analytical platform can copy and transform data from the system of record.

---

# 90. Data Replication

Replication copies data from one system to another.

Example:

    Production Database
            |
            v
        Replica
            |
            v
       Analytics

Replication can reduce analytical workload on production systems.

---

# 91. Change Data Capture

CDC means:

    Change Data Capture

CDC identifies changes occurring in a source system.

Instead of copying the entire database every time, the system can capture:

    INSERT
    UPDATE
    DELETE

Example:

    Customer 101 changed city

CDC records the change and sends it downstream.

CDC is particularly useful for near-real-time pipelines.

---

# 92. Full Load vs Incremental Load

## Full Load

Copy everything.

Example:

    10 million records
    -> copy all 10 million

## Incremental Load

Copy only new or changed records.

Example:

    10 million existing records
    + 50,000 new/changed records

Incremental processing can greatly reduce processing cost and time.

---

# 93. Slowly Changing Dimensions

Dimensions can change over time.

Example:

    Customer 101
    City = Delhi

Later:

    City = Mumbai

The organization must decide whether historical reports should show:

    Current city

or:

    City at the time of the transaction

Slowly changing dimension techniques address such requirements.

---

# 94. Historical Data

Historical data allows organizations to analyze change over time.

Examples:

    Sales in 2020
    Sales in 2021
    Sales in 2022
    Sales in 2023
    Sales in 2024
    Sales in 2025

Operational databases often focus heavily on current state.

Analytical platforms are commonly designed to retain and analyze historical states.

---

# 95. Data Granularity

Granularity refers to the level of detail represented by a record.

Example:

    One row per transaction

has finer granularity than:

    One row per month

Example:

    Transaction-level:
    2026-08-01, Order 1001, ₹5000

    Monthly:
    August 2026, ₹12,500,000

Aggregating too early can permanently remove information.

Therefore, the required analytical grain should be understood before designing datasets.

---

# 96. Data Aggregation

Aggregation combines detailed records.

Examples:

    SUM
    AVG
    COUNT
    MIN
    MAX

Example:

    SELECT
        region,
        SUM(revenue)
    FROM sales
    GROUP BY region;

This converts transaction-level data into regional totals.

---

# 97. Data Lake File Organization

Large data lakes commonly organize data using directories or partitions.

Example:

    sales/
        year=2026/
            month=08/
                day=01/
                day=02/
                day=03/

Partitioning can reduce the amount of data scanned for certain queries.

A query for:

    August 2026

may not need to scan data from:

    January 2024

---

# 98. Partitioning

Partitioning divides data into logical sections.

Possible partition keys:

    Date
    Region
    Country
    Business unit

Good partitioning can improve query performance.

Poor partitioning can create:

- Too many small files
- Uneven partitions
- Slow metadata operations
- Data skew

Partitioning should be based on actual query patterns and data distribution.

---

# 99. Data Skew

Data skew occurs when data is distributed unevenly.

Example:

    Region A = 90% of records
    Region B = 5%
    Region C = 3%
    Region D = 2%

Distributed processing may become inefficient because one processing unit receives much more work than others.

Skew is an important issue in large-scale analytics.

---

# 100. Small Files Problem

A data lake may accumulate thousands or millions of small files.

For example:

    file_001.parquet
    file_002.parquet
    file_003.parquet
    ...
    file_500000.parquet

Even if the total data volume is manageable, metadata and file-management overhead can become significant.

File compaction is often used to address this problem.

---

# 101. Data Formats and Their Typical Uses

| Format | Typical Usage |
|---|---|
| CSV | Simple interchange |
| JSON | APIs and events |
| XML | Legacy and enterprise integration |
| Parquet | Analytical storage |
| Avro | Data serialization and event pipelines |
| ORC | Analytical storage |
| TXT | Logs and simple text |
| PDF | Documents |
| JPEG/PNG | Images |
| MP4 | Video |
| WAV/MP3 | Audio |

The best format depends on the workload.

---

# 102. APIs vs Databases

A database is primarily a data storage system.

An API is primarily an interface through which systems interact.

For example:

    Database
        |
        v
    Application
        |
        v
       API
        |
        v
    External Consumer

The API may expose only selected data instead of providing direct database access.

This creates an abstraction boundary.

---

# 103. Database vs Data Warehouse

A database used by an application may answer:

    Find order 1001.

A warehouse may answer:

    Calculate annual revenue by product, region, and customer segment.

The database is optimized for operational interactions.

The warehouse is optimized for analytical workloads.

---

# 104. Warehouse vs Data Lake

A warehouse generally provides highly structured analytical data.

A lake provides broader storage flexibility.

For example:

    Data Warehouse:
        sales tables
        customer tables
        product tables

    Data Lake:
        sales CSV
        JSON events
        application logs
        PDFs
        images
        audio
        video

---

# 105. Database vs Data Lake

A relational database generally expects structured records and provides rich transactional behavior.

A data lake is primarily a scalable storage environment capable of holding many data formats.

A data lake does not automatically provide the same transactional semantics or data-management experience as a relational database.

---

# 106. Data Warehouse vs Data Lakehouse

A warehouse focuses strongly on governed analytical data.

A lakehouse attempts to provide analytical table management over flexible data-lake storage.

The distinction is architectural rather than simply a difference in file format.

---

# 107. Data Mesh

Data mesh is an organizational and architectural approach in which business domains take greater responsibility for their own analytical data products.

For example:

    Sales Domain
       |
       +---- Sales Data Product

    Finance Domain
       |
       +---- Finance Data Product

    Marketing Domain
       |
       +---- Marketing Data Product

The domains own the meaning and quality of their data while following shared organizational standards.

---

# 108. Data Products

A data product is a dataset or data service designed to provide reliable value to consumers.

A good data product may have:

- Clear ownership
- Documentation
- Defined schema
- Quality expectations
- Access controls
- Business definitions
- Reliability expectations

A raw database dump is not automatically a good data product.

---

# 109. Data Contracts

A data contract defines expectations between a producer and consumer.

It may specify:

    Field name
    Data type
    Required/optional status
    Valid values
    Update frequency
    Ownership
    Versioning

Example:

    customer_id -> integer -> required
    email       -> string  -> optional
    created_at  -> timestamp -> required

Data contracts reduce unexpected changes between systems.

---

# 110. Schema Evolution

Data structures change over time.

For example:

Version 1:

    customer_id
    name
    email

Version 2:

    customer_id
    name
    email
    phone

Adding a column may be relatively easy.

Changing:

    customer_id

from integer to a completely incompatible structure can be much more disruptive.

Schema evolution must therefore be managed carefully.

---

# 111. Data Versioning

Data can change over time.

Versioning can be useful for:

- Datasets
- Schemas
- Pipelines
- Data definitions
- Machine learning datasets

A historical version may be necessary to reproduce a previous analysis.

---

# 112. Reproducibility

A good analytical ecosystem should allow analysts to understand how a result was produced.

For example:

    Source Data
       |
       v
    Pipeline Version 4
       |
       v
    Transformation Version 7
       |
       v
    Dataset Version 12
       |
       v
    Dashboard

Reproducibility is especially important in regulated, financial, scientific, and research environments.

---

# 113. Security

Data security includes protecting:

- Confidentiality
- Integrity
- Availability

Important controls include:

- Authentication
- Authorization
- Encryption
- Auditing
- Network controls
- Role-based access
- Data masking

---

# 114. Authentication vs Authorization

Authentication asks:

    Who are you?

Authorization asks:

    What are you allowed to access?

Example:

An analyst may authenticate successfully but still not have permission to access employee salary information.

---

# 115. Encryption

Data may be encrypted:

    At rest

and:

    In transit

Encryption at rest protects stored data.

Encryption in transit protects data moving between systems.

---

# 116. Sensitive Data

Examples of sensitive information may include:

- Personal identifiers
- Financial information
- Health information
- Authentication information
- Confidential business information

Sensitive data should be handled according to applicable organizational and legal requirements.

---

# 117. Access Control

Common access models include:

- Role-based access control
- Attribute-based access control
- Dataset-level permissions
- Column-level security
- Row-level security

For example:

    Finance users -> Finance data

    HR users -> Employee data

    Regional manager -> Only their region

---

# 118. Data Masking

Data masking hides sensitive information.

Example:

    Original:
    9876543210

    Masked:
    XXXXXXX210

Masking allows certain analytical or operational tasks without exposing complete sensitive values.

---

# 119. Data Retention

Organizations may not keep every dataset forever.

Retention policies define:

    How long data is kept
    When it is archived
    When it is deleted
    Who can access it

Retention requirements may depend on:

- Business needs
- Legal requirements
- Regulatory obligations
- Cost
- Privacy

---

# 120. Cost in Data Analytics Ecosystems

Data platforms have several cost components:

- Storage
- Compute
- Network transfer
- API usage
- Backup
- Data processing
- Query execution
- Licensing
- Infrastructure management

Poorly designed queries can become expensive in large analytical systems.

---

# 121. Compute vs Storage

Modern cloud architectures often separate storage and compute.

Storage holds:

    Data

Compute performs:

    Queries
    Transformations
    Processing

This separation allows organizations to scale processing capacity independently from stored data.

---

# 122. Data Observability

Data observability is the ability to understand the health and behavior of data systems.

It may monitor:

- Freshness
- Volume
- Distribution
- Schema
- Quality
- Pipeline failures

Example:

Expected:

    1,000,000 transactions per day

Actual:

    42,000 transactions

This may indicate a pipeline failure.

---

# 123. Freshness

Freshness measures how current the data is.

For example:

    Last update:
    2026-09-03 08:00

If a dashboard promises hourly data but has not updated for twelve hours, freshness is poor.

---

# 124. Data Drift

Data distributions can change.

Example:

Historically:

    60% Mobile
    40% Desktop

Suddenly:

    98% Mobile
    2% Desktop

This could represent real business behavior or a broken tracking system.

Data drift monitoring can identify such changes.

---

# 125. Analytical Data Modeling

Data modeling defines how analytical information is organized.

Common approaches include:

- Star schema
- Snowflake schema
- Wide tables
- Normalized models
- Data vault
- Dimensional models

The correct model depends on:

- Query patterns
- Data volume
- Business requirements
- Update patterns
- Governance

---

# 126. Dimensions and Measures

Analytical systems commonly distinguish between dimensions and measures.

Dimension:

    Region

Measure:

    Revenue

Dimension:

    Product Category

Measure:

    Units Sold

A question can then be expressed as:

    Revenue by Region

or:

    Units Sold by Product Category

---

# 127. Time Dimension

Time is one of the most important analytical dimensions.

A date dimension may include:

    date
    day
    week
    month
    quarter
    year
    fiscal_year
    fiscal_quarter
    weekday
    holiday_flag

This makes time-based analysis easier.

---

# 128. Analytical Query Pattern

Suppose:

    sales

contains:

    transaction_id
    customer_id
    product_id
    date_id
    quantity
    revenue

An analyst might ask:

    Revenue by month and region.

The system may:

    1. Join sales with date
    2. Join sales with customer/store geography
    3. Group by month
    4. Group by region
    5. Sum revenue

This is fundamentally different from retrieving one transaction.

---

# 129. Data Architecture Decisions

When designing an analytics ecosystem, important questions include:

    Where is the data generated?

    How frequently does it change?

    How much data exists?

    Is the data structured?

    Does the workload require transactions?

    Does the workload require analytics?

    Is historical data required?

    How quickly must data become available?

    Who needs access?

    What security requirements apply?

    What level of data quality is required?

    How much operational complexity is acceptable?

---

# 130. Example Decision Framework

If the requirement is:

    Process millions of banking transactions reliably

a transactional database may be appropriate.

If the requirement is:

    Analyze five years of banking transactions

an analytical warehouse may be appropriate.

If the requirement is:

    Store transaction data, logs, JSON events, PDFs, and audio

a data lake may be appropriate.

If the requirement is:

    Provide live exchange-rate data to another application

an API may be appropriate.

If the requirement is:

    Maintain a manually controlled monthly budget

a spreadsheet may be appropriate.

The technology should follow the workload.

---

# 131. Data Source Selection

When evaluating a data source, consider:

- Authority
- Accuracy
- Completeness
- Timeliness
- Granularity
- Accessibility
- Reliability
- Cost
- Security
- Legal constraints

A technically accessible dataset is not necessarily an appropriate dataset.

---

# 132. Data Accessibility

Data may be accessible through:

    SQL
    API
    File
    Object storage
    Application interface
    Event stream

Different access mechanisms create different engineering requirements.

---

# 133. Data Ingestion

Ingestion is the process of bringing data into an analytical environment.

Examples:

    API -> Data Lake

    PostgreSQL -> Warehouse

    Excel -> Data Lake

    Kafka -> Streaming Platform

    Application Logs -> Log Storage

Ingestion may be:

    Batch

or:

    Streaming

---

# 134. Data Processing

Processing transforms or analyzes data.

Examples:

    Filtering
    Joining
    Aggregating
    Sorting
    Cleaning
    Enriching
    Validating

A processing engine may operate on millions or billions of records.

---

# 135. Data Enrichment

Enrichment combines existing data with additional information.

Example:

    Customer transaction
          +
    Geographic lookup
          =
    Transaction with region

Another example:

    IP address
       +
    GeoIP dataset
       =
    Country / City information

---

# 136. Data Reconciliation

Reconciliation compares data between systems.

Example:

    ERP revenue = ₹10 crore

    Warehouse revenue = ₹9.8 crore

The difference needs investigation.

Possible causes include:

- Timing differences
- Missing records
- Duplicate records
- Transformation errors
- Currency differences
- Business-rule differences

---

# 137. Data Consistency Across Systems

Suppose:

    CRM says:
    Customer status = Active

while:

    Billing system says:
    Customer status = Suspended

The analytics team needs to understand which system is authoritative for the required business question.

Consistency is not simply a technical issue.

It can be a business-definition issue.

---

# 138. Data Latency

Data latency is the delay between data generation and data availability for use.

Example:

    Transaction occurs at 10:00
    Warehouse receives it at 10:05

Latency:

    5 minutes

Different use cases require different latency.

A monthly management report can tolerate high latency.

Fraud detection may require very low latency.

---

# 139. Real-Time Analytics

Real-time analytics aims to provide insights with very low latency.

Example:

    Payment
       |
       v
    Event Stream
       |
       v
    Fraud Model
       |
       v
    Fraud Score
       |
       v
    Transaction Decision

This architecture is more complex than daily batch reporting.

---

# 140. Data Lifecycle

Data has a lifecycle:

    Create
      |
      v
    Capture
      |
      v
    Store
      |
      v
    Process
      |
      v
    Analyze
      |
      v
    Archive
      |
      v
    Delete

The lifecycle should account for:

- Business value
- Security
- Cost
- Compliance
- Retention

---

# 141. Common Architecture Mistakes

## Mistake 1: Treating Every Database as an Analytics Platform

An operational database is not automatically an analytical warehouse.

## Mistake 2: Dumping Everything into a Data Lake

Without governance, documentation, and quality controls, a lake can become difficult to use.

## Mistake 3: Ignoring Business Definitions

A technically correct query can still produce the wrong business result.

## Mistake 4: Treating Spreadsheet Data as Perfect

Manual data often requires significant validation.

## Mistake 5: Ignoring Schema Changes

A source system can change a column or API response and break downstream pipelines.

## Mistake 6: Loading Only Current Data

Historical analysis often requires preservation of historical records.

## Mistake 7: Ignoring Data Granularity

Aggregating too early can destroy information needed later.

---

# 142. Example: Complete Retail Analytics Ecosystem

Consider a retail company.

## Sources

    Point-of-sale system
    Website
    Mobile application
    CRM
    ERP
    Marketing APIs
    Excel files
    Customer support platform

## Operational Storage

    Relational databases
    Application databases

## Integration

    APIs
    Batch ingestion
    CDC
    Streaming events

## Raw Storage

    Data lake

## Processing

    Data cleaning
    Validation
    Deduplication
    Standardization
    Enrichment

## Analytical Storage

    Data warehouse

## Modeling

    Fact_Sales
    Dim_Customer
    Dim_Product
    Dim_Date
    Dim_Store

## Consumption

    BI dashboards
    SQL
    Reports
    Forecasting
    Machine learning

---

# 143. Example Data Classification in Retail

Structured:

    Orders
    Products
    Customers
    Payments

Semi-structured:

    JSON website events
    API responses
    XML feeds

Unstructured:

    Product images
    Customer call recordings
    Product videos
    Customer emails
    PDF invoices

A modern analytics ecosystem can handle all three.

---

# 144. Example: Banking Analytics Ecosystem

Sources:

    Core banking system
    ATM systems
    Mobile banking
    Internet banking
    Credit card systems
    CRM
    Fraud systems

Transactional systems handle:

    Deposits
    Withdrawals
    Transfers
    Payments

Analytical systems handle:

    Customer segmentation
    Fraud analysis
    Revenue analysis
    Product performance
    Risk analysis

The operational and analytical environments may therefore be connected but separately optimized.

---

# 145. Example: Manufacturing Analytics Ecosystem

Sources:

    ERP
    Manufacturing execution system
    IoT sensors
    Machines
    Maintenance systems
    Quality systems

Structured data:

    Production orders
    Inventory
    Maintenance records

Streaming data:

    Temperature
    Pressure
    Vibration
    Machine state

Analytics can identify:

    Production trends
    Quality problems
    Equipment anomalies
    Maintenance requirements

---

# 146. Example: Healthcare Analytics Ecosystem

Possible sources include:

    Hospital information systems
    Laboratory systems
    Medical devices
    Appointment systems
    Billing systems
    Documents

Data may include:

    Structured patient records
    Semi-structured API data
    Unstructured clinical notes
    Medical images

Healthcare data requires particularly careful attention to privacy, access control, security, governance, and regulatory requirements.

---

# 147. Example: Marketing Analytics Ecosystem

Sources:

    Advertising platforms
    Website analytics
    CRM
    Email marketing systems
    Social platforms
    Customer surveys

Analytics questions:

    Which channel produces the most conversions?

    What is customer acquisition cost?

    Which campaigns produce the highest revenue?

Data often arrives through APIs.

---

# 148. Data Ecosystem Relationships

The most important relationships can be understood as:

    Data Sources
         |
         | generate
         v
       Data
         |
         | stored in
         v
    Databases / Files / Lakes
         |
         | integrated into
         v
    Analytical Platforms
         |
         | modeled into
         v
    Analytical Datasets
         |
         | consumed by
         v
    Analysts / BI / Data Science
         |
         | produce
         v
    Insights and Decisions

---

# 149. Core Conceptual Distinctions

A useful way to distinguish the major components is:

    Database
    -> General data management system

    OLTP Database
    -> Runs operational transactions

    Data Warehouse
    -> Structured analytical data

    Data Lake
    -> Flexible storage for diverse data

    Lakehouse
    -> Lake-oriented storage with stronger analytical table capabilities

    API
    -> Interface for system-to-system communication

    Spreadsheet
    -> Human-oriented tabular data management

    Data Pipeline
    -> Moves and transforms data

    Data Catalog
    -> Helps people discover and understand data

    Data Governance
    -> Defines rules and responsibilities around data

---

# 150. The Central Principle of the Data Analytics Ecosystem

The central idea is that analytics is an ecosystem rather than a single technology.

A business may simultaneously require:

    Transactional databases
    Data warehouses
    Data lakes
    APIs
    Spreadsheets
    Business applications
    Batch pipelines
    Streaming pipelines
    Data governance
    Data quality
    Metadata
    BI systems
    Data science platforms

Each component exists because it solves a particular problem.

Transactional systems prioritize reliable business operations.

Analytical systems prioritize efficient analysis.

Data warehouses prioritize curated analytical structures.

Data lakes prioritize flexible large-scale storage.

APIs prioritize system-to-system access.

Spreadsheets prioritize human-managed tabular information.

Business applications generate and consume operational data.

Structured data provides predictable schemas.

Semi-structured data provides flexible organization.

Unstructured data provides information without a rigid tabular schema.

The data analytics ecosystem connects these components so that data can move from its original operational context toward reliable analytical use.

The quality of the final analytical result depends not only on the query or visualization, but on the entire chain:

    Source
      ->
    Collection
      ->
    Storage
      ->
    Integration
      ->
    Transformation
      ->
    Modeling
      ->
    Governance
      ->
    Analysis
      ->
    Consumption

A weakness anywhere in this chain can affect the reliability of the final result.

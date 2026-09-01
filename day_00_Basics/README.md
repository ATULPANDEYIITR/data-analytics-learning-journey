# DAY 00: DATA ANALYTICS FUNDAMENTALS

## Overview

This lesson introduced the fundamental concepts of **Data Analytics**. The objective was to understand what data analytics is, what data and datasets are, how data is classified, how data is collected and cleaned, how basic statistics are calculated, how data can be grouped and compared, and how analytical results can support business decisions.

The lesson also introduced important concepts such as **correlation, visualization, KPIs, descriptive/diagnostic/predictive/prescriptive analytics, business questions, analytics workflow, common analytics tools, and essential data analyst skills**.


## 1. What Is Data Analytics?

Data Analytics is the process of examining and analyzing data to discover patterns, understand performance, answer questions, identify problems, and support decision-making.

A simple representation of the analytics process is:

```text
Data
  ↓
Cleaning
  ↓
Analysis
  ↓
Insights
  ↓
Decision
```

The important idea is that data analytics is not simply about calculating numbers. The purpose of analysis is to transform raw data into useful information and actionable insights.

For example, a company may have thousands of sales transactions. Simply storing those transactions does not tell management which region is performing best. Analytics can transform those transactions into meaningful information such as:

* Which region has the highest sales?
* Which products are selling the most?
* Are sales increasing or decreasing?
* Which customers are generating the most revenue?
* What factors may be associated with changes in sales?

---

## 2. Understanding Data

Data represents facts, observations, measurements, records, or other pieces of information that can be collected and analyzed.

Examples of data include:

* Customer names
* Sales transactions
* Product prices
* Website visits
* Employee records
* Survey responses

Data is the fundamental raw material used in data analytics.

Without data, an analyst cannot perform meaningful quantitative analysis.

---

## 3. Understanding a Dataset

A dataset is a structured collection of related data records.

The lesson used a simple customer sales dataset:

```python
dataset = [
    {"name": "Alice", "age": 25, "sales": 5000},
    {"name": "Bob", "age": 30, "sales": 7000},
    {"name": "Charlie", "age": 28, "sales": 6000},
    {"name": "David", "age": 35, "sales": 9000}
]
```

Each dictionary represents one record.

For example:

```text
Alice
Age = 25
Sales = 5000
```

The dataset contains four records.

A dataset can contain thousands, millions, or even billions of records in real-world analytical systems.

---

## 4. Understanding Variables

A variable represents a characteristic, attribute, or property that can have different values.

For example:

```text
Name → Categorical
Age → Numerical
Sales → Numerical
```

In the dataset:

* `Name` identifies a person.
* `Age` represents a numerical measurement.
* `Sales` represents a numerical business metric.

Variables are important because analysts examine relationships and patterns among variables.

For example:

```text
Age → Sales
Advertising → Sales
Region → Revenue
Product → Quantity Sold
```

---

## 5. Data Types

Different kinds of data require different analytical approaches.

The lesson introduced the following data types:

### Numerical Data

Numerical data represents quantities that can be measured or calculated.

Examples:

```text
Age
Salary
Revenue
Sales
Quantity
Temperature
```

Numerical data can be used for mathematical and statistical calculations.

### Categorical Data

Categorical data represents groups or categories.

Examples:

```text
Gender
Region
Product Category
Department
Country
```

Categorical data is generally used to divide observations into groups.

### Ordinal Data

Ordinal data contains categories that have an inherent order or ranking.

Examples:

```text
Poor
Average
Good
Excellent
```

or:

```text
Beginner
Intermediate
Advanced
Expert
```

The categories have an order, but the distance between categories may not be mathematically equal.

### Boolean Data

Boolean data contains two logical states:

```text
True
False
```

Examples include:

```text
Customer Active → True
Customer Verified → False
Payment Completed → True
```

### Date and Time Data

Date and time data represents temporal information.

Examples:

```text
2026-09-01
10:30 AM
2026-09-01 10:30:45
```

Date and time data is particularly important when analyzing trends over time.

### Text Data

Text data contains natural language or other textual information.

Examples:

```text
Customer feedback
Reviews
Comments
Descriptions
Messages
```

---

## 6. Structured and Unstructured Data

Data can be broadly categorized based on how it is organized.

### Structured Data

Structured data follows a predefined organization, usually involving rows and columns.

Examples:

* Database tables
* Spreadsheets
* CSV files

Example:

```text
Name      Age      Sales
Alice     25       5000
Bob       30       7000
Charlie   28       6000
```

Structured data is generally easier to query and analyze using tools such as SQL, Excel, and Python.

### Unstructured Data

Unstructured data does not naturally follow a simple tabular structure.

Examples:

* Images
* Videos
* Audio
* Documents
* Social media content

Modern analytics can involve both structured and unstructured data.

---

## 7. Data Collection

Before analysis can begin, data must be collected.

Common sources of data include:

* Databases
* APIs
* Surveys
* Web applications
* Sensors
* Transaction systems
* Spreadsheets

Different businesses collect data from different sources.

For example, an e-commerce company may collect:

```text
Customer Data
       +
Product Data
       +
Transaction Data
       +
Website Activity
       ↓
Analytics Dataset
```

Understanding the source of data is important because the source can affect data quality, structure, completeness, and reliability.

---

## 8. Data Quality

Good analytics depends on good-quality data.

The lesson introduced six important dimensions of data quality.

### Accuracy

Data should correctly represent the real-world value.

### Completeness

Required information should not be missing.

### Consistency

Data should follow consistent rules and formats.

### Validity

Values should conform to defined requirements.

### Uniqueness

Duplicate records should be identified and handled appropriately.

### Timeliness

Data should be sufficiently current for the intended analysis.

Poor-quality data can lead to incorrect conclusions.

This is why data quality is a fundamental part of data analytics.

---

## 9. Missing Data

Missing data occurs when an expected value is unavailable.

Example:

```python
sales_data = [5000, 7000, None, 9000, 6000]
```

Here:

```text
5000
7000
None
9000
6000
```

The `None` value represents missing data.

The program counted missing values using:

```python
if value is None:
    missing_values += 1
```

The ability to detect missing values is an important part of data cleaning.

In real-world analytics, missing values can occur because of:

* Data-entry errors
* System failures
* Optional survey responses
* Integration problems
* Missing historical records
* Sensor failures

---

## 10. Basic Data Cleaning

Raw data is often not immediately ready for analysis.

Example:

```python
dirty_data = ["100", "200", "", "300", "400"]
```

This data contains:

* Numeric values stored as strings
* An empty value

The program removed the empty value and converted the remaining strings into integers.

```python
clean_data = []

for value in dirty_data:

    if value != "":
        clean_data.append(int(value))
```

Result:

```text
Original:
["100", "200", "", "300", "400"]

Cleaned:
[100, 200, 300, 400]
```

This demonstrated two fundamental cleaning operations:

1. Removing invalid or empty values.
2. Converting data into an appropriate type.

Data cleaning is essential because inaccurate or incorrectly formatted data can produce incorrect analytical results.

---

# 11. Descriptive Statistics

Descriptive statistics are used to summarize and describe data.

The program calculated:

* Total
* Count
* Average
* Minimum
* Maximum
* Median
* Range

These measures provide a basic understanding of a dataset.

---

## 12. Total

The total is calculated by adding all values.

For:

```text
5000
7000
6000
9000
8000
```

The total is:

```text
35000
```

In Python:

```python
total = sum(sales)
```

Total is commonly used to calculate metrics such as:

* Total revenue
* Total sales
* Total expenses
* Total units sold

---

## 13. Count

Count represents the number of observations or records.

In Python:

```python
count = len(sales)
```

For five sales values:

```text
Count = 5
```

Count is useful for understanding dataset size.

---

## 14. Average / Mean

The average, or arithmetic mean, is calculated as:

```text
Mean = Sum of Values / Number of Values
```

For:

```text
5000
7000
6000
9000
8000
```

The average is:

```text
7000
```

In Python:

```python
average = total / count
```

The mean is commonly used to understand the typical numerical value in a dataset.

---

## 15. Minimum

The minimum represents the smallest value in a dataset.

Python provides:

```python
min(sales)
```

For the sales dataset:

```text
Minimum = 5000
```

Minimum values can be useful for identifying:

* Lowest sales
* Lowest salary
* Lowest transaction value
* Minimum performance

---

## 16. Maximum

The maximum represents the largest value in a dataset.

Python provides:

```python
max(sales)
```

For the sales dataset:

```text
Maximum = 9000
```

Maximum values can help identify the highest observed performance or value.

---

## 17. Median

The median represents the middle value after sorting the dataset.

The program first sorted the values:

```python
sorted_sales = sorted(sales)
```

Then it determined whether the number of observations was odd or even.

For an odd number of observations, the middle value is the median.

For an even number of observations, the median is calculated using the two middle values:

```text
Median =
(Value 1 + Value 2) / 2
```

Median can be useful when extreme values may distort the mean.

---

## 18. Range

Range measures the difference between the largest and smallest values.

Formula:

```text
Range = Maximum - Minimum
```

For the example:

```text
Maximum = 9000
Minimum = 5000
```

Therefore:

```text
Range = 4000
```

Range provides a basic indication of how spread out the values are.

---

# 19. Grouping Data

Grouping allows data to be organized according to categories.

The program used regional sales:

```python
sales_by_region = {
    "North": 15000,
    "South": 12000,
    "East": 18000,
    "West": 10000
}
```

This allows the analyst to compare business performance by region.

For example:

```text
North → ₹15,000
South → ₹12,000
East  → ₹18,000
West  → ₹10,000
```

Grouping is a fundamental analytical operation.

In real-world analytics, data may be grouped by:

* Region
* Product
* Customer
* Department
* Month
* Year
* Age group
* Sales channel

---

# 20. Comparing Values

The program identified the region with the highest sales:

```python
best_region = max(
    sales_by_region,
    key=sales_by_region.get
)
```

The result was:

```text
Highest Sales Region: East
Sales: 18000
```

This demonstrates how analytics can answer business questions through comparison.

For example:

```text
Which region has the highest sales?
Which product has the highest revenue?
Which employee has the highest performance?
Which month had the highest revenue?
```

---

# 21. Percentage Change

Percentage change measures how much a value has increased or decreased relative to a previous value.

Formula:

```text
Percentage Change =
((Current Value - Previous Value) / Previous Value) × 100
```

The program used:

```text
Previous Sales = 10,000
Current Sales = 12,500
```

The percentage change is:

```text
25%
```

This means sales increased by 25%.

Percentage change is commonly used for:

* Revenue growth
* Sales growth
* Customer growth
* Expense changes
* Website traffic changes
* Profit changes

---

# 22. Correlation

Correlation measures the relationship between variables.

The program used:

```text
Advertising → Sales

10 → 100
20 → 150
30 → 200
40 → 260
50 → 300
```

The example demonstrates that advertising and sales appear to move together.

A crucial analytical principle was introduced:

```text
Correlation does not automatically mean causation.
```

This means that if two variables are associated, it does not automatically prove that one caused the other.

For example:

```text
Ice Cream Sales ↑
Swimming Pool Visits ↑
```

These variables may be correlated because both are influenced by another factor such as warmer weather.

Correlation is therefore useful for identifying relationships, but additional analysis is required before making causal conclusions.

---

# 23. Data Visualization

Data visualization represents data graphically so that patterns and relationships can be understood more easily.

The lesson introduced:

| Visualization | Main Purpose          |
| ------------- | --------------------- |
| Bar Chart     | Compare categories    |
| Line Chart    | Show trends over time |
| Pie Chart     | Show proportions      |
| Histogram     | Show distribution     |
| Scatter Plot  | Show relationships    |

### Bar Chart

Useful for comparing categories.

Example:

```text
North  ███████████
South  █████████
East   █████████████
West   ███████
```

### Line Chart

Useful for understanding trends over time.

Example:

```text
January → February → March → April
```

### Pie Chart

Useful for showing proportions of a whole.

### Histogram

Useful for understanding the distribution of numerical values.

### Scatter Plot

Useful for examining relationships between two numerical variables.

Visualization helps transform numerical information into patterns that are easier to interpret.

---

# 24. Key Performance Indicators

A KPI, or **Key Performance Indicator**, is a measurable value used to evaluate performance against a business objective.

The program introduced:

```text
Revenue
Customers
Conversion Rate
Customer Retention
```

Example:

```text
Revenue            → ₹500,000
Customers          → 2,500
Conversion Rate    → 4.5%
Customer Retention → 82%
```

KPIs allow organizations to monitor important business outcomes.

Examples of KPIs in different environments include:

```text
Business:
Revenue
Profit Margin
Customer Retention

Marketing:
Conversion Rate
Customer Acquisition Cost
Website Traffic

Sales:
Sales Revenue
Average Deal Size
Sales Growth

Operations:
Delivery Time
Defect Rate
Production Output
```

---

# 25. Types of Data Analytics

Four major types of analytics were introduced.

## Descriptive Analytics

Answers:

```text
What happened?
```

Example:

```text
Sales increased by 20% this month.
```

Descriptive analytics focuses on understanding historical or current data.

---

## Diagnostic Analytics

Answers:

```text
Why did it happen?
```

Example:

```text
Sales increased because demand for Product A increased.
```

Diagnostic analytics attempts to identify factors associated with an observed outcome.

---

## Predictive Analytics

Answers:

```text
What might happen?
```

Example:

```text
Sales may increase next month based on historical trends.
```

Predictive analytics uses historical data and analytical models to estimate future outcomes.

---

## Prescriptive Analytics

Answers:

```text
What should we do?
```

Example:

```text
Increase inventory for products with expected higher demand.
```

Prescriptive analytics focuses on potential actions and decisions.

---

# 26. Business Questions

Data analytics should begin with a clear question.

The example business question was:

```text
Which region generated the highest sales?
```

The analysis produced:

```text
East
```

This illustrates an important principle:

```text
Business Question
        ↓
Data
        ↓
Analysis
        ↓
Insight
        ↓
Decision
```

An analyst should not simply analyze data without understanding the business problem.

The goal is to connect analysis to a meaningful question.

---

# 27. Basic Data Analytics Workflow

The complete workflow introduced in the lesson was:

```text
Business Question
       ↓
Data Collection
       ↓
Data Cleaning
       ↓
Data Transformation
       ↓
Exploratory Analysis
       ↓
Statistical Analysis
       ↓
Visualization
       ↓
Insights
       ↓
Decision
```

Each stage has an important purpose.

### Business Question

Determine what needs to be answered.

### Data Collection

Obtain relevant information.

### Data Cleaning

Fix or remove problematic data.

### Data Transformation

Convert data into a form suitable for analysis.

### Exploratory Analysis

Explore patterns, distributions, relationships, and unusual observations.

### Statistical Analysis

Apply mathematical and statistical techniques.

### Visualization

Present important findings graphically.

### Insights

Interpret what the analysis means.

### Decision

Use the findings to support an action or business decision.

---

# 28. Common Data Analytics Tools

The lesson introduced several commonly used analytics tools:

```text
Excel
SQL
Python
R
Power BI
Tableau
Databases
```

Each tool can serve different purposes.

### Excel

Useful for:

* Spreadsheet analysis
* Formulas
* Pivot tables
* Basic visualization
* Data cleaning

### SQL

Useful for:

* Querying databases
* Filtering data
* Aggregating data
* Joining tables
* Extracting business information

### Python

Useful for:

* Data cleaning
* Data analysis
* Automation
* Statistical analysis
* Visualization
* Machine learning

### R

Useful for:

* Statistics
* Data analysis
* Visualization
* Research

### Power BI

Useful for:

* Business intelligence
* Interactive dashboards
* Reporting
* Visualization

### Tableau

Useful for:

* Data visualization
* Interactive dashboards
* Business intelligence

### Databases

Databases store and manage large collections of structured data.

---

# 29. Data Analyst Skills

The lesson identified important skills required for data analytics.

These include:

```text
Data Cleaning
SQL
Statistics
Data Visualization
Excel
Python
Business Understanding
Communication
Problem Solving
```

A strong data analyst needs both technical and business skills.

Technical skills allow the analyst to work with data.

Business understanding allows the analyst to understand why the analysis matters.

Communication allows the analyst to explain findings to people who may not have a technical background.

Problem-solving allows the analyst to convert ambiguous business problems into analytical questions.

---

# 30. Important Concepts Learned

The following concepts were covered in this lesson:

1. Data Analytics
2. Data
3. Dataset
4. Variables
5. Numerical Data
6. Categorical Data
7. Ordinal Data
8. Boolean Data
9. Date and Time Data
10. Text Data
11. Structured Data
12. Unstructured Data
13. Data Collection
14. Data Quality
15. Missing Data
16. Data Cleaning
17. Descriptive Statistics
18. Total
19. Count
20. Mean
21. Median
22. Minimum
23. Maximum
24. Range
25. Data Grouping
26. Value Comparison
27. Percentage Change
28. Correlation
29. Data Visualization
30. KPIs
31. Descriptive Analytics
32. Diagnostic Analytics
33. Predictive Analytics
34. Prescriptive Analytics
35. Business Questions
36. Analytics Workflow
37. Analytics Tools
38. Data Analyst Skills

---

# 31. Practical Python Concepts Used

The program also demonstrated several basic Python programming concepts relevant to data analytics.

### Lists

```python
sales = [5000, 7000, 6000, 9000, 8000]
```

Lists were used to store collections of values.

### Dictionaries

```python
sales_by_region = {
    "North": 15000,
    "South": 12000,
    "East": 18000,
    "West": 10000
}
```

Dictionaries were used to associate categories with values.

### Loops

```python
for value in sales_data:
    print(value)
```

Loops were used to process multiple records.

### Conditional Statements

```python
if value is None:
    missing_values += 1
```

Conditions were used to identify missing values.

### Built-in Functions

The program used functions such as:

```python
sum()
len()
min()
max()
sorted()
```

These functions are extremely useful when working with datasets.

### Type Conversion

The program converted strings into integers:

```python
int(value)
```

This demonstrated the importance of data types during data cleaning.

---

# 32. The Core Idea of Data Analytics

The most important lesson from this topic is that **data analytics is about turning raw data into useful insights that support decisions**.

A simple example is:

```text
Raw Data
   ↓
Sales Transactions
   ↓
Clean Data
   ↓
Regional Sales
   ↓
Analysis
   ↓
East = Highest Sales
   ↓
Business Insight
   ↓
Investigate Why East Performs Better
   ↓
Business Decision
```

The analyst's job is not simply to produce numbers.

The analyst needs to understand:

```text
What happened?
Why did it happen?
What might happen next?
What should we do?
```

These four questions correspond to the four major types of analytics:

```text
Descriptive  → What happened?
Diagnostic   → Why did it happen?
Predictive   → What might happen?
Prescriptive → What should we do?
```

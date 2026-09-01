# ============================================================
# DAY 01: INTRODUCTION TO DATA ANALYTICS
# ============================================================
#
# PURPOSE:
# This program provides a complete introduction to Data Analytics.
#
# TOPICS COVERED:
# 1. What is Data Analytics?
# 2. Data vs Information vs Knowledge
# 3. What is an Analyst?
# 4. Role and Responsibilities of a Data Analyst
# 5. Types of Data Analytics
# 6. Descriptive Analytics
# 7. Diagnostic Analytics
# 8. Predictive Analytics
# 9. Prescriptive Analytics
# 10. Analytics Lifecycle
# 11. Real-World Applications
# 12. Structured vs Unstructured Data
# 13. Quantitative vs Qualitative Data
# 14. Metrics, Measures, Dimensions and KPIs
# 15. Basic Data Exploration
# 16. Business Questions vs Analytical Questions
# 17. Correlation vs Causation
# 18. Basic Statistical Thinking
# 19. Decision Making Using Data
# 20. Introduction to Excel, Python and Jupyter
#
# TOOLS:
# - Python
# - Jupyter Notebook
# - Excel concepts
#
# ============================================================


print("=" * 70)
print("DAY 01 - INTRODUCTION TO DATA ANALYTICS")
print("=" * 70)


# ============================================================
# SECTION 1: WHAT IS DATA?
# ============================================================

print("\n" + "=" * 70)
print("1. WHAT IS DATA?")
print("=" * 70)

print("""
Data is a collection of raw facts, observations, measurements,
records, symbols, values, or events.

Examples:

    Age = 30
    Sales = 250000
    City = Lucknow
    Temperature = 32.5
    Product = Laptop
    Quantity Sold = 15

These values by themselves may not provide a complete meaning.

Data becomes useful when we provide context, organize it,
analyze it, and interpret it.
""")

print("\nExample of raw data:")

sales = [12000, 15000, 18000, 11000, 22000]

print("Sales values:", sales)


# ============================================================
# SECTION 2: WHAT IS DATA ANALYTICS?
# ============================================================

print("\n" + "=" * 70)
print("2. WHAT IS DATA ANALYTICS?")
print("=" * 70)

print("""
Data Analytics is the systematic process of collecting,
cleaning, transforming, exploring, analyzing, interpreting,
and communicating data to generate useful insights and
support decision-making.

A simplified representation is:

    RAW DATA
       |
       v
    CLEANING
       |
       v
    TRANSFORMATION
       |
       v
    EXPLORATION
       |
       v
    ANALYSIS
       |
       v
    INSIGHT
       |
       v
    DECISION
       |
       v
    ACTION
       |
       v
    OUTCOME

The important idea is that analytics is not simply
"looking at numbers".

Analytics attempts to answer meaningful questions.
""")

print("\nExample:")

monthly_sales = {
    "January": 100000,
    "February": 120000,
    "March": 95000,
    "April": 150000
}

print("Monthly sales:", monthly_sales)

average_sales = sum(monthly_sales.values()) / len(monthly_sales)

print("Average monthly sales:", average_sales)

print("""
The raw values are DATA.

The calculated average is INFORMATION.

The observation that April performed significantly better
than March is an INSIGHT.

A decision such as increasing April's successful marketing
strategy is an ACTION.
""")


# ============================================================
# SECTION 3: DATA VS INFORMATION VS KNOWLEDGE
# ============================================================

print("\n" + "=" * 70)
print("3. DATA VS INFORMATION VS KNOWLEDGE")
print("=" * 70)

print("""
DATA
----
Raw facts without sufficient interpretation.

Example:
    500
    600
    700

INFORMATION
-----------
Processed or organized data that provides meaning.

Example:
    Monthly sales were:
    January = 500
    February = 600
    March = 700

KNOWLEDGE
---------
Understanding derived from information, experience,
analysis, and context.

Example:
    Sales increased for three consecutive months,
    suggesting improving demand.

WISDOM / DECISION
-----------------
Applying knowledge to make a decision.

Example:
    Increase inventory because demand is increasing.
""")


# ============================================================
# SECTION 4: EXAMPLE OF DATA -> INFORMATION -> KNOWLEDGE
# ============================================================

print("\n" + "=" * 70)
print("4. DATA -> INFORMATION -> KNOWLEDGE -> DECISION")
print("=" * 70)

orders = [100, 120, 135, 160, 190]

print("Raw order data:", orders)

growth = ((orders[-1] - orders[0]) / orders[0]) * 100

print("Overall growth:", round(growth, 2), "%")

print("""
Interpretation:

Data:
    100, 120, 135, 160, 190

Information:
    Orders increased from 100 to 190.

Knowledge:
    The business experienced substantial growth.

Decision:
    Management may need to increase inventory,
    staffing, logistics capacity, or marketing investment.

This demonstrates why analytics connects data to decisions.
""")


# ============================================================
# SECTION 5: WHAT IS A DATA ANALYST?
# ============================================================

print("\n" + "=" * 70)
print("5. WHO IS A DATA ANALYST?")
print("=" * 70)

print("""
A Data Analyst is a professional who works with data to
answer questions, identify patterns, discover problems,
measure performance, communicate insights, and support
business or organizational decisions.

A Data Analyst commonly works across several stages:

    Business Question
          |
          v
    Data Collection
          |
          v
    Data Cleaning
          |
          v
    Data Exploration
          |
          v
    Data Analysis
          |
          v
    Visualization
          |
          v
    Insight
          |
          v
    Recommendation
          |
          v
    Decision
""")


# ============================================================
# SECTION 6: ROLE OF A DATA ANALYST
# ============================================================

print("\n" + "=" * 70)
print("6. ROLE AND RESPONSIBILITIES OF A DATA ANALYST")
print("=" * 70)

responsibilities = [
    "Understand business problems",
    "Define analytical questions",
    "Collect data",
    "Extract data from databases",
    "Clean data",
    "Handle missing values",
    "Identify duplicate records",
    "Detect anomalies",
    "Transform data",
    "Perform exploratory analysis",
    "Calculate metrics",
    "Create dashboards",
    "Build visualizations",
    "Identify trends",
    "Compare performance",
    "Communicate findings",
    "Make data-driven recommendations",
    "Monitor KPIs",
    "Support decision-making"
]

for number, responsibility in enumerate(responsibilities, start=1):
    print(f"{number:02d}. {responsibility}")


# ============================================================
# SECTION 7: DATA ANALYST MINDSET
# ============================================================

print("\n" + "=" * 70)
print("7. DATA ANALYST MINDSET")
print("=" * 70)

print("""
A strong analyst does not immediately jump into calculations.

A good analytical process asks:

1. What problem are we trying to solve?
2. What decision needs to be made?
3. What data is relevant?
4. Is the data trustworthy?
5. What assumptions are we making?
6. What patterns exist?
7. What could explain those patterns?
8. Are there alternative explanations?
9. Does correlation imply causation?
10. How certain are we?
11. What action should be taken?
12. How will we measure the result?

The analyst should remain curious, skeptical,
logical, quantitative, and business-oriented.
""")


# ============================================================
# SECTION 8: TYPES OF DATA ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("8. TYPES OF DATA ANALYTICS")
print("=" * 70)

analytics_types = {
    "Descriptive": "What happened?",
    "Diagnostic": "Why did it happen?",
    "Predictive": "What is likely to happen?",
    "Prescriptive": "What should we do?"
}

for analytics_type, question in analytics_types.items():
    print(f"{analytics_type:15} -> {question}")


# ============================================================
# SECTION 9: DESCRIPTIVE ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("9. DESCRIPTIVE ANALYTICS")
print("=" * 70)

print("""
Descriptive analytics summarizes historical or current data.

Primary question:

    WHAT HAPPENED?

Common techniques:

    - Counts
    - Sums
    - Averages
    - Percentages
    - Minimum
    - Maximum
    - Frequencies
    - Aggregation
    - Trend summaries
    - Dashboards
    - Reports
""")


sales_data = [100, 120, 150, 130, 170, 200]

total_sales = sum(sales_data)
average_sales = total_sales / len(sales_data)
minimum_sales = min(sales_data)
maximum_sales = max(sales_data)

print("Sales data:", sales_data)
print("Total:", total_sales)
print("Average:", average_sales)
print("Minimum:", minimum_sales)
print("Maximum:", maximum_sales)

print("""
These calculations describe what happened.

They do not necessarily explain WHY sales changed.
""")


# ============================================================
# SECTION 10: DIAGNOSTIC ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("10. DIAGNOSTIC ANALYTICS")
print("=" * 70)

print("""
Diagnostic analytics attempts to determine:

    WHY DID IT HAPPEN?

Suppose sales declined.

Descriptive analytics:
    Sales declined by 20%.

Diagnostic analytics:
    Sales declined because:
        - Website traffic decreased.
        - Product availability declined.
        - Marketing spending was reduced.
        - Competitor pricing changed.

Common diagnostic techniques:

    - Drill-down analysis
    - Comparison
    - Segmentation
    - Correlation analysis
    - Root-cause analysis
    - Variance analysis
    - Cohort analysis
    - Funnel analysis
""")


# ============================================================
# SECTION 11: SIMPLE DIAGNOSTIC EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("11. DIAGNOSTIC ANALYSIS EXAMPLE")
print("=" * 70)

months = ["January", "February", "March", "April"]

sales = [100000, 110000, 70000, 105000]
website_visits = [10000, 11000, 6000, 10500]

for month, sale, visits in zip(months, sales, website_visits):
    print(
        f"{month:10} | Sales = {sale:>7} | Visits = {visits:>5}"
    )

print("""
Notice:

March has significantly lower website traffic and
significantly lower sales.

This creates a possible diagnostic hypothesis:

    Lower traffic may have contributed to lower sales.

But this alone does not prove causation.

Additional investigation is required.
""")


# ============================================================
# SECTION 12: PREDICTIVE ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("12. PREDICTIVE ANALYTICS")
print("=" * 70)

print("""
Predictive analytics attempts to estimate future outcomes.

Primary question:

    WHAT IS LIKELY TO HAPPEN?

Examples:

    - Forecast next month's sales
    - Predict customer churn
    - Estimate demand
    - Predict loan default risk
    - Forecast inventory requirements
    - Predict equipment failure

Predictive analytics often uses:

    - Statistics
    - Regression
    - Time-series analysis
    - Machine learning
    - Classification
    - Forecasting

Important:

A prediction is not a guarantee.

Predictions contain uncertainty.
""")


# ============================================================
# SECTION 13: SIMPLE FORECASTING EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("13. SIMPLE PREDICTION EXAMPLE")
print("=" * 70)

historical_sales = [100, 110, 120, 130, 140]

print("Historical sales:", historical_sales)

average_growth = (
    (historical_sales[-1] - historical_sales[0])
    / (len(historical_sales) - 1)
)

next_month_prediction = historical_sales[-1] + average_growth

print("Estimated average monthly increase:", average_growth)
print("Simple next-month prediction:", next_month_prediction)

print("""
This is an extremely simple forecasting technique.

Real predictive analytics may use:

    - Multiple variables
    - Seasonality
    - Trends
    - Historical patterns
    - Regression models
    - Machine learning models
    - External variables

The quality of a prediction depends heavily on
the quality and relevance of the data.
""")


# ============================================================
# SECTION 14: PRESCRIPTIVE ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("14. PRESCRIPTIVE ANALYTICS")
print("=" * 70)

print("""
Prescriptive analytics attempts to determine:

    WHAT SHOULD WE DO?

It goes beyond predicting an outcome.

Example:

Predictive:
    Sales may decline by 10%.

Prescriptive:
    Increase marketing spending by 15%,
    adjust pricing,
    and increase inventory in high-demand regions.

Prescriptive analytics may involve:

    - Optimization
    - Simulation
    - Scenario analysis
    - Decision models
    - Mathematical programming
    - Constraint optimization
    - Recommendation systems
""")


# ============================================================
# SECTION 15: SIMPLE PRESCRIPTIVE EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("15. PRESCRIPTIVE DECISION EXAMPLE")
print("=" * 70)

inventory = 80
expected_demand = 120

shortage = expected_demand - inventory

print("Current inventory:", inventory)
print("Expected demand:", expected_demand)
print("Potential shortage:", shortage)

if shortage > 0:
    print(
        "Recommendation: Increase inventory by at least",
        shortage,
        "units."
    )
else:
    print("Recommendation: Current inventory may be sufficient.")


# ============================================================
# SECTION 16: FOUR TYPES TOGETHER
# ============================================================

print("\n" + "=" * 70)
print("16. DESCRIPTIVE -> DIAGNOSTIC -> PREDICTIVE -> PRESCRIPTIVE")
print("=" * 70)

print("""
Business problem:

Sales are declining.

DESCRIPTIVE:
    What happened?
    Sales declined by 15%.

DIAGNOSTIC:
    Why did it happen?
    Website traffic and conversion rate declined.

PREDICTIVE:
    What may happen?
    Sales may decline another 8% next month.

PRESCRIPTIVE:
    What should we do?
    Improve acquisition campaigns, optimize the checkout
    experience, and focus on high-converting customer segments.

The four forms of analytics can work together.
""")


# ============================================================
# SECTION 17: ANALYTICS MATURITY
# ============================================================

print("\n" + "=" * 70)
print("17. ANALYTICS MATURITY")
print("=" * 70)

maturity = [
    ("Level 1", "Descriptive", "What happened?"),
    ("Level 2", "Diagnostic", "Why did it happen?"),
    ("Level 3", "Predictive", "What may happen?"),
    ("Level 4", "Prescriptive", "What should we do?")
]

for level, analytics, question in maturity:
    print(f"{level}: {analytics:15} | {question}")


# ============================================================
# SECTION 18: ANALYTICS LIFECYCLE
# ============================================================

print("\n" + "=" * 70)
print("18. DATA ANALYTICS LIFECYCLE")
print("=" * 70)

lifecycle = [
    "1. Define the business problem",
    "2. Define analytical objectives",
    "3. Identify required data",
    "4. Collect data",
    "5. Store and organize data",
    "6. Clean data",
    "7. Transform data",
    "8. Explore data",
    "9. Analyze data",
    "10. Visualize results",
    "11. Interpret findings",
    "12. Communicate insights",
    "13. Recommend action",
    "14. Implement decision",
    "15. Monitor outcomes",
    "16. Iterate"
]

for step in lifecycle:
    print(step)


# ============================================================
# SECTION 19: BUSINESS PROBLEM
# ============================================================

print("\n" + "=" * 70)
print("19. BUSINESS PROBLEM VS DATA PROBLEM")
print("=" * 70)

print("""
BUSINESS PROBLEM:

    "Why are our customers leaving?"

DATA PROBLEM:

    "Can we identify customer characteristics associated
     with churn?"

ANALYTICAL QUESTION:

    "Which factors are associated with customer churn,
     and how do churn rates differ across customer segments?"

This distinction is extremely important.

A Data Analyst should understand the business problem
before starting technical analysis.
""")


# ============================================================
# SECTION 20: STRUCTURED DATA
# ============================================================

print("\n" + "=" * 70)
print("20. STRUCTURED DATA")
print("=" * 70)

print("""
Structured data follows a defined schema.

Examples:

    Customer ID
    Name
    Age
    City
    Revenue
    Purchase Date

Typical structured data formats:

    - Excel spreadsheets
    - CSV files
    - SQL tables
    - Relational databases

Example:
""")

customer = {
    "customer_id": 101,
    "age": 30,
    "city": "Lucknow",
    "revenue": 25000
}

for key, value in customer.items():
    print(f"{key:15}: {value}")


# ============================================================
# SECTION 21: UNSTRUCTURED DATA
# ============================================================

print("\n" + "=" * 70)
print("21. UNSTRUCTURED DATA")
print("=" * 70)

print("""
Unstructured data does not naturally fit into traditional
rows and columns.

Examples:

    - Images
    - Videos
    - Audio
    - Emails
    - Documents
    - Social media posts
    - Customer reviews

Analytics of unstructured data may require techniques such as:

    - Natural Language Processing
    - Computer Vision
    - Speech Processing
    - Embeddings
    - Machine Learning
""")


# ============================================================
# SECTION 22: QUALITATIVE VS QUANTITATIVE DATA
# ============================================================

print("\n" + "=" * 70)
print("22. QUALITATIVE VS QUANTITATIVE DATA")
print("=" * 70)

print("""
QUALITATIVE DATA
----------------
Describes characteristics or categories.

Examples:

    Gender category
    Product type
    Customer feedback
    City
    Satisfaction level

QUANTITATIVE DATA
-----------------
Represents measurable quantities.

Examples:

    Age
    Revenue
    Quantity
    Salary
    Temperature
    Profit
""")


# ============================================================
# SECTION 23: DISCRETE VS CONTINUOUS DATA
# ============================================================

print("\n" + "=" * 70)
print("23. DISCRETE VS CONTINUOUS DATA")
print("=" * 70)

print("""
DISCRETE DATA

Countable values.

Examples:

    Number of customers
    Number of products
    Number of complaints

Example:
    10 customers
    11 customers
    12 customers

CONTINUOUS DATA

Can take values within a range.

Examples:

    Height
    Weight
    Temperature
    Time
    Distance

Example:

    70.2 kg
    70.25 kg
    70.257 kg
""")


# ============================================================
# SECTION 24: DIMENSIONS AND MEASURES
# ============================================================

print("\n" + "=" * 70)
print("24. DIMENSIONS AND MEASURES")
print("=" * 70)

print("""
DIMENSIONS describe characteristics.

Examples:

    Region
    Product
    Customer
    Department
    Date

MEASURES represent numerical values.

Examples:

    Revenue
    Profit
    Quantity
    Cost
    Sales

Example:

    Region = North
    Product = Laptop
    Revenue = 500000

Region and Product are dimensions.

Revenue is a measure.
""")


# ============================================================
# SECTION 25: METRICS
# ============================================================

print("\n" + "=" * 70)
print("25. METRICS")
print("=" * 70)

print("""
A metric is a measurable value used to evaluate
performance or behavior.

Examples:

    Revenue
    Profit
    Customer count
    Conversion rate
    Retention rate
    Churn rate
    Average order value
""")


# ============================================================
# SECTION 26: KPI
# ============================================================

print("\n" + "=" * 70)
print("26. KEY PERFORMANCE INDICATORS")
print("=" * 70)

print("""
A KPI is a metric that is specifically tied to an important
business objective.

Example:

Business objective:
    Increase customer retention.

Possible KPI:
    Customer retention rate.

A metric is not automatically a KPI.

A KPI must have strategic relevance.
""")


# ============================================================
# SECTION 27: CALCULATING BASIC BUSINESS METRICS
# ============================================================

print("\n" + "=" * 70)
print("27. BASIC BUSINESS METRICS")
print("=" * 70)

revenue = 500000
cost = 350000
customers = 1000
orders = 1250

profit = revenue - cost
average_revenue_per_customer = revenue / customers
average_order_value = revenue / orders
profit_margin = (profit / revenue) * 100

print("Revenue:", revenue)
print("Cost:", cost)
print("Profit:", profit)
print("Revenue per customer:", average_revenue_per_customer)
print("Average order value:", average_order_value)
print("Profit margin:", round(profit_margin, 2), "%")


# ============================================================
# SECTION 28: CONVERSION RATE
# ============================================================

print("\n" + "=" * 70)
print("28. CONVERSION RATE")
print("=" * 70)

website_visitors = 10000
buyers = 450

conversion_rate = (buyers / website_visitors) * 100

print("Visitors:", website_visitors)
print("Buyers:", buyers)
print("Conversion rate:", round(conversion_rate, 2), "%")


# ============================================================
# SECTION 29: CHURN RATE
# ============================================================

print("\n" + "=" * 70)
print("29. CHURN RATE")
print("=" * 70)

customers_start = 5000
customers_lost = 250

churn_rate = (customers_lost / customers_start) * 100

print("Customers at beginning:", customers_start)
print("Customers lost:", customers_lost)
print("Churn rate:", round(churn_rate, 2), "%")


# ============================================================
# SECTION 30: GROWTH RATE
# ============================================================

print("\n" + "=" * 70)
print("30. GROWTH RATE")
print("=" * 70)

old_value = 100000
new_value = 125000

growth_rate = ((new_value - old_value) / old_value) * 100

print("Old value:", old_value)
print("New value:", new_value)
print("Growth rate:", round(growth_rate, 2), "%")


# ============================================================
# SECTION 31: DATA EXPLORATION
# ============================================================

print("\n" + "=" * 70)
print("31. BASIC DATA EXPLORATION")
print("=" * 70)

data = [12, 15, 18, 20, 20, 22, 25, 30, 35]

print("Dataset:", data)
print("Number of observations:", len(data))
print("Minimum:", min(data))
print("Maximum:", max(data))
print("Total:", sum(data))
print("Mean:", sum(data) / len(data))


# ============================================================
# SECTION 32: MEDIAN
# ============================================================

print("\n" + "=" * 70)
print("32. MEDIAN")
print("=" * 70)

sorted_data = sorted(data)

middle = len(sorted_data) // 2

if len(sorted_data) % 2 == 1:
    median = sorted_data[middle]
else:
    median = (
        sorted_data[middle - 1] +
        sorted_data[middle]
    ) / 2

print("Sorted data:", sorted_data)
print("Median:", median)

print("""
The median represents the middle value after sorting.

Median is useful when extreme values can distort the mean.
""")


# ============================================================
# SECTION 33: RANGE
# ============================================================

print("\n" + "=" * 70)
print("33. RANGE")
print("=" * 70)

data_range = max(data) - min(data)

print("Range:", data_range)

print("""
Range = Maximum - Minimum

It provides a simple measure of how spread out
the observations are.
""")


# ============================================================
# SECTION 34: OUTLIERS
# ============================================================

print("\n" + "=" * 70)
print("34. OUTLIERS")
print("=" * 70)

customer_orders = [10, 12, 11, 13, 12, 14, 500]

print("Customer orders:", customer_orders)

average = sum(customer_orders) / len(customer_orders)

print("Mean:", round(average, 2))

print("""
The value 500 is much larger than the other observations.

It may be an outlier.

But an outlier is not automatically an error.

Possible explanations:

    - Data entry mistake
    - Fraud
    - Special customer
    - Bulk purchase
    - Genuine extreme event

An analyst should investigate before deleting it.
""")


# ============================================================
# SECTION 35: MISSING DATA
# ============================================================

print("\n" + "=" * 70)
print("35. MISSING DATA")
print("=" * 70)

customer_ages = [25, 30, None, 42, 35, None, 28]

print("Customer ages:", customer_ages)

missing_count = customer_ages.count(None)

print("Missing values:", missing_count)

print("""
Missing data may occur because:

    - Customer did not provide information
    - System failure
    - Data integration problem
    - Incorrect data collection
    - Field was optional
    - Data was lost

Possible approaches:

    - Remove records
    - Replace values
    - Use mean/median/mode
    - Use model-based imputation
    - Keep missing as a category
    - Investigate the source
""")


# ============================================================
# SECTION 36: DUPLICATE DATA
# ============================================================

print("\n" + "=" * 70)
print("36. DUPLICATE DATA")
print("=" * 70)

customer_ids = [101, 102, 103, 103, 104, 105, 105]

unique_ids = set(customer_ids)

print("Customer IDs:", customer_ids)
print("Unique IDs:", unique_ids)

duplicates = len(customer_ids) - len(unique_ids)

print("Potential duplicate records:", duplicates)

print("""
Duplicates can distort:

    - Customer counts
    - Revenue
    - Orders
    - Conversion rates
    - Average values

Therefore, duplicate detection is an important
data-cleaning activity.
""")


# ============================================================
# SECTION 37: CORRELATION VS CAUSATION
# ============================================================

print("\n" + "=" * 70)
print("37. CORRELATION VS CAUSATION")
print("=" * 70)

print("""
CORRELATION

Two variables change together.

Example:

    Advertising spending increases.
    Sales also increase.

This may indicate a relationship.

CAUSATION

One variable directly contributes to a change
in another variable.

Important:

    CORRELATION DOES NOT AUTOMATICALLY MEAN CAUSATION.

Other factors may influence both variables.

For example:

    Advertising increases
    Sales increase
    Holiday season occurs

The holiday season may influence both advertising
and sales.

Therefore, an analyst must avoid jumping from
association to causal conclusions.
""")


# ============================================================
# SECTION 38: SPURIOUS CORRELATION
# ============================================================

print("\n" + "=" * 70)
print("38. SPURIOUS CORRELATION")
print("=" * 70)

print("""
A spurious correlation occurs when two variables appear
related even though there is no meaningful causal relationship.

This can happen because:

    - Coincidence
    - Confounding variables
    - Selection effects
    - Time trends
    - Small samples

Analysts should always ask:

    "What else could explain this relationship?"
""")


# ============================================================
# SECTION 39: SAMPLE VS POPULATION
# ============================================================

print("\n" + "=" * 70)
print("39. POPULATION VS SAMPLE")
print("=" * 70)

print("""
POPULATION

The complete group being studied.

Example:
    Every customer of a company.

SAMPLE

A subset of that population.

Example:
    5,000 customers selected from all customers.

Analytics frequently uses samples because studying
an entire population may be expensive, slow, or impossible.

A good sample should be appropriately selected and
representative of the population for the intended analysis.
""")


# ============================================================
# SECTION 40: BUSINESS QUESTIONS
# ============================================================

print("\n" + "=" * 70)
print("40. TURNING BUSINESS QUESTIONS INTO ANALYTICAL QUESTIONS")
print("=" * 70)

print("""
Weak question:

    "Tell me something interesting about sales."

Better question:

    "Which products generated the most revenue?"

Even better:

    "Which products generated the highest revenue
     during the last six months, and how did their
     growth compare with the previous six months?"

Strong analytical questions should be:

    - Specific
    - Measurable
    - Relevant
    - Answerable using available data
    - Connected to a decision
""")


# ============================================================
# SECTION 41: EXCEL IN DATA ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("41. EXCEL FOR DATA ANALYTICS")
print("=" * 70)

print("""
Excel is widely used for:

    - Data entry
    - Data cleaning
    - Sorting
    - Filtering
    - Formulas
    - Conditional formatting
    - Pivot tables
    - Charts
    - Basic statistical analysis
    - Reporting
    - Dashboard creation

Important Excel concepts include:

    Cells
    Rows
    Columns
    Tables
    Formulas
    Functions
    Pivot Tables
    Pivot Charts
    Power Query
    Power Pivot
""")


# ============================================================
# SECTION 42: IMPORTANT EXCEL FUNCTIONS
# ============================================================

print("\n" + "=" * 70)
print("42. IMPORTANT EXCEL FUNCTIONS")
print("=" * 70)

excel_functions = [
    "SUM()",
    "AVERAGE()",
    "MIN()",
    "MAX()",
    "COUNT()",
    "COUNTA()",
    "COUNTIF()",
    "COUNTIFS()",
    "SUMIF()",
    "SUMIFS()",
    "AVERAGEIF()",
    "AVERAGEIFS()",
    "IF()",
    "IFS()",
    "AND()",
    "OR()",
    "XLOOKUP()",
    "INDEX()",
    "MATCH()",
    "TEXT()",
    "LEFT()",
    "RIGHT()",
    "MID()",
    "TRIM()",
    "CONCAT()"
]

for function in excel_functions:
    print(function)


# ============================================================
# SECTION 43: PYTHON FOR DATA ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("43. PYTHON FOR DATA ANALYTICS")
print("=" * 70)

print("""
Python is a programming language widely used for
data analysis and data science.

Common Python libraries include:

    NumPy
        Numerical computing

    pandas
        Data manipulation and analysis

    Matplotlib
        Visualization

    Seaborn
        Statistical visualization

    SciPy
        Scientific computing and statistics

    scikit-learn
        Machine learning

    statsmodels
        Statistical modeling

Python is particularly useful when:

    - Datasets become large
    - Analysis must be repeated
    - Automation is required
    - Complex transformations are needed
    - Multiple datasets must be combined
    - Statistical or machine-learning models are required
""")


# ============================================================
# SECTION 44: JUPYTER NOTEBOOK
# ============================================================

print("\n" + "=" * 70)
print("44. JUPYTER NOTEBOOK")
print("=" * 70)

print("""
Jupyter Notebook is an interactive environment commonly
used for data analysis.

A notebook can contain:

    - Python code
    - Explanatory text
    - Markdown
    - Tables
    - Charts
    - Mathematical expressions
    - Output

Typical analytical workflow:

    Markdown explanation
            |
            v
    Python code
            |
            v
    Output
            |
            v
    Interpretation
            |
            v
    Next analysis

This makes Jupyter especially useful for
exploratory data analysis and learning.
""")


# ============================================================
# SECTION 45: SIMPLE DATASET
# ============================================================

print("\n" + "=" * 70)
print("45. SIMPLE BUSINESS DATASET")
print("=" * 70)

employees = [
    {
        "name": "A",
        "department": "Sales",
        "salary": 50000,
        "performance": 80
    },
    {
        "name": "B",
        "department": "Sales",
        "salary": 55000,
        "performance": 90
    },
    {
        "name": "C",
        "department": "Marketing",
        "salary": 60000,
        "performance": 85
    },
    {
        "name": "D",
        "department": "Finance",
        "salary": 65000,
        "performance": 88
    }
]

for employee in employees:
    print(employee)


# ============================================================
# SECTION 46: FILTERING DATA
# ============================================================

print("\n" + "=" * 70)
print("46. FILTERING DATA")
print("=" * 70)

sales_employees = [
    employee
    for employee in employees
    if employee["department"] == "Sales"
]

print("Sales employees:")

for employee in sales_employees:
    print(employee)


# ============================================================
# SECTION 47: AGGREGATION
# ============================================================

print("\n" + "=" * 70)
print("47. AGGREGATION")
print("=" * 70)

total_salary = sum(
    employee["salary"]
    for employee in employees
)

average_salary = total_salary / len(employees)

average_performance = (
    sum(employee["performance"] for employee in employees)
    / len(employees)
)

print("Total salary:", total_salary)
print("Average salary:", average_salary)
print("Average performance:", average_performance)


# ============================================================
# SECTION 48: SEGMENTATION
# ============================================================

print("\n" + "=" * 70)
print("48. SEGMENTATION")
print("=" * 70)

print("""
Segmentation means dividing data into meaningful groups.

Possible segments:

    - Geography
    - Age
    - Customer type
    - Product category
    - Income
    - Acquisition channel
    - Department
    - Experience level

Segmentation helps analysts identify differences
that may be hidden inside aggregate numbers.
""")


departments = {}

for employee in employees:

    department = employee["department"]

    if department not in departments:
        departments[department] = []

    departments[department].append(employee["performance"])

for department, performances in departments.items():

    average_performance = (
        sum(performances) / len(performances)
    )

    print(
        department,
        "average performance:",
        round(average_performance, 2)
    )


# ============================================================
# SECTION 49: TREND ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("49. TREND ANALYSIS")
print("=" * 70)

monthly_revenue = [
    100000,
    105000,
    110000,
    108000,
    115000,
    125000
]

print("Monthly revenue:", monthly_revenue)

for i in range(1, len(monthly_revenue)):

    change = monthly_revenue[i] - monthly_revenue[i - 1]

    print(
        f"Month {i + 1}: change = {change}"
    )

print("""
Trend analysis examines how a metric changes over time.

Questions include:

    - Is revenue increasing?
    - Is growth accelerating?
    - Is there seasonality?
    - When did performance change?
    - Are there unusual periods?
""")


# ============================================================
# SECTION 50: VARIANCE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("50. VARIANCE ANALYSIS")
print("=" * 70)

budget = 1000000
actual = 920000

variance = actual - budget
variance_percentage = (variance / budget) * 100

print("Budget:", budget)
print("Actual:", actual)
print("Variance:", variance)
print("Variance %:", round(variance_percentage, 2), "%")

print("""
Variance analysis compares actual results against
a reference value such as:

    - Budget
    - Forecast
    - Target
    - Previous period
    - Benchmark
""")


# ============================================================
# SECTION 51: DATA QUALITY
# ============================================================

print("\n" + "=" * 70)
print("51. DATA QUALITY")
print("=" * 70)

print("""
Important dimensions of data quality include:

1. Accuracy
   Is the value correct?

2. Completeness
   Is required information present?

3. Consistency
   Does data agree across systems?

4. Validity
   Does the value follow required rules?

5. Uniqueness
   Are duplicate records avoided?

6. Timeliness
   Is the data sufficiently current?

Bad data can produce bad analysis.

A technically correct calculation performed on
poor-quality data can still produce a misleading result.
""")


# ============================================================
# SECTION 52: DATA CLEANING MINDSET
# ============================================================

print("\n" + "=" * 70)
print("52. DATA CLEANING MINDSET")
print("=" * 70)

print("""
Before analyzing data, check:

    [ ] Missing values
    [ ] Duplicate records
    [ ] Invalid values
    [ ] Incorrect data types
    [ ] Inconsistent spelling
    [ ] Impossible values
    [ ] Outliers
    [ ] Date problems
    [ ] Currency inconsistencies
    [ ] Unit inconsistencies
    [ ] Unexpected categories
    [ ] Data-source mismatches
""")


# ============================================================
# SECTION 53: DATA TYPES IN PYTHON
# ============================================================

print("\n" + "=" * 70)
print("53. PYTHON DATA TYPES")
print("=" * 70)

integer_value = 100
float_value = 99.99
text_value = "Analytics"
boolean_value = True
list_value = [1, 2, 3]
dictionary_value = {"sales": 100000}

print(type(integer_value))
print(type(float_value))
print(type(text_value))
print(type(boolean_value))
print(type(list_value))
print(type(dictionary_value))


# ============================================================
# SECTION 54: ANALYTICAL FUNCTIONS
# ============================================================

print("\n" + "=" * 70)
print("54. CREATING REUSABLE ANALYTICAL FUNCTIONS")
print("=" * 70)


def calculate_growth(old_value, new_value):
    """
    Calculate percentage growth.
    """

    if old_value == 0:
        return None

    return ((new_value - old_value) / old_value) * 100


def calculate_profit(revenue, cost):
    """
    Calculate profit.
    """

    return revenue - cost


def calculate_margin(revenue, profit):
    """
    Calculate profit margin.
    """

    if revenue == 0:
        return None

    return (profit / revenue) * 100


revenue = 500000
cost = 350000

profit = calculate_profit(revenue, cost)
margin = calculate_margin(revenue, profit)
growth = calculate_growth(400000, revenue)

print("Profit:", profit)
print("Margin:", round(margin, 2), "%")
print("Growth:", round(growth, 2), "%")


# ============================================================
# SECTION 55: ANALYTICAL THINKING EXERCISE
# ============================================================

print("\n" + "=" * 70)
print("55. ANALYTICAL THINKING EXERCISE")
print("=" * 70)

products = {
    "Laptop": {
        "sales": 1000000,
        "units": 100
    },
    "Phone": {
        "sales": 800000,
        "units": 200
    },
    "Tablet": {
        "sales": 450000,
        "units": 150
    }
}

print("Product performance:")

for product, values in products.items():

    average_price = values["sales"] / values["units"]

    print(
        f"{product:10} | "
        f"Revenue={values['sales']:>8} | "
        f"Units={values['units']:>4} | "
        f"Avg Price={average_price:>8.2f}"
    )

print("""
Now ask analytical questions:

1. Which product generated the highest revenue?
2. Which product sold the most units?
3. Which product had the highest average price?
4. Does higher unit volume necessarily mean higher revenue?
5. Should the company prioritize revenue, units,
   margin, or another KPI?

This demonstrates an important principle:

    The answer depends on the business objective.
""")


# ============================================================
# SECTION 56: DECISION TREE FOR ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("56. WHICH TYPE OF ANALYTICS SHOULD YOU USE?")
print("=" * 70)


def analytics_type(question):

    question = question.lower()

    if "what happened" in question:
        return "Descriptive Analytics"

    elif "why" in question:
        return "Diagnostic Analytics"

    elif "predict" in question or "forecast" in question:
        return "Predictive Analytics"

    elif "should" in question or "recommend" in question:
        return "Prescriptive Analytics"

    return "Question requires further clarification."


questions = [
    "What happened to sales?",
    "Why did sales fall?",
    "What will sales be next month?",
    "What should we do to improve sales?"
]

for question in questions:

    print(
        f"{question:40} -> "
        f"{analytics_type(question)}"
    )


# ============================================================
# SECTION 57: REAL-WORLD APPLICATIONS
# ============================================================

print("\n" + "=" * 70)
print("57. REAL-WORLD APPLICATIONS OF DATA ANALYTICS")
print("=" * 70)

applications = {
    "Banking": [
        "Fraud detection",
        "Credit risk",
        "Customer segmentation",
        "Transaction analysis"
    ],

    "Healthcare": [
        "Patient analytics",
        "Hospital resource planning",
        "Treatment outcome analysis",
        "Operational analytics"
    ],

    "Retail": [
        "Demand forecasting",
        "Inventory optimization",
        "Customer segmentation",
        "Product analysis"
    ],

    "Marketing": [
        "Campaign analysis",
        "Conversion analysis",
        "Customer acquisition",
        "Marketing attribution"
    ],

    "Manufacturing": [
        "Quality control",
        "Predictive maintenance",
        "Production optimization",
        "Supply-chain analytics"
    ],

    "Sports": [
        "Player performance",
        "Team strategy",
        "Injury analysis",
        "Game statistics"
    ],

    "Government": [
        "Public-service analytics",
        "Resource allocation",
        "Population analysis",
        "Policy evaluation"
    ],

    "Cybersecurity": [
        "Threat detection",
        "Anomaly detection",
        "Incident analysis",
        "Security monitoring"
    ]
}

for industry, uses in applications.items():

    print(f"\n{industry}:")

    for use in uses:
        print("   -", use)


# ============================================================
# SECTION 58: ANALYTICS IN BUSINESS
# ============================================================

print("\n" + "=" * 70)
print("58. DATA ANALYTICS IN BUSINESS")
print("=" * 70)

print("""
A modern organization can use analytics across:

MARKETING
    Who are our customers?
    Which campaigns work?

SALES
    Which products sell?
    Which regions perform best?

FINANCE
    Where is money being spent?
    Are we meeting budgets?

OPERATIONS
    Where are bottlenecks?

HUMAN RESOURCES
    What affects employee retention?

PRODUCT
    Which features are used?

CUSTOMER SERVICE
    What causes complaints?

SUPPLY CHAIN
    How much inventory should we maintain?

EXECUTIVE MANAGEMENT
    Are strategic objectives being achieved?
""")


# ============================================================
# SECTION 59: ANALYTICS AND DECISION-MAKING
# ============================================================

print("\n" + "=" * 70)
print("59. DATA-DRIVEN DECISION MAKING")
print("=" * 70)

print("""
Data-driven decision-making means using evidence,
measurements, analysis, and relevant information
to improve decisions.

This does NOT mean:

    "Ignore human judgment."

Instead:

    DATA + CONTEXT + EXPERIENCE + JUDGMENT
                     |
                     v
                 DECISION

Data can inform decisions, but analysts must understand:

    - Business context
    - Data limitations
    - Uncertainty
    - Assumptions
    - Risks
    - Human factors
""")


# ============================================================
# SECTION 60: COMMON ANALYTICAL MISTAKES
# ============================================================

print("\n" + "=" * 70)
print("60. COMMON DATA ANALYTICS MISTAKES")
print("=" * 70)

mistakes = [
    "Starting analysis without understanding the business problem",
    "Using poor-quality data",
    "Ignoring missing values",
    "Ignoring duplicates",
    "Treating correlation as causation",
    "Using inappropriate metrics",
    "Choosing misleading visualizations",
    "Ignoring sample bias",
    "Overfitting conclusions",
    "Cherry-picking results",
    "Ignoring contradictory evidence",
    "Confusing statistical significance with business importance",
    "Assuming historical patterns always continue",
    "Failing to communicate assumptions",
    "Presenting numbers without context"
]

for number, mistake in enumerate(mistakes, start=1):
    print(f"{number:02d}. {mistake}")


# ============================================================
# SECTION 61: DATA ANALYST VS DATA SCIENTIST
# ============================================================

print("\n" + "=" * 70)
print("61. DATA ANALYST VS DATA SCIENTIST")
print("=" * 70)

print("""
DATA ANALYST

Typical focus:

    - Reporting
    - Dashboards
    - SQL
    - Excel
    - Business analysis
    - Exploratory analysis
    - KPIs
    - Descriptive and diagnostic analytics

DATA SCIENTIST

Typical focus:

    - Predictive modeling
    - Machine learning
    - Statistical modeling
    - Feature engineering
    - Experimentation
    - Advanced forecasting
    - Optimization

There is significant overlap.

The exact responsibilities depend on the organization.
""")


# ============================================================
# SECTION 62: DATA ANALYST VS BUSINESS ANALYST
# ============================================================

print("\n" + "=" * 70)
print("62. DATA ANALYST VS BUSINESS ANALYST")
print("=" * 70)

print("""
DATA ANALYST:

    More heavily focused on:
        - Data
        - Metrics
        - Analysis
        - SQL
        - Visualization
        - Statistical reasoning

BUSINESS ANALYST:

    More heavily focused on:
        - Business requirements
        - Processes
        - Stakeholders
        - Requirements gathering
        - Process improvement
        - Business solutions

The boundaries can overlap significantly.
""")


# ============================================================
# SECTION 63: THE ANALYTICAL STACK
# ============================================================

print("\n" + "=" * 70)
print("63. DATA ANALYTICS TOOL STACK")
print("=" * 70)

tool_stack = {
    "Spreadsheet": "Excel",
    "Programming": "Python",
    "Notebook": "Jupyter",
    "Database": "SQL / PostgreSQL",
    "Data Manipulation": "pandas",
    "Numerical Computing": "NumPy",
    "Visualization": "Matplotlib / Seaborn",
    "BI": "Power BI / Tableau",
    "Version Control": "Git / GitHub"
}

for category, tool in tool_stack.items():
    print(f"{category:22}: {tool}")


# ============================================================
# SECTION 64: MINI END-TO-END ANALYTICS PROJECT
# ============================================================

print("\n" + "=" * 70)
print("64. MINI END-TO-END ANALYTICS PROJECT")
print("=" * 70)

print("""
BUSINESS PROBLEM:

    A company wants to understand monthly sales performance.

STEP 1:
    Collect sales data.

STEP 2:
    Check data quality.

STEP 3:
    Calculate total sales.

STEP 4:
    Calculate average sales.

STEP 5:
    Identify best and worst months.

STEP 6:
    Calculate growth.

STEP 7:
    Investigate unusual changes.

STEP 8:
    Identify possible causes.

STEP 9:
    Forecast future sales.

STEP 10:
    Recommend business actions.

STEP 11:
    Present findings.

STEP 12:
    Monitor whether the recommendation worked.
""")


monthly_sales = {
    "January": 100000,
    "February": 115000,
    "March": 90000,
    "April": 130000,
    "May": 145000,
    "June": 155000
}

total = sum(monthly_sales.values())
average = total / len(monthly_sales)

best_month = max(
    monthly_sales,
    key=monthly_sales.get
)

worst_month = min(
    monthly_sales,
    key=monthly_sales.get
)

growth = calculate_growth(
    monthly_sales["January"],
    monthly_sales["June"]
)

print("Total sales:", total)
print("Average monthly sales:", average)
print("Best month:", best_month)
print("Worst month:", worst_month)
print("January to June growth:", round(growth, 2), "%")


# ============================================================
# SECTION 65: INTERPRETING THE MINI PROJECT
# ============================================================

print("\n" + "=" * 70)
print("65. INTERPRETING THE RESULTS")
print("=" * 70)

print("""
Possible descriptive insight:

    Sales generally increased from January to June,
    although March experienced a decline.

Possible diagnostic question:

    Why did March sales fall?

Possible predictive question:

    If the current trend continues, what might
    July sales look like?

Possible prescriptive question:

    What actions should the company take to sustain
    growth and avoid another March-like decline?

This is how an analyst moves from:

    DATA
      ->
    INFORMATION
      ->
    INSIGHT
      ->
    DECISION
      ->
    ACTION
""")


# ============================================================
# SECTION 66: ANALYTICAL COMMUNICATION
# ============================================================

print("\n" + "=" * 70)
print("66. COMMUNICATING ANALYTICAL INSIGHTS")
print("=" * 70)

print("""
A strong analytical presentation should answer:

1. What happened?
2. Why does it matter?
3. What caused or contributed to it?
4. What evidence supports the conclusion?
5. What are the limitations?
6. What should happen next?

Weak communication:

    "Sales were 155,000 in June."

Strong communication:

    "June generated the highest monthly sales at 155,000,
    representing a substantial increase from January.
    The sustained upward trend should be investigated to
    identify which products, regions, channels, or campaigns
    contributed to the improvement."
""")


# ============================================================
# SECTION 67: DATA ANALYTICS PYRAMID
# ============================================================

print("\n" + "=" * 70)
print("67. DATA ANALYTICS PYRAMID")
print("=" * 70)

print("""
                    DECISION
                       ^
                       |
                    ACTION
                       ^
                       |
                    INSIGHT
                       ^
                       |
                    ANALYSIS
                       ^
                       |
                  INFORMATION
                       ^
                       |
                     DATA

The higher you move in the pyramid,
the more interpretation and business context are required.
""")


# ============================================================
# SECTION 68: FINAL KNOWLEDGE CHECK
# ============================================================

print("\n" + "=" * 70)
print("68. FINAL KNOWLEDGE CHECK")
print("=" * 70)

questions = [
    "What is data analytics?",
    "What is the difference between data and information?",
    "What is the difference between information and knowledge?",
    "What does a Data Analyst do?",
    "What is descriptive analytics?",
    "What is diagnostic analytics?",
    "What is predictive analytics?",
    "What is prescriptive analytics?",
    "What is the analytics lifecycle?",
    "What is structured data?",
    "What is unstructured data?",
    "What is a metric?",
    "What is a KPI?",
    "What is an outlier?",
    "What is missing data?",
    "Why does data quality matter?",
    "What is correlation?",
    "Why does correlation not necessarily imply causation?",
    "What is segmentation?",
    "What is trend analysis?",
    "How can Excel be used for analytics?",
    "How can Python be used for analytics?",
    "Why is Jupyter useful for analytics?"
]

for number, question in enumerate(questions, start=1):
    print(f"{number:02d}. {question}")


# ============================================================
# SECTION 69: KEY TAKEAWAYS
# ============================================================

print("\n" + "=" * 70)
print("69. KEY TAKEAWAYS")
print("=" * 70)

takeaways = [
    "Data is raw material for analysis.",
    "Information is organized data with context.",
    "Knowledge is understanding derived from information.",
    "Analytics converts data into useful insights.",
    "Data Analysts connect business questions with data.",
    "Descriptive analytics explains what happened.",
    "Diagnostic analytics investigates why it happened.",
    "Predictive analytics estimates what may happen.",
    "Prescriptive analytics recommends what should be done.",
    "Data quality is fundamental to reliable analysis.",
    "Correlation does not automatically prove causation.",
    "Segmentation reveals differences hidden by averages.",
    "KPIs connect measurements to business objectives.",
    "Excel is powerful for spreadsheet-based analytics.",
    "Python enables scalable and programmable analysis.",
    "Jupyter provides an interactive analytical environment.",
    "Analytics should ultimately support better decisions."
]

for number, takeaway in enumerate(takeaways, start=1):
    print(f"{number:02d}. {takeaway}")


# ============================================================
# SECTION 70: COMPLETION
# ============================================================

print("\n" + "=" * 70)
print("DAY 01 COMPLETE")
print("=" * 70)

print("""
You have completed the introductory foundation of
Data Analytics.

You should now understand:

    DATA
      ->
    INFORMATION
      ->
    KNOWLEDGE
      ->
    ANALYSIS
      ->
    INSIGHT
      ->
    DECISION
      ->
    ACTION

The next stage of your learning journey should move
toward practical data handling, Excel analytics,
Python fundamentals for analytics, pandas, data cleaning,
SQL, visualization, statistics, and eventually
advanced analytics and machine learning.
""")

print("=" * 70)
print("END OF PROGRAM")
print("=" * 70)

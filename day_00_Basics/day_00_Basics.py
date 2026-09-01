# ============================================================
# DAY 00: DATA ANALYTICS FUNDAMENTALS
# ============================================================

print("DAY 01 - DATA ANALYTICS FUNDAMENTALS")


# ============================================================
# 1. WHAT IS DATA ANALYTICS?
# ============================================================

print("\n1. WHAT IS DATA ANALYTICS?")

print("Data Analytics is the process of examining data")
print("to discover patterns, understand performance,")
print("answer questions, and support decision-making.")

print("\nBasic Analytics Flow:")
print("Data -> Cleaning -> Analysis -> Insights -> Decision")


# ============================================================
# 2. WHAT IS DATA?
# ============================================================

print("\n2. WHAT IS DATA?")

data_examples = [
    "Customer names",
    "Sales transactions",
    "Product prices",
    "Website visits",
    "Employee records",
    "Survey responses"
]

for data in data_examples:
    print("-", data)


# ============================================================
# 3. DATASET
# ============================================================

print("\n3. DATASET")

dataset = [
    {"name": "Alice", "age": 25, "sales": 5000},
    {"name": "Bob", "age": 30, "sales": 7000},
    {"name": "Charlie", "age": 28, "sales": 6000},
    {"name": "David", "age": 35, "sales": 9000}
]

print("Number of records:", len(dataset))

for record in dataset:
    print(record)


# ============================================================
# 4. VARIABLES
# ============================================================

print("\n4. VARIABLES")

print("A variable represents a characteristic or attribute")
print("that can have different values.")

variables = {
    "Name": "Categorical",
    "Age": "Numerical",
    "Sales": "Numerical"
}

for variable, data_type in variables.items():
    print(variable, "->", data_type)


# ============================================================
# 5. DATA TYPES
# ============================================================

print("\n5. DATA TYPES")

data_types = [
    "Numerical",
    "Categorical",
    "Ordinal",
    "Boolean",
    "Date and Time",
    "Text"
]

for data_type in data_types:
    print("-", data_type)


# ============================================================
# 6. STRUCTURED AND UNSTRUCTURED DATA
# ============================================================

print("\n6. STRUCTURED AND UNSTRUCTURED DATA")

structured_data = [
    "Database tables",
    "Spreadsheets",
    "CSV files"
]

unstructured_data = [
    "Images",
    "Videos",
    "Audio",
    "Documents",
    "Social media content"
]

print("Structured Data:")

for item in structured_data:
    print("-", item)

print("\nUnstructured Data:")

for item in unstructured_data:
    print("-", item)


# ============================================================
# 7. DATA COLLECTION
# ============================================================

print("\n7. DATA COLLECTION")

data_sources = [
    "Databases",
    "APIs",
    "Surveys",
    "Web Applications",
    "Sensors",
    "Transaction Systems",
    "Spreadsheets"
]

for source in data_sources:
    print("-", source)


# ============================================================
# 8. DATA QUALITY
# ============================================================

print("\n8. DATA QUALITY")

quality_dimensions = [
    "Accuracy",
    "Completeness",
    "Consistency",
    "Validity",
    "Uniqueness",
    "Timeliness"
]

for dimension in quality_dimensions:
    print("-", dimension)


# ============================================================
# 9. MISSING DATA
# ============================================================

print("\n9. MISSING DATA")

sales_data = [5000, 7000, None, 9000, 6000]

print("Original Data:", sales_data)

missing_values = 0

for value in sales_data:

    if value is None:
        missing_values += 1

print("Missing Values:", missing_values)


# ============================================================
# 10. BASIC DATA CLEANING
# ============================================================

print("\n10. BASIC DATA CLEANING")

dirty_data = ["100", "200", "", "300", "400"]

clean_data = []

for value in dirty_data:

    if value != "":
        clean_data.append(int(value))

print("Original Data:", dirty_data)
print("Cleaned Data:", clean_data)


# ============================================================
# 11. DESCRIPTIVE STATISTICS
# ============================================================

print("\n11. DESCRIPTIVE STATISTICS")

sales = [5000, 7000, 6000, 9000, 8000]

total = sum(sales)
count = len(sales)
average = total / count

print("Sales:", sales)
print("Total:", total)
print("Count:", count)
print("Average:", average)


# ============================================================
# 12. MINIMUM AND MAXIMUM
# ============================================================

print("\n12. MINIMUM AND MAXIMUM")

print("Minimum:", min(sales))
print("Maximum:", max(sales))


# ============================================================
# 13. MEDIAN
# ============================================================

print("\n13. MEDIAN")

sorted_sales = sorted(sales)
n = len(sorted_sales)

if n % 2 == 1:
    median = sorted_sales[n // 2]
else:
    median = (
        sorted_sales[n // 2 - 1] +
        sorted_sales[n // 2]
    ) / 2

print("Sorted Sales:", sorted_sales)
print("Median:", median)


# ============================================================
# 14. RANGE
# ============================================================

print("\n14. RANGE")

data_range = max(sales) - min(sales)

print("Range:", data_range)


# ============================================================
# 15. GROUPING DATA
# ============================================================

print("\n15. GROUPING DATA")

sales_by_region = {
    "North": 15000,
    "South": 12000,
    "East": 18000,
    "West": 10000
}

for region, amount in sales_by_region.items():
    print(region, "-> ₹", amount)


# ============================================================
# 16. COMPARING VALUES
# ============================================================

print("\n16. COMPARING VALUES")

best_region = max(
    sales_by_region,
    key=sales_by_region.get
)

print("Highest Sales Region:", best_region)
print("Sales:", sales_by_region[best_region])


# ============================================================
# 17. PERCENTAGE CHANGE
# ============================================================

print("\n17. PERCENTAGE CHANGE")

previous_sales = 10000
current_sales = 12500

percentage_change = (
    (current_sales - previous_sales)
    / previous_sales
) * 100

print("Previous Sales:", previous_sales)
print("Current Sales:", current_sales)
print("Percentage Change:", percentage_change, "%")


# ============================================================
# 18. CORRELATION CONCEPT
# ============================================================

print("\n18. CORRELATION")

advertising = [10, 20, 30, 40, 50]
sales = [100, 150, 200, 260, 300]

print("Advertising:", advertising)
print("Sales:", sales)

print("\nCorrelation measures the relationship")
print("between variables.")

print("Important:")
print("Correlation does not automatically mean causation.")


# ============================================================
# 19. DATA VISUALIZATION
# ============================================================

print("\n19. DATA VISUALIZATION")

visualizations = {
    "Bar Chart": "Compare categories",
    "Line Chart": "Show trends over time",
    "Pie Chart": "Show proportions",
    "Histogram": "Show distribution",
    "Scatter Plot": "Show relationships"
}

for chart, purpose in visualizations.items():
    print(chart, "->", purpose)


# ============================================================
# 20. KPI
# ============================================================

print("\n20. KEY PERFORMANCE INDICATORS")

kpis = {
    "Revenue": 500000,
    "Customers": 2500,
    "Conversion Rate": 4.5,
    "Customer Retention": 82
}

for kpi, value in kpis.items():
    print(kpi, "->", value)


# ============================================================
# 21. TYPES OF DATA ANALYTICS
# ============================================================

print("\n21. TYPES OF DATA ANALYTICS")

analytics_types = {
    "Descriptive": "What happened?",
    "Diagnostic": "Why did it happen?",
    "Predictive": "What might happen?",
    "Prescriptive": "What should we do?"
}

for analytics_type, question in analytics_types.items():
    print(analytics_type, "->", question)


# ============================================================
# 22. BUSINESS QUESTION
# ============================================================

print("\n22. BUSINESS QUESTION")

question = "Which region generated the highest sales?"

print("Question:", question)
print("Answer:", best_region)

print("\nAnalytics should begin with a clear question")
print("and end with an actionable insight.")


# ============================================================
# 23. BASIC DATA ANALYTICS WORKFLOW
# ============================================================

print("\n23. BASIC DATA ANALYTICS WORKFLOW")

print("""
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
""")


# ============================================================
# 24. DATA ANALYTICS TOOLS
# ============================================================

print("\n24. COMMON DATA ANALYTICS TOOLS")

tools = [
    "Excel",
    "SQL",
    "Python",
    "R",
    "Power BI",
    "Tableau",
    "Databases"
]

for tool in tools:
    print("-", tool)


# ============================================================
# 25. DATA ANALYST SKILLS
# ============================================================

print("\n25. DATA ANALYST SKILLS")

skills = [
    "Data Cleaning",
    "SQL",
    "Statistics",
    "Data Visualization",
    "Excel",
    "Python",
    "Business Understanding",
    "Communication",
    "Problem Solving"
]

for skill in skills:
    print("-", skill)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 60)
print("DAY 01 COMPLETED")
print("=" * 60)

print("""
Today you learned:

1. Data Analytics
2. Data and Datasets
3. Variables
4. Data Types
5. Structured and Unstructured Data
6. Data Collection
7. Data Quality
8. Missing Data
9. Data Cleaning
10. Descriptive Statistics
11. Mean, Median, Minimum, Maximum and Range
12. Data Grouping
13. Percentage Change
14. Correlation
15. Data Visualization
16. KPIs
17. Types of Data Analytics
18. Business Questions
19. Analytics Workflow
20. Analytics Tools
21. Data Analyst Skills
""")

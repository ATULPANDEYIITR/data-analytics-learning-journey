"""
DATA ANALYST ROLE
=================

Topic:
Responsibilities, Analytical Thinking, Business Understanding,
Stakeholder Management, Requirements Gathering, Problem Definition,
Analytical Storytelling, and Communication

Purpose:
This script is a comprehensive learning guide for understanding what a
Data Analyst actually does in a professional organization.

The focus is not only on Python syntax or statistical calculations.
A strong Data Analyst must understand the business problem, identify
the correct analytical question, communicate with stakeholders, analyze
data appropriately, derive meaningful insights, and translate those
insights into decisions.

Learning progression:
1. What is a Data Analyst?
2. Responsibilities of a Data Analyst
3. The difference between data, information, insight, and decision
4. Analytical thinking
5. Business understanding
6. Stakeholder management
7. Requirements gathering
8. Problem definition
9. Metrics and KPIs
10. Hypotheses and assumptions
11. Exploratory analysis
12. Root-cause analysis
13. Segmentation
14. Correlation vs causation
15. Statistical thinking
16. Experimentation and A/B testing
17. Analytical storytelling
18. Data visualization
19. Communication
20. Handling ambiguity
21. Advanced analytical thinking
22. Capstone business case
23. Professional Data Analyst checklist

NOTE:
This file is intentionally educational. It uses Python to demonstrate
analytical concepts. Real-world analysis would normally use tools such
as Python, SQL, Excel, BI platforms, statistical packages, databases,
and cloud data platforms.
"""


# ============================================================
# 1. WHAT IS A DATA ANALYST?
# ============================================================

print("=" * 70)
print("WHAT IS A DATA ANALYST?")
print("=" * 70)

"""
A Data Analyst converts raw data into useful information and actionable
business insights.

A simplified analytical chain is:

Raw Data
    ↓
Data Cleaning
    ↓
Analysis
    ↓
Information
    ↓
Insight
    ↓
Recommendation
    ↓
Business Decision
    ↓
Business Action
    ↓
Business Outcome

A beginner may think:

    "A Data Analyst works with numbers."

A better definition is:

    "A Data Analyst uses data, analytical reasoning, and business
     understanding to help an organization make better decisions."

The difference is extremely important.

A Data Analyst is not simply a person who creates charts.

The analyst must understand:

- What problem are we solving?
- Why does the problem matter?
- Who cares about the answer?
- What decision will be made?
- What data is required?
- Is the data reliable?
- Which analytical method is appropriate?
- What does the result actually mean?
- What should the organization do next?
"""


# ============================================================
# 2. CORE RESPONSIBILITIES OF A DATA ANALYST
# ============================================================

print("\n" + "=" * 70)
print("CORE RESPONSIBILITIES")
print("=" * 70)

responsibilities = [
    "Understand business objectives",
    "Gather analytical requirements",
    "Define the business problem",
    "Identify relevant data",
    "Validate data quality",
    "Clean and transform data",
    "Explore patterns and trends",
    "Calculate metrics and KPIs",
    "Investigate causes and relationships",
    "Perform statistical analysis",
    "Create reports and dashboards",
    "Communicate findings",
    "Tell a clear analytical story",
    "Provide evidence-based recommendations",
    "Support stakeholders in decision-making",
    "Monitor business performance",
]

for number, responsibility in enumerate(responsibilities, start=1):
    print(f"{number}. {responsibility}")


# ============================================================
# 3. DATA, INFORMATION, INSIGHT, AND DECISION
# ============================================================

print("\n" + "=" * 70)
print("DATA → INFORMATION → INSIGHT → DECISION")
print("=" * 70)

"""
These concepts are related but are NOT the same.

DATA
----
Raw observations.

Example:
100, 120, 150, 180

INFORMATION
-----------
Processed data with context.

Example:
Monthly sales increased from 100 units to 180 units.

INSIGHT
-------
An interpretation that explains something meaningful.

Example:
Sales increased primarily because the company expanded into
two new geographic markets.

RECOMMENDATION
--------------
A suggested action based on evidence.

Example:
Continue investment in the two new markets while monitoring
customer acquisition cost.

DECISION
--------
The business chooses what to do.

Example:
Management approves additional regional marketing investment.

ACTION
------
The organization executes the decision.

OUTCOME
-------
The organization measures whether the action worked.

A mature Data Analyst thinks beyond:

    "What happened?"

and asks:

    "Why did it happen?"
    "What does it mean?"
    "What should we do?"
    "How confident are we?"
    "How will we know whether the decision worked?"
"""


# ============================================================
# 4. ANALYTICAL THINKING
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL THINKING")
print("=" * 70)

"""
Analytical thinking is the ability to break a complex problem into
smaller, measurable, logically connected questions.

Weak analytical thinking:

    "Sales are falling. Let's make a dashboard."

Strong analytical thinking:

    1. How large is the decline?
    2. When did it begin?
    3. Which products are affected?
    4. Which regions are affected?
    5. Which customer segments are affected?
    6. Did prices change?
    7. Did marketing spend change?
    8. Did competitors change their pricing?
    9. Did website traffic change?
    10. Did conversion rate change?
    11. Did customer retention change?
    12. What evidence supports each explanation?
    13. What action could reverse the decline?

Analytical thinking therefore involves:

- decomposition
- comparison
- classification
- measurement
- pattern recognition
- hypothesis generation
- hypothesis testing
- prioritization
- causal reasoning
- uncertainty management
"""


# ============================================================
# 5. A STRUCTURED ANALYTICAL THINKING FRAMEWORK
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL THINKING FRAMEWORK")
print("=" * 70)

analytical_framework = [
    ("1. Observe", "What is happening?"),
    ("2. Quantify", "How large is the problem?"),
    ("3. Compare", "Compared with what?"),
    ("4. Segment", "Where and for whom is it happening?"),
    ("5. Investigate", "What factors may explain it?"),
    ("6. Hypothesize", "What are the most plausible explanations?"),
    ("7. Test", "What evidence supports or rejects each hypothesis?"),
    ("8. Evaluate", "How reliable is the evidence?"),
    ("9. Recommend", "What should the business do?"),
    ("10. Measure", "How will success be evaluated?"),
]

for stage, question in analytical_framework:
    print(f"{stage}: {question}")


# ============================================================
# 6. THE PYRAMID OF QUESTIONS
# ============================================================

print("\n" + "=" * 70)
print("THE PYRAMID OF ANALYTICAL QUESTIONS")
print("=" * 70)

questions = {
    "Descriptive": "What happened?",
    "Diagnostic": "Why did it happen?",
    "Predictive": "What is likely to happen?",
    "Prescriptive": "What should we do?",
}

for analytical_type, question in questions.items():
    print(f"{analytical_type}: {question}")

"""
DESCRIPTIVE ANALYTICS
---------------------
Examples:

- Revenue increased by 12%.
- Customer churn increased from 4% to 6%.
- Website traffic decreased by 10%.

DIAGNOSTIC ANALYTICS
--------------------
Questions:

- Why did revenue increase?
- Why did churn increase?
- Why did traffic decrease?

PREDICTIVE ANALYTICS
--------------------
Questions:

- What might happen next month?
- Which customers are likely to churn?
- What demand should we expect?

PRESCRIPTIVE ANALYTICS
----------------------
Questions:

- What should we do?
- Which customers should receive an offer?
- Which marketing channel should receive additional budget?

A Data Analyst often works primarily with descriptive and diagnostic
analytics, while advanced analysts may also contribute to predictive
and prescriptive analytics.
"""


# ============================================================
# 7. BUSINESS UNDERSTANDING
# ============================================================

print("\n" + "=" * 70)
print("BUSINESS UNDERSTANDING")
print("=" * 70)

"""
Technical skill alone does not make someone an excellent Data Analyst.

Suppose an analyst knows:

- Python
- SQL
- Excel
- statistics
- Power BI

but does not understand the business.

The analyst may produce technically correct analysis that is
strategically useless.

Business understanding means knowing:

- how the organization makes money
- who its customers are
- what products/services it provides
- how customers move through the business
- what costs exist
- what operational constraints exist
- what KPIs matter
- what risks exist
- what decisions management must make
- what success means

Example:

An e-commerce company may care about:

Revenue
Orders
Average Order Value
Conversion Rate
Customer Acquisition Cost
Customer Lifetime Value
Return Rate
Cart Abandonment
Customer Retention
Gross Margin

An analyst must understand how these metrics interact.
"""


# ============================================================
# 8. BUSINESS MODEL THINKING
# ============================================================

print("\n" + "=" * 70)
print("BUSINESS MODEL THINKING")
print("=" * 70)

business_model = {
    "Customers": "Who buys?",
    "Product": "What is being sold?",
    "Value proposition": "Why do customers buy?",
    "Revenue": "How does the organization earn money?",
    "Costs": "What does it cost to operate?",
    "Acquisition": "How are customers acquired?",
    "Retention": "How are customers retained?",
    "Operations": "How is the service/product delivered?",
    "Risk": "What can cause business loss?",
}

for component, question in business_model.items():
    print(f"{component}: {question}")


# ============================================================
# 9. METRICS AND KPIs
# ============================================================

print("\n" + "=" * 70)
print("METRICS AND KPIs")
print("=" * 70)

"""
A metric is a measurable quantity.

A KPI (Key Performance Indicator) is a metric that is particularly
important for evaluating a strategic or operational objective.

Examples:

Revenue
Profit
Orders
Conversion Rate
Retention Rate
Churn Rate
Customer Acquisition Cost
Customer Lifetime Value
Average Order Value

Important principle:

    Not every metric is a KPI.

A dashboard containing 100 metrics may contain less useful information
than a dashboard containing 10 carefully selected KPIs.
"""


# ============================================================
# 10. BASIC KPI CALCULATIONS
# ============================================================

print("\n" + "=" * 70)
print("BASIC KPI CALCULATIONS")
print("=" * 70)


def conversion_rate(conversions, visitors):
    """Calculate conversion rate."""
    if visitors == 0:
        return 0
    return conversions / visitors * 100


def churn_rate(churned_customers, customers):
    """Calculate customer churn rate."""
    if customers == 0:
        return 0
    return churned_customers / customers * 100


def average_order_value(revenue, orders):
    """Calculate average order value."""
    if orders == 0:
        return 0
    return revenue / orders


def customer_acquisition_cost(marketing_cost, new_customers):
    """Calculate customer acquisition cost."""
    if new_customers == 0:
        return 0
    return marketing_cost / new_customers


print("Conversion Rate:", conversion_rate(800, 10000), "%")
print("Churn Rate:", churn_rate(600, 10000), "%")
print("Average Order Value:", average_order_value(500000, 10000))
print("Customer Acquisition Cost:",
      customer_acquisition_cost(200000, 4000))


# ============================================================
# 11. REQUIREMENTS GATHERING
# ============================================================

print("\n" + "=" * 70)
print("REQUIREMENTS GATHERING")
print("=" * 70)

"""
Requirements gathering means understanding exactly what a stakeholder
needs from an analytical project.

A stakeholder may say:

    "I need a sales dashboard."

This is NOT a complete analytical requirement.

The analyst should ask:

- Who will use the dashboard?
- What decision will it support?
- What business problem are we solving?
- Which metrics are required?
- What dimensions are needed?
- What time period is relevant?
- How frequently should it refresh?
- What level of detail is required?
- Which data sources should be used?
- What filters are required?
- What constitutes success?
- What are the acceptance criteria?

Requirements gathering prevents "building the wrong thing correctly."
"""


# ============================================================
# 12. REQUIREMENTS GATHERING QUESTIONS
# ============================================================

print("\n" + "=" * 70)
print("REQUIREMENTS GATHERING QUESTIONS")
print("=" * 70)

requirement_questions = [
    "What decision are you trying to make?",
    "What problem are you trying to solve?",
    "Who is the intended user?",
    "What business outcome matters?",
    "Which metrics do you currently use?",
    "Which metrics are most important?",
    "What time period should be analyzed?",
    "What dimensions should be available?",
    "What data sources are available?",
    "How frequently is the analysis required?",
    "What level of accuracy is required?",
    "What are the known data limitations?",
    "What does success look like?",
    "What action will be taken based on the result?",
]

for question in requirement_questions:
    print("-", question)


# ============================================================
# 13. REQUIREMENT VS SOLUTION
# ============================================================

print("\n" + "=" * 70)
print("REQUIREMENT VS SOLUTION")
print("=" * 70)

"""
A common mistake is confusing the requested solution with the actual
requirement.

Stakeholder says:

    "Build me a dashboard."

Potential underlying requirement:

    "I need to identify which regions are underperforming so that
     regional managers can take corrective action."

Dashboard = solution.

Identify underperforming regions = analytical requirement.

Take corrective action = business objective.

A strong analyst identifies the requirement beneath the requested tool.
"""


# ============================================================
# 14. PROBLEM DEFINITION
# ============================================================

print("\n" + "=" * 70)
print("PROBLEM DEFINITION")
print("=" * 70)

"""
Problem definition is one of the most important analytical skills.

A poorly defined problem creates poor analysis.

BAD:

    "Sales are bad."

BETTER:

    "Monthly sales declined by 15% during the last quarter."

STRONG:

    "Monthly sales declined by 15% during the last quarter, primarily
     in the enterprise customer segment. Management wants to determine
     whether the decline is related to pricing, customer retention,
     product mix, or reduced acquisition."

An excellent problem statement identifies:

1. Current state
2. Desired state
3. Gap
4. Time period
5. Population or segment
6. Business impact
7. Decision required
8. Analytical scope
"""


# ============================================================
# 15. PROBLEM STATEMENT TEMPLATE
# ============================================================

print("\n" + "=" * 70)
print("PROBLEM STATEMENT TEMPLATE")
print("=" * 70)

problem_statement_template = """
Current situation:
    What is happening?

Business impact:
    Why does it matter?

Scope:
    Where, when, and for whom is the problem occurring?

Evidence:
    What data indicates the problem?

Potential drivers:
    What factors might explain it?

Decision:
    What decision needs to be made?

Success criteria:
    What outcome would indicate improvement?
"""

print(problem_statement_template)


# ============================================================
# 16. HYPOTHESIS-DRIVEN ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("HYPOTHESIS-DRIVEN ANALYSIS")
print("=" * 70)

"""
A hypothesis is a testable explanation for an observed phenomenon.

Example:

Observation:
    Revenue declined.

Possible hypotheses:

H1:
    Customer traffic decreased.

H2:
    Conversion rate decreased.

H3:
    Average order value decreased.

H4:
    Customer churn increased.

H5:
    Product availability declined.

H6:
    Pricing changes affected demand.

The analyst then looks for evidence.

This is better than randomly exploring hundreds of columns without
a clear analytical direction.
"""

hypotheses = {
    "H1": "Customer traffic decreased",
    "H2": "Conversion rate decreased",
    "H3": "Average order value decreased",
    "H4": "Customer churn increased",
    "H5": "Product availability decreased",
    "H6": "Pricing changes affected demand",
}

for hypothesis, explanation in hypotheses.items():
    print(f"{hypothesis}: {explanation}")


# ============================================================
# 17. ASSUMPTIONS
# ============================================================

print("\n" + "=" * 70)
print("ASSUMPTIONS")
print("=" * 70)

"""
Analysts frequently work with incomplete information.

An assumption is something believed to be true for the purpose of
analysis but that may require validation.

Examples:

- Customer IDs are unique.
- Revenue values are recorded consistently.
- Dates use the same timezone.
- Missing values are not systematically biased.
- A transaction represents a completed purchase.
- Data extraction includes all relevant regions.

Good analysts explicitly document assumptions.

This improves transparency and prevents stakeholders from treating
analytical conclusions as absolute truths.
"""


# ============================================================
# 18. DATA QUALITY
# ============================================================

print("\n" + "=" * 70)
print("DATA QUALITY")
print("=" * 70)

"""
Before trusting analysis, validate the data.

Important dimensions of data quality include:

1. Accuracy
2. Completeness
3. Consistency
4. Timeliness
5. Uniqueness
6. Validity

Example:

If the database contains:

Revenue = 10,000
Revenue = -500,000

the analyst should not immediately conclude that the company lost
500,000.

The value may represent:

- a refund
- a reversal
- a data-entry error
- a chargeback
- an accounting adjustment

Data must be understood in business context.
"""


# ============================================================
# 19. EXPLORATORY DATA ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("EXPLORATORY DATA ANALYSIS")
print("=" * 70)

"""
Exploratory Data Analysis (EDA) is the process of examining data to
understand its structure, distributions, patterns, relationships,
outliers, and anomalies.

Typical questions:

- How many observations exist?
- What variables exist?
- What are the data types?
- Are values missing?
- Are there duplicates?
- What is the distribution?
- Are there extreme values?
- Are there trends?
- Are there relationships?
- Are there meaningful segments?

EDA is not merely generating graphs.

EDA is a process of asking increasingly intelligent questions.
"""


# ============================================================
# 20. SIMPLE EDA EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("SIMPLE EDA EXAMPLE")
print("=" * 70)

sales = [120, 150, 180, 160, 210, 240, 230, 280]

total_sales = sum(sales)
average_sales = total_sales / len(sales)
minimum_sales = min(sales)
maximum_sales = max(sales)

print("Total sales:", total_sales)
print("Average sales:", average_sales)
print("Minimum sales:", minimum_sales)
print("Maximum sales:", maximum_sales)

growth = (sales[-1] - sales[0]) / sales[0] * 100

print("Growth from first to last observation:", round(growth, 2), "%")


# ============================================================
# 21. COMPARISON
# ============================================================

print("\n" + "=" * 70)
print("COMPARISON")
print("=" * 70)

"""
Almost every useful analysis contains comparison.

A number by itself often means very little.

Example:

    Revenue = ₹10 million

Is that good?

We need a benchmark.

Possible comparisons:

- Previous month
- Previous year
- Budget
- Forecast
- Target
- Competitor
- Industry benchmark
- Similar customer segment
- Similar geographic region

A good analyst asks:

    "Compared with what?"
"""

current_revenue = 12_000_000
previous_revenue = 10_000_000

growth_rate = (
    (current_revenue - previous_revenue)
    / previous_revenue
    * 100
)

print("Revenue growth:", round(growth_rate, 2), "%")


# ============================================================
# 22. SEGMENTATION
# ============================================================

print("\n" + "=" * 70)
print("SEGMENTATION")
print("=" * 70)

"""
Aggregated metrics can hide important patterns.

Suppose overall conversion rate is 5%.

That number may hide:

Mobile users       = 2%
Desktop users      = 8%

New customers      = 3%
Returning customers = 9%

Region A            = 7%
Region B            = 2%

Segmentation helps answer:

    "Where exactly is the problem?"

Common segmentation dimensions:

- geography
- product
- customer type
- age group
- acquisition channel
- device
- time
- subscription plan
- income category
- transaction size
"""


# ============================================================
# 23. ROOT-CAUSE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("ROOT-CAUSE ANALYSIS")
print("=" * 70)

"""
Finding a correlation is not necessarily finding the root cause.

Root-cause analysis attempts to identify the underlying driver of a
problem.

Useful techniques include:

- 5 Whys
- Fishbone / Ishikawa analysis
- Pareto analysis
- Segmentation
- Funnel analysis
- Cohort analysis
- Time-series analysis
- Process analysis
- Statistical testing
- Controlled experimentation

Example:

Sales decreased.

Why?

    Fewer orders.

Why?

    Conversion rate decreased.

Why?

    Checkout completion decreased.

Why?

    Checkout errors increased.

Why?

    A payment integration failed after a software release.

Potential root cause:
    Payment integration failure.

This is far more useful than simply reporting:

    "Sales decreased."
"""


# ============================================================
# 24. PARETO THINKING
# ============================================================

print("\n" + "=" * 70)
print("PARETO THINKING")
print("=" * 70)

"""
Pareto analysis asks whether a relatively small number of causes
contribute to a large proportion of the outcome.

Example:

Suppose customer complaints are:

Delivery delay       = 400
Product quality      = 250
Billing              = 100
Website              = 80
Other                = 70

Rather than treating all categories equally, management may prioritize
the categories responsible for the largest share of complaints.
"""

complaints = {
    "Delivery delay": 400,
    "Product quality": 250,
    "Billing": 100,
    "Website": 80,
    "Other": 70,
}

total_complaints = sum(complaints.values())

for category, count in sorted(
    complaints.items(),
    key=lambda item: item[1],
    reverse=True
):
    percentage = count / total_complaints * 100
    print(f"{category}: {count} ({percentage:.2f}%)")


# ============================================================
# 25. CORRELATION VS CAUSATION
# ============================================================

print("\n" + "=" * 70)
print("CORRELATION VS CAUSATION")
print("=" * 70)

"""
Correlation means two variables move together.

Causation means a change in one variable actually produces a change
in another variable.

Example:

Ice cream sales increase.
Sunburn cases increase.

They are correlated.

But ice cream does not cause sunburn.

A third variable exists:

    Hot weather.

This illustrates a confounding variable.

Therefore:

    Correlation ≠ Causation

Analysts must be careful when communicating relationships.

Better language:

    "The variables are associated."

instead of automatically saying:

    "X caused Y."

Causal claims usually require stronger evidence, such as:

- randomized experiments
- controlled experiments
- natural experiments
- quasi-experimental methods
- causal inference techniques
"""


# ============================================================
# 26. STATISTICAL THINKING
# ============================================================

print("\n" + "=" * 70)
print("STATISTICAL THINKING")
print("=" * 70)

"""
A Data Analyst does not need to become a theoretical mathematician,
but must understand statistical reasoning.

Important concepts include:

- mean
- median
- mode
- variance
- standard deviation
- percentiles
- distributions
- sampling
- confidence intervals
- probability
- hypothesis testing
- statistical significance
- effect size
- statistical power
- bias
- variance
- sampling error
- selection bias
- survivorship bias
- confounding

The central question is:

    "How confident should I be in this conclusion?"
"""


# ============================================================
# 27. MEAN VS MEDIAN
# ============================================================

print("\n" + "=" * 70)
print("MEAN VS MEDIAN")
print("=" * 70)

income = [30000, 32000, 35000, 38000, 40000, 500000]

mean_income = sum(income) / len(income)

sorted_income = sorted(income)
n = len(sorted_income)

if n % 2 == 0:
    median_income = (
        sorted_income[n // 2 - 1]
        + sorted_income[n // 2]
    ) / 2
else:
    median_income = sorted_income[n // 2]

print("Mean income:", mean_income)
print("Median income:", median_income)

"""
The extreme value of 500,000 strongly increases the mean.

Therefore, when distributions are skewed, the median may provide a
more representative measure of the typical observation.
"""


# ============================================================
# 28. A/B TESTING
# ============================================================

print("\n" + "=" * 70)
print("A/B TESTING")
print("=" * 70)

"""
A/B testing compares two variants.

Example:

A = existing checkout page
B = redesigned checkout page

Suppose:

A:
1000 visitors
50 purchases

B:
1000 visitors
65 purchases

Conversion:

A = 5%
B = 6.5%

The naive conclusion is:

    "B is better."

A stronger analyst asks:

- Is the difference statistically significant?
- Was randomization performed correctly?
- Was the sample size sufficient?
- Were users exposed to both versions fairly?
- Was the experiment contaminated?
- Were multiple metrics tested?
- Was the experiment stopped too early?
- Is the effect practically meaningful?

Statistical significance and business significance are different.

A 0.01% improvement may be statistically significant with a huge
sample but commercially irrelevant.
"""


# ============================================================
# 29. BUSINESS SIGNIFICANCE
# ============================================================

print("\n" + "=" * 70)
print("STATISTICAL SIGNIFICANCE VS BUSINESS SIGNIFICANCE")
print("=" * 70)

"""
Statistical significance asks:

    "Is the observed difference unlikely to be explained by random
     variation under the statistical model?"

Business significance asks:

    "Is the difference large enough to matter to the organization?"

Example:

A redesigned website increases conversion from:

5.00% → 5.02%

This might be statistically detectable.

But if implementation costs ₹50 lakh and the incremental revenue is
₹2 lakh, the change may not make business sense.

The analyst must connect statistical results to economics.
"""


# ============================================================
# 30. STAKEHOLDER MANAGEMENT
# ============================================================

print("\n" + "=" * 70)
print("STAKEHOLDER MANAGEMENT")
print("=" * 70)

"""
Stakeholders are people or groups affected by, interested in, or
responsible for the outcome of an analytical project.

Examples:

- executives
- managers
- product managers
- marketing teams
- sales teams
- finance teams
- operations
- engineering
- data engineering
- customers
- compliance teams

Different stakeholders need different levels of detail.

An executive may ask:

    "What is happening and what should we do?"

An engineer may ask:

    "Which event is generating the anomaly?"

A finance manager may ask:

    "What is the financial impact?"

A product manager may ask:

    "Which user segment is affected?"

Good stakeholder management means tailoring communication to the
audience.
"""


# ============================================================
# 31. STAKEHOLDER EXPECTATION MANAGEMENT
# ============================================================

print("\n" + "=" * 70)
print("STAKEHOLDER EXPECTATION MANAGEMENT")
print("=" * 70)

"""
A Data Analyst should establish expectations around:

- scope
- timeline
- data availability
- analytical methodology
- assumptions
- limitations
- deliverables
- confidence level
- dependencies

Never silently make major assumptions.

If the data cannot answer the question, say so.

A professional response is:

    "The current dataset can measure customer retention, but it does
     not contain the acquisition source required to determine whether
     the retention decline differs by marketing channel."

This is better than inventing an answer.
"""


# ============================================================
# 32. COMMUNICATION
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL COMMUNICATION")
print("=" * 70)

"""
Communication is one of the most important Data Analyst skills.

An analysis can be technically excellent but useless if stakeholders
cannot understand it.

A good communication structure is:

    Context
       ↓
    Problem
       ↓
    Evidence
       ↓
    Insight
       ↓
    Impact
       ↓
    Recommendation
       ↓
    Next action

Avoid presenting 30 charts before explaining what matters.
"""


# ============================================================
# 33. THE "SO WHAT?" TEST
# ============================================================

print("\n" + "=" * 70)
print("THE 'SO WHAT?' TEST")
print("=" * 70)

"""
For every analytical finding, ask:

    "So what?"

Example:

Finding:
    Website traffic increased 20%.

So what?

Possible answer:
    The increase came from paid advertising.

So what?

    Paid advertising generated traffic but conversion remained low.

So what?

    The company may be spending more money to acquire low-intent
    visitors.

So what?

    Marketing should evaluate campaign-level ROI instead of optimizing
    purely for traffic.

This converts a descriptive observation into a business insight.
"""


# ============================================================
# 34. ANALYTICAL STORYTELLING
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL STORYTELLING")
print("=" * 70)

"""
Analytical storytelling means presenting data in a logical narrative
that allows an audience to understand:

    What happened?
    Why did it happen?
    Why does it matter?
    What should happen next?

A strong analytical story is selective.

It does not show every calculation.

It highlights the evidence necessary to support the conclusion.
"""


# ============================================================
# 35. STORYTELLING FRAMEWORK
# ============================================================

print("\n" + "=" * 70)
print("STORYTELLING FRAMEWORK")
print("=" * 70)

storytelling_framework = [
    "1. Executive summary",
    "2. Business context",
    "3. Problem definition",
    "4. Key evidence",
    "5. Analytical findings",
    "6. Root cause or drivers",
    "7. Business impact",
    "8. Recommendation",
    "9. Risks and limitations",
    "10. Next steps",
]

for item in storytelling_framework:
    print(item)


# ============================================================
# 36. DATA VISUALIZATION THINKING
# ============================================================

print("\n" + "=" * 70)
print("DATA VISUALIZATION THINKING")
print("=" * 70)

"""
Choose visualizations based on the analytical question.

Comparison:
    Bar chart

Trend:
    Line chart

Distribution:
    Histogram / box plot

Relationship:
    Scatter plot

Composition:
    Stacked bar / carefully used pie chart

Geographical pattern:
    Map

The objective is not to make a chart beautiful.

The objective is to make the important pattern easy to understand.
"""


# ============================================================
# 37. GOOD VS BAD DASHBOARD THINKING
# ============================================================

print("\n" + "=" * 70)
print("GOOD VS BAD DASHBOARD THINKING")
print("=" * 70)

bad_dashboard = [
    "Too many charts",
    "Too many colors",
    "No clear objective",
    "No comparison",
    "No business context",
    "No explanation of anomalies",
    "Too many low-value metrics",
]

good_dashboard = [
    "Clear business objective",
    "Important KPIs are prioritized",
    "Relevant comparisons are visible",
    "Trends are easy to identify",
    "Filters support actual decisions",
    "Exceptions are highlighted",
    "Definitions are documented",
    "Actions are connected to insights",
]

print("Problems with weak dashboards:")
for item in bad_dashboard:
    print("-", item)

print("\nCharacteristics of stronger dashboards:")
for item in good_dashboard:
    print("-", item)


# ============================================================
# 38. HANDLING AMBIGUITY
# ============================================================

print("\n" + "=" * 70)
print("HANDLING AMBIGUITY")
print("=" * 70)

"""
Real-world analytical requests are often ambiguous.

Example:

    "Why are customers unhappy?"

This is not directly measurable.

The analyst must operationalize the problem.

Possible measurable indicators:

- customer satisfaction score
- NPS
- support ticket volume
- complaint rate
- refund rate
- negative review frequency
- product return rate
- customer churn

The analyst converts vague language into measurable concepts.

This is a major professional skill.
"""


# ============================================================
# 39. OPERATIONAL DEFINITIONS
# ============================================================

print("\n" + "=" * 70)
print("OPERATIONAL DEFINITIONS")
print("=" * 70)

"""
Different people may use the same word differently.

For example:

"Customer"

Could mean:

- registered user
- paying customer
- active customer
- customer with at least one purchase
- customer with a purchase in the last 90 days

"Revenue"

Could mean:

- gross revenue
- net revenue
- recognized revenue
- booked revenue
- revenue excluding refunds

Therefore, analysts must define metrics precisely.
"""

metric_definitions = {
    "Active customer":
        "A customer who completed at least one transaction during the defined period.",
    "Conversion rate":
        "Number of conversions divided by the defined eligible population.",
    "Churn rate":
        "Number of customers considered churned divided by the defined customer base.",
}

for metric, definition in metric_definitions.items():
    print(f"{metric}: {definition}")


# ============================================================
# 40. FUNNEL ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("FUNNEL ANALYSIS")
print("=" * 70)

"""
Funnels represent sequential stages in a process.

Example:

Website visitors
       ↓
Product viewers
       ↓
Cart additions
       ↓
Checkout
       ↓
Purchase

Suppose:

Visitors = 100,000
Product views = 40,000
Cart additions = 10,000
Checkout = 6,000
Purchases = 3,000

The analyst can calculate conversion between stages and identify
where the largest drop occurs.
"""

funnel = [
    ("Visitors", 100000),
    ("Product views", 40000),
    ("Cart additions", 10000),
    ("Checkout", 6000),
    ("Purchases", 3000),
]

for i, (stage, count) in enumerate(funnel):
    if i == 0:
        print(stage, ":", count)
    else:
        previous_count = funnel[i - 1][1]
        stage_conversion = count / previous_count * 100
        print(
            stage,
            ":",
            count,
            f"| Conversion from previous stage: {stage_conversion:.2f}%"
        )


# ============================================================
# 41. COHORT THINKING
# ============================================================

print("\n" + "=" * 70)
print("COHORT ANALYSIS")
print("=" * 70)

"""
A cohort is a group of users sharing a common characteristic or
starting event.

Example:

January customers
February customers
March customers

Instead of asking:

    "What is our retention rate?"

we can ask:

    "How does retention behave for customers acquired in each month?"

This helps distinguish:

- seasonal effects
- changes in product quality
- acquisition quality
- onboarding changes
- customer behavior changes
"""


# ============================================================
# 42. TIME-SERIES THINKING
# ============================================================

print("\n" + "=" * 70)
print("TIME-SERIES THINKING")
print("=" * 70)

"""
When analyzing time-based data, consider:

- trend
- seasonality
- cycles
- sudden changes
- moving averages
- growth rates
- period-over-period changes
- year-over-year changes
- structural breaks

Example:

Sales:

January   100
February  105
March     110
April     108
May       112

A single month's decrease does not necessarily mean the business is
in decline.

The analyst must consider the broader pattern.
"""


# ============================================================
# 43. DATA BIAS
# ============================================================

print("\n" + "=" * 70)
print("DATA BIAS")
print("=" * 70)

"""
Important sources of analytical bias include:

Selection bias
--------------
The sample does not represent the target population.

Survivorship bias
-----------------
Only successful cases remain visible.

Confirmation bias
------------------
The analyst searches mainly for evidence supporting an existing belief.

Measurement bias
----------------
The measurement process systematically distorts results.

Reporting bias
--------------
Some events are more likely to be reported than others.

Availability bias
-----------------
Easily available data is treated as if it represents the complete
reality.

A sophisticated analyst actively looks for these problems.
"""


# ============================================================
# 44. DATA-DRIVEN DOES NOT MEAN DATA-BLIND
# ============================================================

print("\n" + "=" * 70)
print("DATA-DRIVEN DOES NOT MEAN DATA-BLIND")
print("=" * 70)

"""
Data is evidence, not reality itself.

Business decisions may also depend on:

- strategy
- regulations
- operational constraints
- customer experience
- ethics
- organizational capability
- risk
- cost
- qualitative feedback

An analyst should not say:

    "The data says we must do X."

A more professional formulation is:

    "Based on the available evidence, X appears to be the strongest
     option under the stated assumptions and constraints."
"""


# ============================================================
# 45. ADVANCED ANALYTICAL THINKING
# ============================================================

print("\n" + "=" * 70)
print("ADVANCED ANALYTICAL THINKING")
print("=" * 70)

"""
At advanced levels, analysts think about:

1. Causal inference
2. Experimental design
3. Counterfactual reasoning
4. Selection effects
5. Confounding
6. Measurement error
7. Statistical power
8. Model assumptions
9. Uncertainty
10. Sensitivity analysis
11. Scenario analysis
12. Decision theory
13. Cost-benefit analysis
14. Expected value
15. Risk-adjusted decisions

The advanced analyst does not only ask:

    "What is the estimate?"

They ask:

    "What assumptions produce this estimate?"
    "How sensitive is the conclusion?"
    "What would happen under alternative scenarios?"
    "What evidence would change my conclusion?"
"""


# ============================================================
# 46. COUNTERFACTUAL THINKING
# ============================================================

print("\n" + "=" * 70)
print("COUNTERFACTUAL THINKING")
print("=" * 70)

"""
A counterfactual asks:

    "What would have happened if the intervention had NOT occurred?"

Example:

A company launches a new marketing campaign.

Sales increase by 20%.

Can we conclude that the campaign caused the increase?

Not necessarily.

Sales might have increased because:

- demand was already rising
- competitors had stock problems
- seasonality occurred
- prices changed
- another campaign ran simultaneously

The important comparison is:

    Observed outcome with intervention

versus

    Estimated outcome without intervention

This is central to causal reasoning.
"""


# ============================================================
# 47. SENSITIVITY ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("SENSITIVITY ANALYSIS")
print("=" * 70)

"""
Sensitivity analysis asks:

    "Would the recommendation change if an assumption changed?"

Suppose an investment is profitable if customer retention is above 70%.

Test several scenarios.
"""

retention_scenarios = [0.60, 0.65, 0.70, 0.75, 0.80]

for retention in retention_scenarios:
    profitable = retention >= 0.70
    print(
        f"Retention = {retention:.0%} | "
        f"Profitable assumption = {profitable}"
    )

"""
This is much stronger than presenting one forecast as if it were
certain.
"""


# ============================================================
# 48. EXPECTED VALUE THINKING
# ============================================================

print("\n" + "=" * 70)
print("EXPECTED VALUE")
print("=" * 70)

"""
Expected value provides a framework for decisions involving
uncertainty.

Formula:

Expected Value = Σ(probability × outcome)

Example:

Option A:
70% chance of ₹100,000 gain
30% chance of ₹20,000 loss
"""

probability_gain = 0.70
gain = 100000

probability_loss = 0.30
loss = -20000

expected_value = (
    probability_gain * gain
    + probability_loss * loss
)

print("Expected value of Option A:", expected_value)


# ============================================================
# 49. ANALYST VS REPORTING SPECIALIST
# ============================================================

print("\n" + "=" * 70)
print("REPORTING VS ANALYSIS")
print("=" * 70)

"""
REPORTING:

    "Revenue was ₹10 million."

ANALYSIS:

    "Revenue was ₹10 million, 8% below target, with the largest gap
     coming from the enterprise segment."

DEEP ANALYSIS:

    "Revenue was 8% below target primarily because enterprise order
     volume declined 15%. The decline was concentrated in two regions
     where customer acquisition fell after a channel budget reduction."

RECOMMENDATION:

    "Restore investment in the affected acquisition channels and
     monitor enterprise conversion and acquisition cost weekly."

The progression is:

    Reporting
        ↓
    Description
        ↓
    Diagnosis
        ↓
    Insight
        ↓
    Recommendation
"""


# ============================================================
# 50. EXECUTIVE COMMUNICATION
# ============================================================

print("\n" + "=" * 70)
print("EXECUTIVE COMMUNICATION")
print("=" * 70)

"""
Executives usually care about:

- business impact
- financial impact
- strategic significance
- risk
- opportunity
- recommended action
- confidence
- timing

They generally do not need every intermediate calculation.

A strong executive summary might follow:

    "Revenue declined 12% versus target, driven primarily by lower
     enterprise conversion in two regions. The evidence suggests
     reduced lead quality is the largest contributor. We recommend
     reallocating acquisition budget toward higher-converting channels
     and reviewing the impact after four weeks."

The supporting analysis can contain all technical details separately.
"""


# ============================================================
# 51. COMMUNICATION TO TECHNICAL STAKEHOLDERS
# ============================================================

print("\n" + "=" * 70)
print("COMMUNICATION TO TECHNICAL STAKEHOLDERS")
print("=" * 70)

"""
Technical stakeholders may require:

- data source
- SQL logic
- transformation logic
- joins
- filters
- metric definitions
- assumptions
- statistical methodology
- reproducibility
- validation
- lineage

Therefore, communication must be audience-specific.

The same analysis may require:

Executive summary
+
Technical appendix
+
Dashboard
+
Data dictionary
"""


# ============================================================
# 52. ANALYTICAL DOCUMENTATION
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL DOCUMENTATION")
print("=" * 70)

"""
A professional analytical project should document:

- objective
- business question
- data sources
- metric definitions
- assumptions
- methodology
- transformations
- limitations
- findings
- recommendations
- owner
- refresh frequency
- validation rules

This makes the analysis reproducible and auditable.
"""


# ============================================================
# 53. DATA DICTIONARY
# ============================================================

print("\n" + "=" * 70)
print("DATA DICTIONARY")
print("=" * 70)

data_dictionary = {
    "customer_id": "Unique identifier for the customer",
    "order_id": "Unique identifier for the transaction",
    "order_date": "Date on which the order was placed",
    "revenue": "Revenue associated with the transaction",
    "region": "Geographic region associated with the customer",
    "channel": "Customer acquisition channel",
}

for field, definition in data_dictionary.items():
    print(f"{field}: {definition}")


# ============================================================
# 54. CAPSTONE CASE STUDY
# ============================================================

print("\n" + "=" * 70)
print("CAPSTONE CASE STUDY")
print("=" * 70)

"""
BUSINESS SCENARIO
-----------------

An e-commerce company reports that monthly revenue has fallen.

Management asks:

    "Why are sales declining?"

A weak analyst immediately opens a visualization tool.

A strong analyst follows a structured process.

STEP 1:
Understand the business objective.

Management wants to understand the revenue decline and identify
potential corrective actions.

STEP 2:
Define the problem.

Revenue declined during the latest period compared with the previous
period.

STEP 3:
Decompose revenue.

Revenue can be approximated as:

    Number of orders × Average Order Value

Orders can be influenced by:

    Traffic × Conversion Rate

Therefore:

    Revenue
        ↓
    Orders
        ↓
    Traffic
        ↓
    Conversion
        ↓
    Average Order Value

STEP 4:
Create hypotheses.

H1: Traffic decreased.
H2: Conversion decreased.
H3: Average order value decreased.
H4: Returning customers declined.
H5: Product availability decreased.
H6: Specific regions underperformed.
H7: Marketing channel performance changed.

STEP 5:
Segment the data.

Analyze:

- region
- product
- customer type
- acquisition channel
- device
- time

STEP 6:
Identify the largest contribution to the decline.

STEP 7:
Investigate possible causes.

STEP 8:
Evaluate confidence and data limitations.

STEP 9:
Estimate business impact.

STEP 10:
Recommend an action.

STEP 11:
Define success metrics.

STEP 12:
Monitor results after implementation.
"""


# ============================================================
# 55. CAPSTONE NUMERICAL EXAMPLE
# ============================================================

print("\n" + "=" * 70)
print("CAPSTONE NUMERICAL EXAMPLE")
print("=" * 70)

previous_period = {
    "visitors": 100000,
    "conversion_rate": 0.05,
    "average_order_value": 1000,
}

current_period = {
    "visitors": 85000,
    "conversion_rate": 0.045,
    "average_order_value": 980,
}

previous_orders = (
    previous_period["visitors"]
    * previous_period["conversion_rate"]
)

current_orders = (
    current_period["visitors"]
    * current_period["conversion_rate"]
)

previous_revenue = (
    previous_orders
    * previous_period["average_order_value"]
)

current_revenue = (
    current_orders
    * current_period["average_order_value"]
)

revenue_change = (
    (current_revenue - previous_revenue)
    / previous_revenue
    * 100
)

print("Previous orders:", previous_orders)
print("Current orders:", current_orders)
print("Previous revenue:", previous_revenue)
print("Current revenue:", current_revenue)
print("Revenue change:", round(revenue_change, 2), "%")


# ============================================================
# 56. CAPSTONE INTERPRETATION
# ============================================================

print("\n" + "=" * 70)
print("CAPSTONE INTERPRETATION")
print("=" * 70)

"""
The business should NOT simply report:

    "Revenue decreased."

The analysis indicates:

1. Visitors decreased.
2. Conversion rate decreased.
3. Average order value decreased.

Therefore, multiple components contributed to the decline.

A strong analytical conclusion would be:

    "Revenue declined because both traffic and conversion decreased,
     while average order value also fell slightly. The next stage of
     analysis should determine whether the traffic decline is related
     to acquisition-channel performance and whether the conversion
     decline is concentrated in specific devices, regions, products,
     or customer segments."

Notice the distinction between:

OBSERVATION:
    Revenue decreased.

DIAGNOSIS:
    Traffic and conversion decreased.

DEEPER INVESTIGATION:
    Identify where and why traffic and conversion changed.

RECOMMENDATION:
    Depends on evidence from the deeper investigation.
"""


# ============================================================
# 57. PRIORITIZATION
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL PRIORITIZATION")
print("=" * 70)

"""
Not every analytical question deserves equal effort.

A useful prioritization framework considers:

    Business Impact
    ×
    Decision Importance
    ×
    Feasibility
    ×
    Confidence

High-impact, decision-relevant questions should generally receive
priority.

Example:

Question A:
    Why did traffic decrease by 2%?

Question B:
    Why did conversion decrease by 25%?

Question B may deserve more immediate investigation if conversion is
a major revenue driver.
"""


# ============================================================
# 58. ANALYTICAL TRADE-OFFS
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL TRADE-OFFS")
print("=" * 70)

"""
Real-world analysis involves trade-offs.

Examples:

Speed vs accuracy
Detail vs simplicity
Completeness vs timeliness
Complexity vs interpretability
Precision vs cost
Automation vs flexibility

A stakeholder may need an answer today.

A perfect analysis may require three weeks.

The analyst must determine what level of rigor is appropriate for
the decision.

The goal is not maximum complexity.

The goal is appropriate analytical rigor.
"""


# ============================================================
# 59. ETHICAL ANALYTICS
# ============================================================

print("\n" + "=" * 70)
print("ETHICAL ANALYTICS")
print("=" * 70)

"""
Professional analysts should consider:

- privacy
- confidentiality
- fairness
- bias
- responsible use of data
- misleading visualizations
- inappropriate conclusions
- sensitive attributes
- data security
- transparency

Never manipulate charts merely to make a result appear stronger.

Never hide important limitations from decision-makers.

Never present uncertainty as certainty.
"""


# ============================================================
# 60. PROFESSIONAL ANALYST MINDSET
# ============================================================

print("\n" + "=" * 70)
print("PROFESSIONAL DATA ANALYST MINDSET")
print("=" * 70)

mindset = [
    "Be curious",
    "Question assumptions",
    "Understand the business",
    "Define problems precisely",
    "Validate data",
    "Think in hypotheses",
    "Compare against meaningful benchmarks",
    "Segment before generalizing",
    "Distinguish correlation from causation",
    "Quantify uncertainty",
    "Focus on business impact",
    "Communicate clearly",
    "Document assumptions",
    "Admit limitations",
    "Recommend actions only when evidence supports them",
]

for item in mindset:
    print("-", item)


# ============================================================
# 61. DATA ANALYST SKILL STACK
# ============================================================

print("\n" + "=" * 70)
print("DATA ANALYST SKILL STACK")
print("=" * 70)

skill_stack = {
    "Business": [
        "Business understanding",
        "Domain knowledge",
        "KPI understanding",
        "Decision-making context",
    ],
    "Analytical": [
        "Problem solving",
        "Critical thinking",
        "Hypothesis development",
        "Root-cause analysis",
        "Statistical reasoning",
    ],
    "Technical": [
        "SQL",
        "Python",
        "Excel",
        "Data cleaning",
        "Data visualization",
        "BI tools",
    ],
    "Communication": [
        "Written communication",
        "Presentation",
        "Analytical storytelling",
        "Stakeholder management",
    ],
}

for category, skills in skill_stack.items():
    print(f"\n{category}:")
    for skill in skills:
        print(f"  - {skill}")


# ============================================================
# 62. COMPLETE ANALYTICAL WORKFLOW
# ============================================================

print("\n" + "=" * 70)
print("COMPLETE DATA ANALYSIS WORKFLOW")
print("=" * 70)

workflow = [
    "1. Understand the business context",
    "2. Identify stakeholders",
    "3. Gather requirements",
    "4. Define the business problem",
    "5. Define success criteria",
    "6. Identify required metrics",
    "7. Identify data sources",
    "8. Validate data quality",
    "9. Prepare and clean data",
    "10. Perform exploratory analysis",
    "11. Segment the population",
    "12. Compare relevant groups",
    "13. Generate hypotheses",
    "14. Test hypotheses",
    "15. Investigate root causes",
    "16. Quantify business impact",
    "17. Assess uncertainty",
    "18. Develop recommendations",
    "19. Communicate findings",
    "20. Implement action",
    "21. Measure outcome",
    "22. Iterate",
]

for step in workflow:
    print(step)


# ============================================================
# 63. ANALYTICAL QUALITY CHECKLIST
# ============================================================

print("\n" + "=" * 70)
print("ANALYTICAL QUALITY CHECKLIST")
print("=" * 70)

quality_checklist = [
    "Is the business problem clearly defined?",
    "Is the decision clearly identified?",
    "Are stakeholders identified?",
    "Are requirements documented?",
    "Are metrics precisely defined?",
    "Are assumptions documented?",
    "Is the data source appropriate?",
    "Has data quality been checked?",
    "Have missing values been investigated?",
    "Have duplicates been investigated?",
    "Have outliers been investigated?",
    "Have meaningful comparisons been made?",
    "Has segmentation been considered?",
    "Have alternative explanations been considered?",
    "Has correlation been distinguished from causation?",
    "Has uncertainty been communicated?",
    "Is the recommendation supported by evidence?",
    "Is the business impact quantified?",
    "Can another analyst reproduce the analysis?",
    "Are limitations documented?",
]

for number, question in enumerate(quality_checklist, start=1):
    print(f"{number}. {question}")


# ============================================================
# 64. FINAL PROFESSIONAL FRAMEWORK
# ============================================================

print("\n" + "=" * 70)
print("THE DATA ANALYST MENTAL MODEL")
print("=" * 70)

"""
The complete mental model can be summarized as:

BUSINESS
    ↓
QUESTION
    ↓
PROBLEM
    ↓
REQUIREMENTS
    ↓
METRICS
    ↓
DATA
    ↓
QUALITY
    ↓
ANALYSIS
    ↓
EVIDENCE
    ↓
INSIGHT
    ↓
IMPACT
    ↓
RECOMMENDATION
    ↓
DECISION
    ↓
ACTION
    ↓
MEASUREMENT
    ↓
LEARNING

The best Data Analysts do not start with:

    "Which Python library should I use?"

They start with:

    "What decision are we trying to improve?"

Python, SQL, Excel, statistics, visualization, and BI tools are means
to accomplish the analytical objective.

The ultimate value of a Data Analyst comes from connecting:

    DATA + ANALYTICAL THINKING + BUSINESS UNDERSTANDING
    + COMMUNICATION + DECISION-MAKING
"""


# ============================================================
# 65. MINI PRACTICE EXERCISES
# ============================================================

print("\n" + "=" * 70)
print("MINI PRACTICE EXERCISES")
print("=" * 70)

exercises = [
    "A company reports a 10% fall in revenue. List five hypotheses.",
    "Define three KPIs for an e-commerce company.",
    "Convert 'customers are unhappy' into a measurable problem statement.",
    "Create five stakeholder questions for a sales dashboard.",
    "Explain why a 20% increase in website traffic may not increase revenue.",
    "Identify three possible confounding variables in a marketing analysis.",
    "Write an executive summary for a hypothetical sales decline.",
    "Design a funnel for an online shopping process.",
    "List five data-quality checks before analyzing customer data.",
    "Explain why correlation does not automatically prove causation.",
]

for number, exercise in enumerate(exercises, start=1):
    print(f"{number}. {exercise}")


# ============================================================
# 66. FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL SUMMARY")
print("=" * 70)

summary = """
A professional Data Analyst is much more than a person who writes
Python code or creates dashboards.

The analyst must understand the business, communicate with
stakeholders, gather requirements, define problems, identify useful
metrics, validate data, analyze evidence, investigate causes,
communicate insights, and support decisions.

The fundamental progression is:

    Business problem
        ↓
    Analytical question
        ↓
    Data
        ↓
    Analysis
        ↓
    Insight
        ↓
    Recommendation
        ↓
    Decision
        ↓
    Outcome

The most important mindset is:

    Do not begin with the data.
    Begin with the decision.

Then determine what evidence is required to improve that decision.

A technically sophisticated analyst who solves the wrong problem
provides little value.

A strong Data Analyst combines:

    Business Understanding
    +
    Analytical Thinking
    +
    Technical Skills
    +
    Statistical Reasoning
    +
    Stakeholder Management
    +
    Problem Definition
    +
    Analytical Storytelling
    +
    Communication

That combination transforms data into business value.
"""

print(summary)


# ============================================================
# END OF PROGRAM
# ============================================================

print("=" * 70)
print("END OF DATA ANALYST ROLE LEARNING MODULE")
print("=" * 70)

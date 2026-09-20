<!-- File: README.md -->
# Excel Analytics Project: Sales Dataset Cleaning, KPI Calculation, Pivot Analysis, Dashboard Creation, and Business Recommendations

## Project purpose

This repository demonstrates an end-to-end sales analytics workflow built around an Excel-compatible management dashboard.

The project starts with a deliberately imperfect sales dataset. The raw records contain common data-quality problems such as inconsistent text formatting, missing category information, an invalid numeric value, a missing discount, and a duplicate order.

Python performs the repeatable data preparation and analytical work. The resulting workbook contains cleaned data, KPI calculations, pivot-style analysis tables, a dashboard, a data-quality report, and evidence-based business observations.

The project is designed to demonstrate how a business analyst can move from raw transactional data to an Excel reporting model without manually changing the original dataset.

## Project structure

The repository is organized as follows:

`data/raw_sales.csv` contains the intentionally imperfect source dataset.

`src/analytics.py` contains data loading, cleaning, KPI calculation, pivot-style analysis, and recommendation logic.

`src/create_workbook.py` creates the final Excel workbook.

`tests/test_analytics.py` verifies the analytical pipeline.

`output/` is created automatically when the workbook-generation script runs.

`.github/workflows/ci.yml` runs linting, tests, and workbook generation in GitHub Actions.

`Dockerfile` provides a reproducible environment for creating the workbook.

`pyproject.toml` contains Python project metadata, dependencies, pytest configuration, and Ruff configuration.

`requirements.txt` provides a simple dependency installation path.

`.env.example` documents optional runtime configuration.

## Prerequisites

Python 3.11 or newer is required.

Excel is useful for opening and interacting with the generated workbook, but Microsoft Excel is not required to run the Python analysis or generate the workbook.

The Python dependencies are:

- pandas for tabular data manipulation
- openpyxl for Excel workbook creation
- matplotlib for the Excel-compatible analytical environment and future chart extensions
- pytest for automated tests
- Ruff for linting

## Installation

Create a virtual environment:

`python -m venv .venv`

On Windows PowerShell, activate it with:

`.venv\Scripts\Activate.ps1`

On macOS or Linux, activate it with:

`source .venv/bin/activate`

Install dependencies:

`pip install -r requirements.txt`

## Configuration

The default configuration reads:

`data/raw_sales.csv`

and creates:

`output/sales_analytics_dashboard.xlsx`

The application supports these environment variables:

`DATA_PATH` changes the source CSV path.

`OUTPUT_DIR` changes the output directory.

`WORKBOOK_NAME` changes the generated workbook filename.

The `.env.example` file documents these variables. The application does not automatically load `.env`, which avoids introducing a hidden configuration dependency.

## Generate the Excel workbook

Run:

`python src/create_workbook.py`

The command creates:

`output/sales_analytics_dashboard.xlsx`

The workbook contains these worksheets:

- Dashboard
- Raw_Data
- Clean_Data
- KPI_Summary
- Data_Quality
- Pivot_Analysis
- Recommendations

## Raw dataset

The raw dataset represents sales transactions with these fields:

`order_id` identifies an order.

`order_date` stores the transaction date.

`product` identifies the item sold.

`category` groups products into Electronics, Furniture, or Stationery.

`region` identifies the sales region.

`salesperson` identifies the salesperson.

`city` identifies the customer or transaction city.

`quantity` records the number of units.

`unit_price` records the listed selling price per unit.

`discount_rate` records the discount as a decimal fraction.

`channel` identifies Online or Retail sales.

The dataset intentionally contains imperfect records. This makes the cleaning process observable instead of presenting an already-perfect dataset.

## Data cleaning

The cleaning process is implemented in `clean_sales_data()`.

### Text normalization

Text fields are converted to pandas string values and leading or trailing whitespace is removed.

For example, a region recorded as ` north ` becomes `north`.

This prevents visually identical values from being treated as different groups during aggregation.

### Date conversion

Dates are converted using pandas date parsing with invalid values converted to missing values instead of crashing the complete process.

The cleaned dataset therefore contains a consistent date representation.

### Numeric conversion

`quantity`, `unit_price`, and `discount_rate` are converted to numeric values.

The invalid `unit_price` value `bad` becomes a missing numeric value and is subsequently repaired using the product-level median.

### Missing category repair

A product-to-category mapping is used when category information is missing.

For example:

`Desk Lamp` maps to `Furniture`.

This approach is appropriate when product master data provides a reliable classification.

### Missing quantity repair

A missing quantity is first repaired using the median quantity for the same product.

If no product-level value is available, the overall median quantity is used.

Median values are used instead of averages because they are less sensitive to unusually large orders.

### Invalid price repair

A missing or invalid price is first repaired using the median unit price for the same product.

If a product-level median is unavailable, the overall median price is used.

This approach avoids inventing a price from an unrelated product.

### Missing discount repair

A missing discount rate is treated as zero.

This rule assumes that the absence of a discount in this demonstration dataset means that no discount was recorded.

In a production system, the business definition of a missing discount should be confirmed before applying the same rule.

### Duplicate removal

Duplicate records are removed using `order_id`.

The first occurrence is retained.

This is preferable to silently deleting records based on every column because an order identifier provides a business-level uniqueness rule.

### Range validation

Quantity and price are prevented from becoming negative.

Discount rates are constrained to the interval from zero through one.

A discount rate of `0.20` therefore represents 20%.

## Derived sales measures

The cleaned dataset adds several analytical columns.

### Gross sales

Gross sales are calculated as:

`quantity × unit_price`

For example, five units at 100 each produce gross sales of 500.

### Discount amount

Discount amount is:

`gross_sales × discount_rate`

For a gross sale of 500 with a 10% discount, the discount amount is 50.

### Net sales

Net sales are:

`gross_sales - discount_amount`

The previous example therefore produces net sales of 450.

### Month

The transaction date is converted into a month key such as `2026-03`.

This supports monthly trend analysis.

### Quarter

The transaction date is also converted into a quarter such as `2026Q1`.

This allows the same cleaned dataset to support quarterly analysis.

## KPI calculation

The KPI layer calculates the main measures normally used in a sales management report.

### Total orders

The number of unique order IDs.

### Units sold

The sum of all cleaned quantities.

### Gross sales

The total before discounts.

### Discount amount

The total monetary value of discounts.

### Net sales

The total after discounts.

### Average order value

Net sales divided by the number of unique orders.

### Average selling price

Net sales divided by total units.

### Discount rate

Total discount amount divided by gross sales.

These definitions are implemented in `calculate_kpis()` so that the same definitions are reused every time the report is generated.

## Pivot-style analysis

Excel PivotTables summarize dimensions and measures by grouping records.

This repository creates equivalent analytical tables with pandas so that the workbook can be reproduced automatically.

The analysis contains:

### Region analysis

Sales are grouped by region.

Measures include orders, units, gross sales, discounts, and net sales.

### Category analysis

Sales are grouped by product category.

This makes it possible to compare broad business segments.

### Product analysis

Sales are grouped by product and category.

This identifies products contributing substantial sales volume or revenue.

### Channel analysis

Sales are grouped into Online and Retail.

This permits channel-level comparison of order count, units, and net sales.

### Monthly analysis

Transactions are grouped by month.

This supports trend analysis and identification of periods with relatively higher or lower sales.

### Salesperson analysis

Transactions are grouped by salesperson.

The table can be used to inspect differences in order volume, units, and net sales.

### Region-category analysis

A two-dimensional pivot table crosses region with category.

This is useful when a category performs differently across geographic markets.

## Dashboard

The Dashboard worksheet presents the most important information in a management-oriented layout.

The KPI cards show:

- Net Sales
- Orders
- Units Sold
- Average Order Value
- Discount Rate

The dashboard also contains charts for:

- Net sales by region
- Net sales by category
- monthly net sales

The underlying analytical tables remain available in the workbook so that a user can inspect the numbers behind the charts.

## Data-quality report

The `Data_Quality` worksheet records how the raw dataset changed.

The report includes:

- input row count
- output row count
- duplicate rows removed
- missing categories repaired
- missing quantities repaired
- invalid prices repaired
- missing discounts repaired

This creates an audit trail for the cleaning stage.

## Business recommendations

The Recommendations worksheet does not use arbitrary business statements.

Each observation is calculated from the cleaned dataset.

The report examines:

- the region with the highest net sales
- the category with the highest net sales
- the highest-net-sales product
- the strongest sales channel by net sales
- differences in average order value between higher-discount and lower-discount orders

The recommendations are deliberately phrased as actions for investigation rather than unsupported claims about causality.

For example, a region with higher sales is evidence of higher observed sales in this dataset. It does not by itself prove that the region has better customers, better salespeople, better marketing, or greater future potential.

## Python implementation

`src/analytics.py` is the analytical core.

The main functions are:

`load_raw_data()` loads and validates the source dataset.

`clean_sales_data()` applies normalization, type conversion, missing-value repair, duplicate removal, and derived-field calculation.

`calculate_kpis()` calculates the business KPI table.

`create_pivots()` creates the grouped analytical tables.

`create_business_recommendations()` converts observed analytical results into structured business observations.

`run_analysis()` executes the complete analytical pipeline.

The use of functions keeps data preparation separate from workbook presentation.

## Excel implementation

`src/create_workbook.py` converts the analytical results into a structured Excel workbook using openpyxl.

The workbook separates:

- raw data
- cleaned data
- KPI calculations
- data-quality measurements
- pivot-style analysis
- dashboard presentation
- business observations

This separation is important because a reporting workbook becomes difficult to audit when raw records, calculations, and presentation are mixed into one worksheet.

The cleaned data is also stored as an Excel Table. This gives the workbook structured tabular behavior when opened in Excel.

## Testing

Run:

`pytest`

The tests cover:

- required source columns
- duplicate removal
- missing category repair
- invalid price repair
- missing discount repair
- calculated sales measures
- KPI presence
- pivot-table creation
- recommendation generation

The tests use the actual dataset included in the repository.

## Linting

Run:

`ruff check src tests`

The project uses Ruff for static code-quality checks.

The configuration is stored in `pyproject.toml`.

## Reproducibility

The analytical workflow is deterministic for a fixed source dataset.

The workbook can be regenerated after changing the raw dataset:

`python src/create_workbook.py`

The output directory is created automatically.

The generated `.xlsx` file is excluded from Git because it is a derived artifact.

## Architecture

The processing flow is:

`raw_sales.csv`

then:

`load_raw_data()`

then:

`clean_sales_data()`

then:

`calculate_kpis()`

and:

`create_pivots()`

then:

`create_business_recommendations()`

then:

`create_workbook.py`

then:

`sales_analytics_dashboard.xlsx`

This separation makes the workflow easier to test and maintain.

## Performance considerations

The implementation uses pandas vectorized operations for arithmetic and grouping.

The main aggregation operations are based on `groupby()` rather than Python-level loops over every transaction.

For a small or medium sales dataset, this approach is practical and easy to audit.

For substantially larger datasets, a production architecture may move raw storage and aggregation into a database or analytical warehouse and use Excel as the reporting layer rather than the primary processing engine.

The repository does not make a fixed performance claim because actual performance depends on data volume, hardware, storage, and workload.

## Edge cases

The cleaning pipeline handles:

- missing category values
- missing quantity values
- invalid numeric prices
- missing discount rates
- inconsistent whitespace
- mixed date formats
- duplicate order IDs
- negative numeric values
- discount rates outside the expected range
- empty required identifiers

Rows without a usable order ID, date, or product are removed because those records cannot be reliably attributed to a transaction.

## Common mistakes

Do not calculate revenue by summing unit prices.

Revenue requires quantity multiplied by unit price.

Do not calculate average order value using the number of rows if a single order can contain multiple rows.

Use unique order IDs when the business definition is order-level.

Do not compare regions before standardizing their text values.

Values such as `North`, ` north `, and `NORTH` should be normalized before grouping.

Do not treat a missing numeric value as zero unless the business meaning supports that decision.

A missing price and a genuine zero price represent different business conditions.

Do not interpret correlation or group-level differences as proof of causation.

For example, a higher average order value for discounted orders does not prove that discounts caused customers to spend more.

## Security considerations

The project does not require passwords, API keys, database credentials, or external service credentials.

The `.env` file is excluded from Git.

Only `.env.example` is intended to be committed.

The sample dataset contains synthetic business records and does not require protected credentials.

When adapting the repository to real business data, access control, data classification, retention policies, personal-data handling, and workbook distribution controls should be applied according to the organization's requirements.

## Docker

Build the image:

`docker build -t excel-sales-analytics .`

Run the analysis:

`docker run --rm -v "${PWD}/output:/app/output" excel-sales-analytics`

On Windows PowerShell, the same command can be run from the repository directory.

The container creates the workbook under `/app/output`, which is mapped to the local `output` directory.

The container runs the application as a non-root user.

## Continuous integration

GitHub Actions is configured in `.github/workflows/ci.yml`.

The workflow:

- checks out the repository
- installs Python
- installs dependencies
- runs Ruff
- runs pytest
- generates the Excel workbook
- verifies that the workbook exists

No deployment credentials are required.

## Production considerations

A production sales analytics solution would normally validate the source data against a documented data contract.

The following controls would be useful:

- unique transaction identifiers
- explicit product master data
- controlled region and category values
- defined discount rules
- currency definitions
- timezone rules for transaction timestamps
- documented revenue definitions
- automated data-quality thresholds
- reconciliation against source financial systems
- access control for confidential sales information
- scheduled report generation
- versioned business definitions

The Excel workbook should be treated as a reporting artifact. It should not become the authoritative financial system unless the organization has explicitly designed and controlled it for that purpose.

## Limitations

The dataset is intentionally small and educational.

It does not include cost of goods sold, gross margin, taxes, returns, refunds, customer IDs, inventory levels, targets, sales quotas, currency conversion, or marketing expenditure.

Because cost data is absent, the project does not calculate profit or margin.

Because the dataset is synthetic, observed patterns should not be interpreted as real market behavior.

The recommendations are descriptive and analytical. They do not establish causal relationships.

## License

This project is provided as an educational software repository. A production organization should add its own licensing terms before distributing modified versions commercially.

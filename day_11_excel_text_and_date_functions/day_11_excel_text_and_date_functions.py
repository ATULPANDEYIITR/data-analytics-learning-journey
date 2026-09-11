"""
Excel Text & Date Functions
===========================

A standalone Python study file for learning and practicing the Excel functions:

Text functions:
    LEFT, RIGHT, MID, LEN, TRIM, CLEAN, SUBSTITUTE, TEXT,
    CONCAT, TEXTJOIN

Date functions:
    DATE, YEAR, MONTH, DAY, EOMONTH

The examples use Python to reproduce the important ideas and behaviors of
the corresponding Excel functions. Excel formulas are shown in comments and
strings so that the relationship between Python and Excel remains explicit.

The script is intentionally self-contained and uses only Python's standard
library.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta
import re
import statistics
import unicodedata


# ============================================================================
# 1. BASIC TERMINOLOGY
# ============================================================================

def print_title(title: str) -> None:
    """Print a readable section heading."""
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def print_example(description: str, excel_formula: str, result) -> None:
    """Display an educational example."""
    print(f"\n{description}")
    print(f"Excel formula : {excel_formula}")
    print(f"Result        : {result!r}")


print_title("EXCEL TEXT & DATE FUNCTIONS")

print(
    """
This study file covers two major Excel function families.

Text functions manipulate characters and strings:
    LEFT, RIGHT, MID, LEN, TRIM, CLEAN, SUBSTITUTE, TEXT,
    CONCAT, TEXTJOIN

Date functions construct, inspect, and calculate calendar dates:
    DATE, YEAR, MONTH, DAY, EOMONTH

Important distinction:
    Excel stores dates as numeric serial values internally, while displaying
    them using date formats. Text that merely looks like a date is not
    necessarily a real Excel date value.

The Python examples below model the underlying concepts using strings and
datetime.date values.
"""
)


# ============================================================================
# 2. LEFT
# ============================================================================

print_title("2. LEFT")

def excel_left(text: str, num_chars: int = 1) -> str:
    """
    Approximate Excel LEFT(text, [num_chars]).

    Excel:
        =LEFT(A2, 4)

    Returns the leftmost number of characters.

    Important Excel behavior:
        - num_chars defaults to 1.
        - num_chars must be non-negative.
        - requesting more characters than exist returns the entire text.
        - an empty string returns an empty string.
    """
    if num_chars < 0:
        raise ValueError("Excel LEFT does not accept a negative num_chars.")
    if num_chars == 0:
        return ""
    return text[:num_chars]


name = "Atul Pandey"
print_example(
    "Extract the first four characters.",
    '=LEFT("Atul Pandey",4)',
    excel_left(name, 4),
)

print_example(
    "Extract the first character using the default count.",
    '=LEFT("Excel")',
    excel_left("Excel"),
)

print_example(
    "Request more characters than the text contains.",
    '=LEFT("ABC",10)',
    excel_left("ABC", 10),
)

print_example(
    "Request zero characters.",
    '=LEFT("ABC",0)',
    excel_left("ABC", 0),
)


# ============================================================================
# 3. RIGHT
# ============================================================================

print_title("3. RIGHT")

def excel_right(text: str, num_chars: int = 1) -> str:
    """
    Approximate Excel RIGHT(text, [num_chars]).

    Excel:
        =RIGHT(A2, 4)

    Returns the rightmost characters.
    """
    if num_chars < 0:
        raise ValueError("Excel RIGHT does not accept a negative num_chars.")
    if num_chars == 0:
        return ""
    return text[-num_chars:] if num_chars < len(text) else text


account_code = "INV-2026-00452"

print_example(
    "Extract the last five characters.",
    '=RIGHT("INV-2026-00452",5)',
    excel_right(account_code, 5),
)

print_example(
    "Extract the last character using the default count.",
    '=RIGHT("Excel")',
    excel_right("Excel"),
)


# ============================================================================
# 4. MID
# ============================================================================

print_title("4. MID")

def excel_mid(text: str, start_num: int, num_chars: int) -> str:
    """
    Approximate Excel MID(text, start_num, num_chars).

    Excel uses 1-based character positions.

    Python uses 0-based indexing, so the implementation converts:
        Excel start_num 1 -> Python index 0

    Excel:
        =MID(A2, 5, 4)

    returns four characters beginning at character position 5.
    """
    if start_num < 1:
        raise ValueError("Excel MID start_num must be at least 1.")
    if num_chars < 0:
        raise ValueError("Excel MID num_chars cannot be negative.")
    if num_chars == 0:
        return ""

    start_index = start_num - 1
    return text[start_index:start_index + num_chars]


product_code = "PRD-IND-2026-001"

print_example(
    "Extract the regional code.",
    '=MID("PRD-IND-2026-001",5,3)',
    excel_mid(product_code, 5, 3),
)

print_example(
    "Extract characters from beyond the end.",
    '=MID("ABC",10,5)',
    excel_mid("ABC", 10, 5),
)


# ============================================================================
# 5. LEN
# ============================================================================

print_title("5. LEN")

def excel_len(text: str) -> int:
    """
    Approximate Excel LEN(text).

    LEN counts characters, including spaces.

    Excel:
        =LEN(A2)
    """
    return len(text)


text_with_spaces = "  Excel Data  "

print_example(
    "Count every character, including spaces.",
    '=LEN("  Excel Data  ")',
    excel_len(text_with_spaces),
)

print_example(
    "Compare the length before and after trimming.",
    '=LEN(TRIM("  Excel Data  "))',
    excel_len("Excel Data"),
)


# ============================================================================
# 6. TRIM
# ============================================================================

print_title("6. TRIM")

def excel_trim(text: str) -> str:
    """
    Approximate Excel TRIM.

    Excel TRIM:
        - removes leading spaces
        - removes trailing spaces
        - reduces repeated internal ASCII spaces to one

    It does not fully solve every form of invisible or non-breaking
    whitespace. CLEAN and SUBSTITUTE may be required for imported data.
    """
    return " ".join(text.split(" "))


dirty_spacing = "   Atul    Pandey   Excel   "

print_example(
    "Remove leading/trailing spaces and reduce repeated spaces.",
    '=TRIM("   Atul    Pandey   Excel   ")',
    excel_trim(dirty_spacing),
)


# ============================================================================
# 7. CLEAN
# ============================================================================

print_title("7. CLEAN")

def excel_clean(text: str) -> str:
    """
    Approximate Excel CLEAN.

    Excel CLEAN removes non-printable characters in the range represented
    by ASCII control characters 0 through 31.

    This is especially useful for data imported from external systems.
    """
    return "".join(character for character in text if ord(character) >= 32)


dirty_control_text = "Customer\x0bName\x0d\x0aAtul"

print_example(
    "Remove control characters.",
    '=CLEAN("Customer<vertical-tab>Name<line-break>Atul")',
    excel_clean(dirty_control_text),
)


# ============================================================================
# 8. TRIM + CLEAN
# ============================================================================

print_title("8. TRIM AND CLEAN TOGETHER")

messy_import = "  Atul\x0d   Pandey\x0a   Excel  "

cleaned_import = excel_trim(excel_clean(messy_import))

print_example(
    "Clean imported text in two stages.",
    '=TRIM(CLEAN(A2))',
    cleaned_import,
)

print(
    """
A common data-cleaning pattern is:

    =TRIM(CLEAN(A2))

The two functions solve different problems:
    CLEAN -> removes non-printable control characters.
    TRIM  -> normalizes ordinary spaces.

For some imported web data, a non-breaking space (CHAR(160)) can remain.
A common Excel pattern is:

    =TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))

This replaces the non-breaking space with an ordinary space before cleaning.
"""
)


# ============================================================================
# 9. SUBSTITUTE
# ============================================================================

print_title("9. SUBSTITUTE")

def excel_substitute(
    text: str,
    old_text: str,
    new_text: str,
    instance_num: int | None = None,
) -> str:
    """
    Approximate Excel SUBSTITUTE(text, old_text, new_text, [instance_num]).

    Without instance_num:
        replace every occurrence.

    With instance_num:
        replace only that occurrence, counting from 1.
    """
    if instance_num is not None and instance_num <= 0:
        raise ValueError("instance_num must be positive.")

    if instance_num is None:
        return text.replace(old_text, new_text)

    occurrence = 0
    result = []
    position = 0

    while True:
        found = text.find(old_text, position)

        if found == -1:
            result.append(text[position:])
            break

        occurrence += 1

        if occurrence == instance_num:
            result.append(text[position:found])
            result.append(new_text)
            result.append(text[found + len(old_text):])
            break

        result.append(text[position:found])
        result.append(old_text)
        position = found + len(old_text)

    return "".join(result)


phone = "98765-43210"

print_example(
    "Remove all hyphens.",
    '=SUBSTITUTE("98765-43210","-","")',
    excel_substitute(phone, "-", ""),
)

print_example(
    "Replace only the second hyphen.",
    '=SUBSTITUTE("2026-09-11-REPORT","-","/",2)',
    excel_substitute("2026-09-11-REPORT", "-", "/", 2),
)

print_example(
    "Replace every occurrence of a word.",
    '=SUBSTITUTE("Data Data Data","Data","Excel")',
    excel_substitute("Data Data Data", "Data", "Excel"),
)


# ============================================================================
# 10. TEXT
# ============================================================================

print_title("10. TEXT")

def excel_text(value, format_code: str) -> str:
    """
    Educational implementation of common Excel TEXT formatting patterns.

    Excel:
        =TEXT(A2,"0.00")
        =TEXT(A2,"#,##0.00")
        =TEXT(A2,"dd-mm-yyyy")
        =TEXT(A2,"mmm yyyy")
        =TEXT(A2,"0.0%")

    Excel's complete custom-format system is much larger than this teaching
    implementation. The function below intentionally implements common
    numeric and date patterns used in practical worksheets.
    """
    if isinstance(value, datetime):
        value = value.date()

    if isinstance(value, date):
        replacements = {
            "yyyy": f"{value.year:04d}",
            "yy": f"{value.year % 100:02d}",
            "mmmm": value.strftime("%B"),
            "mmm": value.strftime("%b"),
            "mm": f"{value.month:02d}",
            "dd": f"{value.day:02d}",
            "d": str(value.day),
        }

        result = format_code

        # Replace longer tokens first.
        for token in ["yyyy", "mmmm", "mmm", "yy", "mm", "dd", "d"]:
            result = result.replace(token, replacements[token])

        return result

    if isinstance(value, (int, float)):
        if "%" in format_code:
            decimals = 0
            if "." in format_code:
                decimals = len(format_code.split(".")[1].replace("%", ""))
            return f"{value * 100:.{decimals}f}%"

        if "," in format_code:
            if "." in format_code:
                decimals = len(format_code.split(".")[1])
            else:
                decimals = 0
            return f"{value:,.{decimals}f}"

        if "." in format_code:
            decimals = len(format_code.split(".")[1])
            return f"{value:.{decimals}f}"

        return str(round(value))

    return str(value)


salary = 1250000.5
transaction_date = date(2026, 9, 11)

print_example(
    "Format a number with thousands separators and two decimals.",
    '=TEXT(1250000.5,"#,##0.00")',
    excel_text(salary, "#,##0.00"),
)

print_example(
    "Format a number as a percentage.",
    '=TEXT(0.1845,"0.0%")',
    excel_text(0.1845, "0.0%"),
)

print_example(
    "Format a date.",
    '=TEXT(DATE(2026,9,11),"dd-mm-yyyy")',
    excel_text(transaction_date, "dd-mm-yyyy"),
)

print_example(
    "Format a month and year.",
    '=TEXT(DATE(2026,9,11),"mmm yyyy")',
    excel_text(transaction_date, "mmm yyyy"),
)

print(
    """
TEXT converts a value into formatted text.

This is important:

    =TEXT(A2,"#,##0.00")

does not return a numeric value suitable for ordinary arithmetic. It returns
text that looks like a formatted number.

Therefore:

    =A2*2

and

    =TEXT(A2,"#,##0.00")

serve different purposes.

Use TEXT primarily when a value needs to be embedded into readable text.
"""


# ============================================================================
# 11. CONCAT
# ============================================================================

print_title("11. CONCAT")

def excel_concat(*values) -> str:
    """
    Approximate Excel CONCAT.

    Excel:
        =CONCAT(A2," ",B2)

    CONCAT combines supplied values without automatically adding separators.
    """
    return "".join("" if value is None else str(value) for value in values)


first_name = "Atul"
last_name = "Pandey"

print_example(
    "Combine first and last names.",
    '=CONCAT(A2," ",B2)',
    excel_concat(first_name, " ", last_name),
)

print_example(
    "Combine several pieces without separators.",
    '=CONCAT("INV-",2026,"-",452)',
    excel_concat("INV-", 2026, "-", 452),
)


# ============================================================================
# 12. TEXTJOIN
# ============================================================================

print_title("12. TEXTJOIN")

def excel_textjoin(
    delimiter: str,
    ignore_empty: bool,
    *values,
) -> str:
    """
    Approximate Excel TEXTJOIN(delimiter, ignore_empty, text1, ...).

    Example:
        =TEXTJOIN(", ",TRUE,A2:A5)

    When ignore_empty is TRUE, empty strings and None values are skipped.
    """
    pieces = []

    for value in values:
        if value is None:
            if ignore_empty:
                continue
            pieces.append("")
            continue

        value = str(value)

        if ignore_empty and value == "":
            continue

        pieces.append(value)

    return delimiter.join(pieces)


skills = ["Python", "", "SQL", None, "Excel"]

print_example(
    "Join non-empty skills using commas.",
    '=TEXTJOIN(", ",TRUE,A2:E2)',
    excel_textjoin(", ", True, *skills),
)

print_example(
    "Join values while preserving empty positions.",
    '=TEXTJOIN("|",FALSE,A2:E2)',
    excel_textjoin("|", False, *skills),
)


# ============================================================================
# 13. TEXT FUNCTION COMPARISON
# ============================================================================

print_title("13. TEXT FUNCTION COMPARISON")

comparison = {
    "LEFT": "Extract characters from the beginning.",
    "RIGHT": "Extract characters from the end.",
    "MID": "Extract characters from a specified position.",
    "LEN": "Count characters.",
    "TRIM": "Normalize ordinary spaces.",
    "CLEAN": "Remove non-printable control characters.",
    "SUBSTITUTE": "Replace matching text.",
    "TEXT": "Convert a value into formatted text.",
    "CONCAT": "Join text without automatically adding separators.",
    "TEXTJOIN": "Join text using a delimiter, with optional empty-value handling.",
}

for function_name, purpose in comparison.items():
    print(f"{function_name:12} -> {purpose}")


# ============================================================================
# 14. PRACTICAL TEXT CLEANING PIPELINE
# ============================================================================

print_title("14. PRACTICAL TEXT CLEANING PIPELINE")

raw_customer = "  Atul\x0d Pandey   "

step_1 = excel_clean(raw_customer)
step_2 = excel_trim(step_1)
step_3 = excel_substitute(step_2, " ", "_")

print("Raw value       :", repr(raw_customer))
print("After CLEAN     :", repr(step_1))
print("After TRIM      :", repr(step_2))
print("After SUBSTITUTE:", repr(step_3))

print(
    """
A practical sequence can be:

    =TRIM(CLEAN(A2))

followed by targeted SUBSTITUTE operations when a specific character,
separator, or unwanted value must be changed.
"""
)


# ============================================================================
# 15. DATE
# ============================================================================

print_title("15. DATE")

def excel_date(year: int, month: int, day: int) -> date:
    """
    Model Excel DATE(year, month, day).

    Excel DATE has an important normalization behavior:
        month 13 becomes January of the following year.
        day 0 means the final day of the previous month.

    Python's date constructor does not accept these normalized values directly,
    so this implementation explicitly reproduces the useful Excel behavior.
    """
    if not all(isinstance(value, int) for value in (year, month, day)):
        raise TypeError("DATE components must be integers in this model.")

    # Normalize the month into the range 1..12.
    normalized_year = year + (month - 1) // 12
    normalized_month = (month - 1) % 12 + 1

    first_day = date(normalized_year, normalized_month, 1)
    return first_day + timedelta(days=day - 1)


created_date = excel_date(2026, 9, 11)

print_example(
    "Construct a date.",
    '=DATE(2026,9,11)',
    created_date,
)

print_example(
    "Demonstrate month normalization.",
    '=DATE(2026,13,15)',
    excel_date(2026, 13, 15),
)

print_example(
    "Demonstrate day zero.",
    '=DATE(2026,9,0)',
    excel_date(2026, 9, 0),
)

print(
    """
DATE is preferable to manually assembling date text because it creates an
actual date value.

Example:

    =DATE(2026,9,11)

is a date value.

By contrast:

    ="11/09/2026"

is text.

This distinction matters when sorting, comparing, calculating intervals,
filtering, and applying date functions.
"""
)


# ============================================================================
# 16. YEAR
# ============================================================================

print_title("16. YEAR")

def excel_year(value: date | datetime) -> int:
    """Model Excel YEAR(serial_number)."""
    if isinstance(value, datetime):
        value = value.date()
    return value.year


print_example(
    "Extract the year.",
    '=YEAR(DATE(2026,9,11))',
    excel_year(created_date),
)


# ============================================================================
# 17. MONTH
# ============================================================================

print_title("17. MONTH")

def excel_month(value: date | datetime) -> int:
    """Model Excel MONTH(serial_number)."""
    if isinstance(value, datetime):
        value = value.date()
    return value.month


print_example(
    "Extract the month number.",
    '=MONTH(DATE(2026,9,11))',
    excel_month(created_date),
)


# ============================================================================
# 18. DAY
# ============================================================================

print_title("18. DAY")

def excel_day(value: date | datetime) -> int:
    """Model Excel DAY(serial_number)."""
    if isinstance(value, datetime):
        value = value.date()
    return value.day


print_example(
    "Extract the day number.",
    '=DAY(DATE(2026,9,11))',
    excel_day(created_date),
)


# ============================================================================
# 19. DATE COMPONENT EXTRACTION
# ============================================================================

print_title("19. YEAR + MONTH + DAY")

for label, function, formula in [
    ("Year", excel_year, '=YEAR(DATE(2026,9,11))'),
    ("Month", excel_month, '=MONTH(DATE(2026,9,11))'),
    ("Day", excel_day, '=DAY(DATE(2026,9,11))'),
]:
    print(f"{label:6}: {function(created_date)} | {formula}")


# ============================================================================
# 20. EOMONTH
# ============================================================================

print_title("20. EOMONTH")

def excel_eomonth(start_date: date | datetime, months: int) -> date:
    """
    Model Excel EOMONTH(start_date, months).

    It returns the last day of the month that is a specified number of months
    before or after the starting date.

    Examples:
        =EOMONTH(DATE(2026,9,11),0)
            -> 30-Sep-2026

        =EOMONTH(DATE(2026,9,11),1)
            -> 31-Oct-2026

        =EOMONTH(DATE(2026,9,11),-1)
            -> 31-Aug-2026
    """
    if isinstance(start_date, datetime):
        start_date = start_date.date()

    target_month_index = start_date.year * 12 + (start_date.month - 1) + months
    target_year = target_month_index // 12
    target_month = target_month_index % 12 + 1

    final_day = monthrange(target_year, target_month)[1]
    return date(target_year, target_month, final_day)


print_example(
    "Last day of the current month.",
    '=EOMONTH(DATE(2026,9,11),0)',
    excel_eomonth(created_date, 0),
)

print_example(
    "Last day of the following month.",
    '=EOMONTH(DATE(2026,9,11),1)',
    excel_eomonth(created_date, 1),
)

print_example(
    "Last day of the previous month.",
    '=EOMONTH(DATE(2026,9,11),-1)',
    excel_eomonth(created_date, -1),
)


# ============================================================================
# 21. EOMONTH FOR MONTH-END BUSINESS LOGIC
# ============================================================================

print_title("21. EOMONTH IN BUSINESS LOGIC")

invoice_date = date(2026, 9, 11)
month_end = excel_eomonth(invoice_date, 0)
previous_month_end = excel_eomonth(invoice_date, -1)
next_month_end = excel_eomonth(invoice_date, 1)

print("Invoice date       :", invoice_date)
print("Previous month end:", previous_month_end)
print("Current month end :", month_end)
print("Next month end    :", next_month_end)

print(
    """
EOMONTH is useful for:
    - monthly reporting
    - accounting periods
    - month-end balances
    - subscription cycles
    - financial models
    - invoice cut-off dates
    - portfolio reporting
    - monthly KPI calculations
"""
)


# ============================================================================
# 22. DATE FUNCTION COMBINATION
# ============================================================================

print_title("22. DATE FUNCTION COMBINATIONS")

transaction = date(2026, 9, 11)

print(
    "Transaction date :", transaction,
    "\nYear             :", excel_year(transaction),
    "\nMonth            :", excel_month(transaction),
    "\nDay              :", excel_day(transaction),
    "\nMonth end        :", excel_eomonth(transaction, 0),
)

formula_description = """
Excel equivalent:

    =DATE(2026,9,11)
    =YEAR(A2)
    =MONTH(A2)
    =DAY(A2)
    =EOMONTH(A2,0)
"""
print(formula_description)


# ============================================================================
# 23. TEXT + DATE
# ============================================================================

print_title("23. TEXT + DATE")

report_date = excel_date(2026, 9, 11)

formatted_date = excel_text(report_date, "dd-mm-yyyy")
month_label = excel_text(report_date, "mmm yyyy")

print_example(
    "Create a readable date label.",
    '=TEXT(DATE(2026,9,11),"dd-mm-yyyy")',
    formatted_date,
)

print_example(
    "Create a reporting-period label.",
    '=TEXT(DATE(2026,9,11),"mmm yyyy")',
    month_label,
)


# ============================================================================
# 24. CONCAT + TEXT
# ============================================================================

print_title("24. CONCAT + TEXT")

employee = "Atul Pandey"
joining_date = date(2026, 9, 11)

employee_label = excel_concat(
    employee,
    " | Joined: ",
    excel_text(joining_date, "dd-mm-yyyy"),
)

print_example(
    "Combine a name and formatted date.",
    '=CONCAT(A2," | Joined: ",TEXT(B2,"dd-mm-yyyy"))',
    employee_label,
)


# ============================================================================
# 25. TEXTJOIN + TEXT
# ============================================================================

print_title("25. TEXTJOIN + TEXT")

report_items = [
    "Revenue: " + excel_text(1250000.50, "#,##0.00"),
    "Growth: " + excel_text(0.1845, "0.0%"),
    "Date: " + excel_text(date(2026, 9, 11), "dd-mm-yyyy"),
]

joined_report = excel_textjoin(" | ", True, *report_items)

print_example(
    "Build a compact report string.",
    '=TEXTJOIN(" | ",TRUE,A2:C2)',
    joined_report,
)


# ============================================================================
# 26. REAL-WORLD DATA CLEANING EXAMPLE
# ============================================================================

print_title("26. REAL-WORLD DATA CLEANING EXAMPLE")

raw_records = [
    "  ATUL   PANDEY  ",
    "ATUL\x0d PANDEY",
    "  ATUL\x0aPANDEY  ",
    "ATUL\x0b   PANDEY",
]

print("Raw records:")
for record in raw_records:
    print(repr(record))

print("\nCleaned records:")
cleaned_records = []

for record in raw_records:
    cleaned = excel_trim(excel_clean(record))
    cleaned_records.append(cleaned)
    print(repr(cleaned))


# ============================================================================
# 27. EXTRACTING PARTS OF AN IDENTIFIER
# ============================================================================

print_title("27. EXTRACTING PARTS OF AN IDENTIFIER")

identifier = "EMP-IND-2026-00452"

prefix = excel_left(identifier, 3)
country = excel_mid(identifier, 5, 3)
year = excel_mid(identifier, 9, 4)
employee_number = excel_right(identifier, 5)

print("Identifier      :", identifier)
print("Prefix          :", prefix)
print("Country         :", country)
print("Year            :", year)
print("Employee number :", employee_number)

print(
    """
Equivalent Excel formulas:

    =LEFT(A2,3)
    =MID(A2,5,3)
    =MID(A2,9,4)
    =RIGHT(A2,5)
"""
)


# ============================================================================
# 28. DYNAMIC EXTRACTION USING FIND
# ============================================================================

print_title("28. DYNAMIC TEXT EXTRACTION")

def excel_find(find_text: str, within_text: str, start_num: int = 1) -> int:
    """
    Approximate Excel FIND.

    FIND is case-sensitive and returns a 1-based position.
    """
    if start_num < 1:
        raise ValueError("start_num must be at least 1.")

    position = within_text.find(find_text, start_num - 1)

    if position == -1:
        raise ValueError("The requested text was not found.")

    return position + 1


email = "atul.pandey@example.com"

at_position = excel_find("@", email)
username = excel_left(email, at_position - 1)
domain = excel_right(email, len(email) - at_position)

print("Email    :", email)
print("Username :", username)
print("Domain   :", domain)

print(
    """
Although FIND is not one of the requested primary functions, it is closely
related to MID, LEFT, and RIGHT.

A common Excel pattern is:

    =LEFT(A2,FIND("@",A2)-1)

This extracts the part before @.

The important design principle is that extraction becomes more robust when
the number of characters is derived from a delimiter rather than hard-coded.
"""
)


# ============================================================================
# 29. SUBSTITUTE FOR STANDARDIZING CODES
# ============================================================================

print_title("29. SUBSTITUTE FOR STANDARDIZING CODES")

codes = [
    "INV/2026/001",
    "INV-2026-002",
    "INV 2026 003",
]

for code in codes:
    standardized = excel_substitute(code, "/", "-")
    standardized = excel_substitute(standardized, " ", "-")
    print(f"{code!r:20} -> {standardized!r}")


# ============================================================================
# 30. DATE VALIDATION
# ============================================================================

print_title("30. DATE VALIDATION")

def is_valid_date(year: int, month: int, day: int) -> bool:
    """Check whether a calendar date is valid."""
    try:
        date(year, month, day)
        return True
    except ValueError:
        return False


date_candidates = [
    (2026, 2, 28),
    (2026, 2, 29),
    (2024, 2, 29),
    (2026, 13, 1),
]

for year, month, day in date_candidates:
    print(
        f"{year:04d}-{month:02d}-{day:02d} -> "
        f"{is_valid_date(year, month, day)}"
    )

print(
    """
Validation matters because a date-looking value can be invalid.

For example:
    2026-02-29

is not a valid Gregorian calendar date because 2026 is not a leap year.

Excel's DATE function can normalize some out-of-range components, while
manual date entry or date validation may behave differently. Understanding
this distinction prevents subtle data-quality errors.
"""
)


# ============================================================================
# 31. LEAP YEAR LOGIC
# ============================================================================

print_title("31. LEAP YEAR AND EOMONTH")

def is_leap_year(year: int) -> bool:
    """Return whether a year is a Gregorian leap year."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


for year in [2024, 2025, 2100, 2000]:
    print(
        f"{year}: leap year={is_leap_year(year)}, "
        f"February days={monthrange(year, 2)[1]}"
    )

print(
    """
EOMONTH automatically handles leap years.

For example:

    =EOMONTH(DATE(2024,2,10),0)

returns 29-Feb-2024, while:

    =EOMONTH(DATE(2025,2,10),0)

returns 28-Feb-2025.
"""
)


# ============================================================================
# 32. MONTH-END REPORTING
# ============================================================================

print_title("32. MONTH-END REPORTING")

sales_dates = [
    date(2026, 9, 2),
    date(2026, 9, 11),
    date(2026, 9, 29),
    date(2026, 10, 1),
]

for transaction_date in sales_dates:
    month_end = excel_eomonth(transaction_date, 0)
    period_label = excel_text(transaction_date, "mmm yyyy")
    print(
        f"{transaction_date} -> "
        f"period={period_label}, month_end={month_end}"
    )


# ============================================================================
# 33. TEXT FUNCTIONS AND DATA TYPES
# ============================================================================

print_title("33. TEXT VERSUS NUMERIC VALUES")

numeric_value = 1250.5
formatted_value = excel_text(numeric_value, "#,##0.00")

print("Original value :", numeric_value)
print("Python type    :", type(numeric_value).__name__)
print("Formatted value:", formatted_value)
print("Python type    :", type(formatted_value).__name__)

print(
    """
The same principle applies in Excel:

    A1 = 1250.5

    =A1*2

performs arithmetic.

But:

    =TEXT(A1,"#,##0.00")

returns text.

Formatting and calculation are therefore separate concerns.
"""
)


# ============================================================================
# 34. EMPTY VALUES
# ============================================================================

print_title("34. EMPTY VALUES")

values = ["Atul", "", None, "Pandey"]

print("Values:", values)
print(
    "TEXTJOIN ignoring empty values:",
    excel_textjoin(", ", True, *values),
)
print(
    "TEXTJOIN preserving empty positions:",
    excel_textjoin(", ", False, *values),
)

print(
    """
Empty cells deserve attention.

TEXTJOIN has an explicit ignore_empty argument:

    =TEXTJOIN(", ",TRUE,A2:D2)

TRUE skips empty cells.

FALSE preserves their positions in the joined sequence.

CONCAT does not provide the same delimiter-and-ignore-empty behavior.
"""
)


# ============================================================================
# 35. UNICODE AND INVISIBLE CHARACTERS
# ============================================================================

print_title("35. UNICODE AND INVISIBLE CHARACTERS")

non_breaking_space = "\u00a0"

web_import = f"Atul{non_breaking_space}Pandey"

print("Raw text:", repr(web_import))
print("Ordinary Python split result:", web_import.split())

# Excel commonly requires SUBSTITUTE(CHAR(160)," ") for this kind of data.
normalized = web_import.replace(non_breaking_space, " ")
normalized = excel_trim(normalized)

print("After replacing non-breaking space:", repr(normalized))

print(
    """
A subtle data-cleaning issue is the difference between:
    ordinary space:       U+0020
    non-breaking space:   U+00A0

A value can appear visually correct while still containing a different
character.

A practical Excel formula is:

    =TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))

This is particularly relevant to copied web data and exported reports.
"""
)


# ============================================================================
# 36. CASE SENSITIVITY AND SUBSTITUTE
# ============================================================================

print_title("36. SUBSTITUTE AND CASE")

case_text = "Excel excel EXCEL"

print(
    "Replace lowercase 'excel':",
    excel_substitute(case_text, "excel", "Python"),
)

print(
    """
SUBSTITUTE is case-sensitive.

For example:

    =SUBSTITUTE("Excel excel EXCEL","excel","Python")

does not replace "Excel" or "EXCEL".

This distinction is important when cleaning inconsistent datasets.
A case-insensitive replacement usually requires additional logic.
"""
)


# ============================================================================
# 37. REUSABLE TEXT CLEANING FUNCTION
# ============================================================================

print_title("37. REUSABLE TEXT CLEANING FUNCTION")

def clean_business_text(text: str) -> str:
    """
    Combine common cleaning operations.

    Conceptual Excel equivalent:
        =TRIM(CLEAN(SUBSTITUTE(A2,CHAR(160)," ")))
    """
    text = text.replace("\u00a0", " ")
    text = excel_clean(text)
    text = excel_trim(text)
    return text


business_values = [
    "  Atul\x0d Pandey  ",
    f"Atul{non_breaking_space}Pandey",
    "   Excel   SQL   Python   ",
]

for value in business_values:
    print(repr(value), "->", repr(clean_business_text(value)))


# ============================================================================
# 38. COMBINING TEXT AND DATES FOR REPORT LABELS
# ============================================================================

print_title("38. REPORT LABEL GENERATION")

report_month = date(2026, 9, 11)
revenue = 1850250.75
growth = 0.127

report_label = excel_concat(
    "Sales Report - ",
    excel_text(report_month, "mmm yyyy"),
)

report_details = excel_textjoin(
    " | ",
    True,
    report_label,
    "Revenue: " + excel_text(revenue, "#,##0.00"),
    "Growth: " + excel_text(growth, "0.0%"),
    "Month end: " + excel_text(excel_eomonth(report_month, 0), "dd-mm-yyyy"),
)

print(report_details)


# ============================================================================
# 39. FUNCTION COMPOSITION
# ============================================================================

print_title("39. FUNCTION COMPOSITION")

compound_value = "   EMP-IND-2026-00452   "

cleaned_code = excel_trim(excel_clean(compound_value))
code_year = excel_mid(cleaned_code, 9, 4)
code_suffix = excel_right(cleaned_code, 5)

print("Original :", repr(compound_value))
print("Cleaned  :", cleaned_code)
print("Year     :", code_year)
print("Suffix   :", code_suffix)

print(
    """
Excel functions become especially powerful when nested.

Examples:

    =LEFT(TRIM(CLEAN(A2)),3)

    =RIGHT(TRIM(CLEAN(A2)),5)

    =TEXT(DATE(2026,MONTH(A2),DAY(A2)),"mmm dd")

The inner function is evaluated first, and its result becomes the input to
the outer function.
"""
)


# ============================================================================
# 40. PRACTICAL EMPLOYEE DATASET
# ============================================================================

print_title("40. PRACTICAL EMPLOYEE DATASET")

employees = [
    {
        "employee_code": "EMP-IND-2026-00101",
        "name": "  Atul   Pandey ",
        "joining_date": date(2026, 1, 15),
        "salary": 850000,
    },
    {
        "employee_code": "EMP-IND-2026-00102",
        "name": " Priya   Sharma ",
        "joining_date": date(2026, 3, 7),
        "salary": 920000,
    },
    {
        "employee_code": "EMP-USA-2026-00103",
        "name": "  John   Smith",
        "joining_date": date(2026, 7, 22),
        "salary": 1100000,
    },
]

for employee in employees:
    employee["clean_name"] = clean_business_text(employee["name"])
    employee["country"] = excel_mid(employee["employee_code"], 5, 3)
    employee["employee_number"] = excel_right(employee["employee_code"], 5)
    employee["joining_month"] = excel_text(
        employee["joining_date"],
        "mmm yyyy",
    )
    employee["month_end"] = excel_eomonth(
        employee["joining_date"],
        0,
    )
    employee["salary_text"] = excel_text(
        employee["salary"],
        "#,##0",
    )

    print(
        excel_textjoin(
            " | ",
            True,
            employee["clean_name"],
            employee["country"],
            employee["employee_number"],
            employee["joining_month"],
            "Salary: " + employee["salary_text"],
            "Month end: " + str(employee["month_end"]),
        )
    )


# ============================================================================
# 41. EDGE CASES FOR TEXT FUNCTIONS
# ============================================================================

print_title("41. TEXT FUNCTION EDGE CASES")

text_edge_cases = [
    ("", 3),
    ("ABC", 0),
    ("ABC", 10),
    ("A", 1),
    ("A", 10),
]

for text, count in text_edge_cases:
    print(
        f"LEFT({text!r}, {count}) = {excel_left(text, count)!r}; "
        f"RIGHT({text!r}, {count}) = {excel_right(text, count)!r}"
    )

print(
    """
Important edge cases:
    - empty strings
    - zero character requests
    - character counts larger than the source text
    - leading/trailing spaces
    - control characters
    - Unicode whitespace
    - inconsistent delimiters
    - missing delimiters

Hard-coded extraction lengths are fragile when source formats change.
Delimiter-based extraction is usually more maintainable.
"""
)


# ============================================================================
# 42. EDGE CASES FOR DATE FUNCTIONS
# ============================================================================

print_title("42. DATE FUNCTION EDGE CASES")

date_cases = [
    date(2026, 1, 31),
    date(2026, 2, 28),
    date(2026, 12, 31),
    date(2024, 2, 29),
]

for value in date_cases:
    print(
        f"{value} -> "
        f"YEAR={excel_year(value)}, "
        f"MONTH={excel_month(value)}, "
        f"DAY={excel_day(value)}, "
        f"EOMONTH(0)={excel_eomonth(value, 0)}"
    )

print(
    """
Month length is not constant.

A month can contain:
    28 days
    29 days
    30 days
    31 days

Therefore, adding 30 days is not equivalent to adding one calendar month.

EOMONTH is designed for calendar-month calculations.
"""
)


# ============================================================================
# 43. MONTH OFFSET COMPARISON
# ============================================================================

print_title("43. MONTH OFFSETS")

base_date = date(2026, 9, 15)

for offset in [-3, -2, -1, 0, 1, 2, 3, 12]:
    result = excel_eomonth(base_date, offset)
    print(f"Offset {offset:>3}: {result}")


# ============================================================================
# 44. FINANCIAL REPORTING PERIODS
# ============================================================================

print_title("44. FINANCIAL REPORTING PERIODS")

transactions = [
    date(2026, 9, 1),
    date(2026, 9, 30),
    date(2026, 10, 1),
    date(2026, 12, 31),
]

for transaction_date in transactions:
    period_start = date(
        transaction_date.year,
        transaction_date.month,
        1,
    )
    period_end = excel_eomonth(transaction_date, 0)

    print(
        f"{transaction_date} -> "
        f"{period_start} to {period_end}"
    )


# ============================================================================
# 45. QUARTER IDENTIFICATION
# ============================================================================

print_title("45. QUARTER IDENTIFICATION")

def quarter_from_date(value: date) -> int:
    """Return calendar quarter number 1 through 4."""
    return (value.month - 1) // 3 + 1


for value in [
    date(2026, 1, 15),
    date(2026, 4, 10),
    date(2026, 7, 20),
    date(2026, 12, 31),
]:
    quarter = quarter_from_date(value)
    label = excel_concat(
        "Q",
        quarter,
        " ",
        excel_year(value),
    )
    print(value, "->", label)


# ============================================================================
# 46. DATE SERIAL CONCEPT
# ============================================================================

print_title("46. EXCEL DATE SERIAL CONCEPT")

excel_epoch = date(1899, 12, 30)

def excel_serial_from_date(value: date) -> int:
    """
    Approximate the common Excel 1900-date-system serial representation.

    Excel historically contains the 1900 leap-year compatibility bug. Using
    1899-12-30 as a practical conversion epoch reproduces common modern
    worksheet serial calculations for ordinary dates.
    """
    return (value - excel_epoch).days


def date_from_excel_serial(serial: int) -> date:
    """Convert an ordinary Excel-style serial number back to a date."""
    return excel_epoch + timedelta(days=serial)


serial_date = date(2026, 9, 11)
serial = excel_serial_from_date(serial_date)

print("Date  :", serial_date)
print("Serial:", serial)
print("Back  :", date_from_excel_serial(serial))

print(
    """
Excel's date system is important because dates are stored as numbers with
formatting applied for display.

This explains why dates can participate in arithmetic.

For example:

    =B2-A2

can return the number of days between two dates.

Formatting changes how the result is displayed, not the underlying concept
of the date value itself.
"""
)


# ============================================================================
# 47. TEXT FUNCTION FORMATTING PITFALL
# ============================================================================

print_title("47. TEXT FORMATTING PITFALL")

amount = 1500000
amount_as_text = excel_text(amount, "#,##0")

print("Numeric amount :", amount)
print("Formatted text :", amount_as_text)

print(
    """
A common mistake is to use TEXT too early.

If a numeric value must still participate in calculations, keep it numeric.

Prefer:

    A2 = 1500000
    B2 = A2 * 0.18

and format B2 using cell formatting.

Use:

    =TEXT(A2,"#,##0")

when the formatted result must become part of a sentence or label.
"""
)


# ============================================================================
# 48. CONCAT VS TEXTJOIN
# ============================================================================

print_title("48. CONCAT VS TEXTJOIN")

parts = ["Atul", "", "Pandey", "India"]

concat_result = excel_concat(*parts)
textjoin_result = excel_textjoin(" | ", True, *parts)

print("CONCAT   :", repr(concat_result))
print("TEXTJOIN :", repr(textjoin_result))

print(
    """
CONCAT is useful when the exact sequence is known and separators are
explicitly supplied.

TEXTJOIN is preferable when:
    - one delimiter should be applied repeatedly
    - empty values should optionally be ignored
    - many fields need to be combined

For large lists, TEXTJOIN often expresses the intended logic more clearly.
"""
)


# ============================================================================
# 49. COMMON MISTAKES
# ============================================================================

print_title("49. COMMON MISTAKES")

mistakes = [
    (
        "Confusing MID position with Python indexing",
        "Excel character positions start at 1; Python indexes start at 0.",
    ),
    (
        "Assuming LEN ignores spaces",
        "LEN counts spaces.",
    ),
    (
        "Expecting TRIM to remove every invisible character",
        "TRIM primarily handles ordinary spaces; CLEAN handles control characters.",
    ),
    (
        "Assuming SUBSTITUTE is case-insensitive",
        "SUBSTITUTE is case-sensitive.",
    ),
    (
        "Using TEXT when a number is still needed",
        "TEXT returns formatted text.",
    ),
    (
        "Joining text without a deliberate delimiter",
        "CONCAT does not automatically insert spaces or commas.",
    ),
    (
        "Treating a date-looking string as a date value",
        "Text and actual Excel date values behave differently.",
    ),
    (
        "Adding 30 days to represent one month",
        "Calendar months have different lengths.",
    ),
    (
        "Hard-coding text positions unnecessarily",
        "Delimiter-driven extraction is often more robust.",
    ),
]

for mistake, explanation in mistakes:
    print(f"\nMistake: {mistake}\nReason : {explanation}")


# ============================================================================
# 50. ERROR HANDLING
# ============================================================================

print_title("50. ERROR HANDLING")

invalid_operations = [
    ("LEFT negative count", lambda: excel_left("ABC", -1)),
    ("RIGHT negative count", lambda: excel_right("ABC", -1)),
    ("MID invalid start", lambda: excel_mid("ABC", 0, 2)),
    ("MID negative count", lambda: excel_mid("ABC", 1, -1)),
    ("SUBSTITUTE invalid occurrence", lambda: excel_substitute("ABC", "A", "X", 0)),
    ("FIND missing delimiter", lambda: excel_find("@", "example.com")),
]

for description, operation in invalid_operations:
    try:
        print(description, "->", operation())
    except (ValueError, TypeError) as error:
        print(description, "-> ERROR:", error)


# ============================================================================
# 51. PERFORMANCE CONSIDERATIONS
# ============================================================================

print_title("51. PERFORMANCE CONSIDERATIONS")

print(
    """
Text functions are usually inexpensive for ordinary worksheet datasets, but
performance can matter when they are applied across hundreds of thousands or
millions of cells.

Practical considerations:

1. Avoid repeatedly applying the same expensive transformation.
2. Clean source data once when possible.
3. Avoid deeply nested formulas when a helper column improves readability.
4. Avoid volatile functions when they are not necessary.
5. Prefer structured transformations for repeatable ETL workflows.
6. Keep raw data separate from cleaned and reporting layers.
7. Use Excel Tables and structured references where appropriate.
8. Be careful with formulas that repeatedly scan large ranges.
9. Use Power Query or other data-preparation approaches when worksheet
   formulas become difficult to maintain at scale.

The computational cost is not the only concern. Formula readability and
auditability are equally important in business spreadsheets.
"""
)


# ============================================================================
# 52. SECURITY AND DATA QUALITY CONSIDERATIONS
# ============================================================================

print_title("52. SECURITY AND DATA QUALITY")

print(
    """
Text functions are often used on data imported from:
    - CSV files
    - websites
    - ERP systems
    - CRM systems
    - emails
    - user-entered forms

Important concerns include:

    - hidden control characters
    - misleading whitespace
    - unexpected delimiters
    - malformed identifiers
    - formula injection when exporting untrusted text
    - accidental conversion of identifiers into numbers
    - loss of leading zeros
    - locale-dependent date interpretation

For example, an employee code such as:

    00125

must not automatically become:

    125

if the leading zeros are meaningful.

Similarly, dates such as:

    03/04/2026

can be ambiguous between day/month/year and month/day/year depending on
regional conventions.

Use explicit date construction and consistent formatting in controlled
workflows.
"""
)


# ============================================================================
# 53. DATA TYPE DESIGN
# ============================================================================

print_title("53. DATA TYPE DESIGN")

data_type_rules = {
    "Person name": "Text",
    "Employee code": "Text",
    "Phone number": "Text",
    "Postal code": "Text",
    "Revenue": "Number",
    "Percentage rate": "Number",
    "Transaction date": "Date",
    "Month-end date": "Date",
    "Formatted report label": "Text",
}

for field, data_type in data_type_rules.items():
    print(f"{field:22} -> {data_type}")


# ============================================================================
# 54. UNIT-STYLE TESTS
# ============================================================================

print_title("54. BASIC TESTS")

def run_tests() -> None:
    """Run correctness tests for the educational implementations."""

    assert excel_left("Excel", 2) == "Ex"
    assert excel_left("Excel", 20) == "Excel"
    assert excel_left("Excel", 0) == ""

    assert excel_right("Excel", 2) == "el"
    assert excel_right("Excel", 20) == "Excel"
    assert excel_right("Excel", 0) == ""

    assert excel_mid("Excel", 2, 3) == "xce"
    assert excel_mid("Excel", 20, 3) == ""

    assert excel_len("Excel") == 5
    assert excel_len("Excel ") == 6

    assert excel_trim("  Atul   Pandey  ") == "Atul Pandey"
    assert excel_clean("A\x00B\x1fC") == "ABC"

    assert excel_substitute("A-B-C", "-", "/") == "A/B/C"
    assert excel_substitute("A-B-C", "-", "/", 2) == "A-B/C"

    assert excel_concat("A", " ", "B") == "A B"
    assert excel_textjoin(", ", True, "A", "", "B") == "A, B"

    assert excel_date(2026, 9, 11) == date(2026, 9, 11)
    assert excel_date(2026, 13, 15) == date(2027, 1, 15)
    assert excel_date(2026, 9, 0) == date(2026, 8, 31)

    assert excel_year(date(2026, 9, 11)) == 2026
    assert excel_month(date(2026, 9, 11)) == 9
    assert excel_day(date(2026, 9, 11)) == 11

    assert excel_eomonth(date(2026, 9, 11), 0) == date(2026, 9, 30)
    assert excel_eomonth(date(2026, 9, 11), 1) == date(2026, 10, 31)
    assert excel_eomonth(date(2026, 9, 11), -1) == date(2026, 8, 31)

    print("All tests passed.")


run_tests()


# ============================================================================
# 55. MINI EXERCISES
# ============================================================================

print_title("55. MINI EXERCISES")

exercise_data = {
    "name": "   Atul    Pandey   ",
    "code": "EMP-IND-2026-00452",
    "email": "atul.pandey@example.com",
    "date": date(2026, 9, 11),
}

print(
    """
Practice tasks using the functions implemented above:

1. Clean the name.
2. Extract the first three characters of the employee code.
3. Extract the country code from the employee code.
4. Extract the employee number.
5. Extract the email username.
6. Extract the email domain.
7. Extract the year from the date.
8. Extract the month from the date.
9. Extract the day from the date.
10. Find the last day of the month.
11. Format the date as dd-mm-yyyy.
12. Create a single employee label containing the name, code, and month.
"""
)

clean_name = clean_business_text(exercise_data["name"])
country_code = excel_mid(exercise_data["code"], 5, 3)
employee_number = excel_right(exercise_data["code"], 5)
email_at = excel_find("@", exercise_data["email"])
email_username = excel_left(exercise_data["email"], email_at - 1)
email_domain = excel_right(
    exercise_data["email"],
    len(exercise_data["email"]) - email_at,
)

print("Clean name       :", clean_name)
print("Country code     :", country_code)
print("Employee number  :", employee_number)
print("Email username   :", email_username)
print("Email domain     :", email_domain)
print("Year             :", excel_year(exercise_data["date"]))
print("Month            :", excel_month(exercise_data["date"]))
print("Day              :", excel_day(exercise_data["date"]))
print("Month end        :", excel_eomonth(exercise_data["date"], 0))
print(
    "Formatted date   :",
    excel_text(exercise_data["date"], "dd-mm-yyyy"),
)

employee_label = excel_textjoin(
    " | ",
    True,
    clean_name,
    exercise_data["code"],
    excel_text(exercise_data["date"], "mmm yyyy"),
)

print("Employee label   :", employee_label)


# ============================================================================
# 56. FINAL REFERENCE TABLE
# ============================================================================

print_title("56. QUICK REFERENCE")

reference = [
    ("LEFT", "Beginning", '=LEFT(text,[num_chars])'),
    ("RIGHT", "End", '=RIGHT(text,[num_chars])'),
    ("MID", "Specified position", '=MID(text,start_num,num_chars)'),
    ("LEN", "Character count", '=LEN(text)'),
    ("TRIM", "Ordinary spaces", '=TRIM(text)'),
    ("CLEAN", "Control characters", '=CLEAN(text)'),
    ("SUBSTITUTE", "Text replacement", '=SUBSTITUTE(text,old,new,[instance])'),
    ("TEXT", "Value formatting", '=TEXT(value,format_text)'),
    ("CONCAT", "Text combination", '=CONCAT(text1,...)'),
    ("TEXTJOIN", "Delimited combination", '=TEXTJOIN(delimiter,ignore_empty,text1,...)'),
    ("DATE", "Date construction", '=DATE(year,month,day)'),
    ("YEAR", "Year extraction", '=YEAR(date)'),
    ("MONTH", "Month extraction", '=MONTH(date)'),
    ("DAY", "Day extraction", '=DAY(date)'),
    ("EOMONTH", "Month-end calculation", '=EOMONTH(start_date,months)'),
]

print(f"{'Function':<14} {'Primary purpose':<28} Formula")
print("-" * 78)

for function_name, purpose, syntax in reference:
    print(f"{function_name:<14} {purpose:<28} {syntax}")


# ============================================================================
# 57. INTEGRATED CASE STUDY
# ============================================================================

print_title("57. INTEGRATED CASE STUDY")

case_study_record = {
    "raw_customer_name": "  Atul\x0d   Pandey  ",
    "customer_code": "CUS-IND-2026-00891",
    "invoice_date": date(2026, 9, 11),
    "invoice_amount": 245780.5,
}

clean_customer_name = clean_business_text(
    case_study_record["raw_customer_name"]
)

country = excel_mid(
    case_study_record["customer_code"],
    5,
    3,
)

customer_id = excel_right(
    case_study_record["customer_code"],
    5,
)

invoice_month = excel_text(
    case_study_record["invoice_date"],
    "mmm yyyy",
)

invoice_month_end = excel_eomonth(
    case_study_record["invoice_date"],
    0,
)

invoice_amount_text = excel_text(
    case_study_record["invoice_amount"],
    "#,##0.00",
)

customer_report = excel_textjoin(
    " | ",
    True,
    "Customer: " + clean_customer_name,
    "Country: " + country,
    "ID: " + customer_id,
    "Period: " + invoice_month,
    "Amount: " + invoice_amount_text,
    "Month end: " + str(invoice_month_end),
)

print(customer_report)

print(
    """
Conceptual Excel implementation:

    Customer name:
        =TRIM(CLEAN(A2))

    Country:
        =MID(B2,5,3)

    Customer ID:
        =RIGHT(B2,5)

    Reporting month:
        =TEXT(C2,"mmm yyyy")

    Month end:
        =EOMONTH(C2,0)

    Report label:
        =TEXTJOIN(" | ",TRUE,
            "Customer: "&TRIM(CLEAN(A2)),
            "Country: "&MID(B2,5,3),
            "ID: "&RIGHT(B2,5),
            "Period: "&TEXT(C2,"mmm yyyy"),
            "Amount: "&TEXT(D2,"#,##0.00")
        )

This illustrates the central practical pattern:

    clean -> extract -> format -> combine

Each function performs a focused operation, while composition creates a
complete data-processing workflow.
"""
)


# ============================================================================
# 58. END OF STUDY FILE
# ============================================================================

print_title("END OF EXCEL TEXT & DATE FUNCTIONS STUDY FILE")

print(
    """
Covered functions:

    LEFT
    RIGHT
    MID
    LEN
    TRIM
    CLEAN
    SUBSTITUTE
    TEXT
    CONCAT
    TEXTJOIN
    DATE
    YEAR
    MONTH
    DAY
    EOMONTH

The script also demonstrated:
    - function composition
    - data cleaning
    - identifier parsing
    - delimiter-based extraction
    - date construction
    - date component extraction
    - month-end calculations
    - date formatting
    - report-label generation
    - edge cases
    - validation
    - leap-year behavior
    - Excel date serial concepts
    - data-type considerations
    - performance considerations
    - data-quality and security considerations
    - testing
    - integrated business examples
"""
)

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <optional>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

/*
 * SQL String Functions Case Study
 *
 * Scenario:
 * A support platform receives customer names, email addresses, phone
 * numbers, and ticket messages from multiple systems. Before records are
 * searched or displayed, the platform needs deterministic string
 * transformations similar to SQL expressions.
 *
 * The program models:
 *   - CONCAT through explicit string composition
 *   - SUBSTRING through one-based SQL-style positions
 *   - POSITION through one-based substring lookup
 *   - REPLACE through replacement of every literal occurrence
 *   - LOWER and UPPER for case normalization
 *   - TRIM for boundary whitespace
 *   - regular expressions for validation and structured extraction
 *
 * Compile:
 *   g++ -std=c++17 -O2 -Wall -Wextra -pedantic string_functions.cpp -o string_functions
 */

struct Customer {
    int id;
    std::string firstName;
    std::string lastName;
    std::string email;
    std::string phone;
};

struct Ticket {
    int id;
    int customerId;
    std::string subject;
    std::string message;
};

enum class TicketCategory {
    AccountSecurity,
    Billing,
    CustomerProfile,
    Email,
    General
};

std::string trim(std::string_view value) {
    const auto notSpace = [](unsigned char ch) {
        return !std::isspace(ch);
    };

    std::size_t first = 0;
    while (first < value.size() &&
           !notSpace(static_cast<unsigned char>(value[first]))) {
        ++first;
    }

    if (first == value.size()) {
        return "";
    }

    std::size_t last = value.size();
    while (last > first &&
           !notSpace(static_cast<unsigned char>(value[last - 1]))) {
        --last;
    }

    return std::string(value.substr(first, last - first));
}

std::string lower(std::string_view value) {
    std::string result(value);

    for (char& ch : result) {
        ch = static_cast<char>(
            std::tolower(static_cast<unsigned char>(ch))
        );
    }

    return result;
}

std::string upper(std::string_view value) {
    std::string result(value);

    for (char& ch : result) {
        ch = static_cast<char>(
            std::toupper(static_cast<unsigned char>(ch))
        );
    }

    return result;
}

std::string concat(std::initializer_list<std::string_view> parts) {
    /*
     * SQL CONCAT semantics vary around NULL. This case study uses explicit
     * strings only, so the function has no hidden NULL conversion behavior.
     */
    std::size_t totalSize = 0;

    for (const auto part : parts) {
        totalSize += part.size();
    }

    std::string result;
    result.reserve(totalSize);

    for (const auto part : parts) {
        result.append(part);
    }

    return result;
}

std::string substringSql(
    std::string_view value,
    std::size_t startPosition,
    std::optional<std::size_t> length = std::nullopt
) {
    /*
     * SQL-style positions are one-based. C++ string offsets are zero-based,
     * so startPosition is converted exactly once at the boundary.
     */
    if (startPosition == 0) {
        throw std::invalid_argument(
            "SQL substring positions must be one-based"
        );
    }

    const std::size_t startIndex = startPosition - 1;

    if (startIndex >= value.size()) {
        return "";
    }

    if (!length.has_value()) {
        return std::string(value.substr(startIndex));
    }

    return std::string(value.substr(startIndex, length.value()));
}

std::size_t positionSql(
    std::string_view needle,
    std::string_view haystack
) {
    /*
     * SQL-style POSITION returns one-based coordinates. Zero represents
     * "not found" in this model.
     */
    const std::size_t index = haystack.find(needle);

    if (index == std::string_view::npos) {
        return 0;
    }

    return index + 1;
}

std::string replaceAll(
    std::string value,
    std::string_view search,
    std::string_view replacement
) {
    /*
     * std::string::replace works at one occurrence at a time. A loop makes
     * the SQL REPLACE behavior explicit and avoids treating the search string
     * as a regular expression.
     */
    if (search.empty()) {
        return value;
    }

    std::size_t position = 0;

    while ((position = value.find(search, position)) != std::string::npos) {
        value.replace(position, search.size(), replacement);
        position += replacement.size();
    }

    return value;
}

bool regexMatches(
    std::string_view value,
    const std::regex& expression
) {
    return std::regex_search(value.begin(), value.end(), expression);
}

std::optional<std::string> regexExtract(
    std::string_view value,
    const std::regex& expression
) {
    std::match_results<std::string_view::const_iterator> match;

    if (!std::regex_search(
            value.begin(),
            value.end(),
            match,
            expression
        )) {
        return std::nullopt;
    }

    return std::string(match[0].first, match[0].second);
}

std::string normalizeEmail(const std::string& email) {
    return lower(trim(email));
}

std::string normalizePhone(const std::string& phone) {
    /*
     * A regex removes separators without requiring separate rules for '-',
     * spaces, parentheses, or dots.
     */
    static const std::regex nonDigits("[^0-9]+");
    return std::regex_replace(phone, nonDigits, "");
}

std::string customerName(const Customer& customer) {
    return concat({
        trim(customer.firstName),
        " ",
        trim(customer.lastName)
    });
}

std::string contactLabel(const Customer& customer) {
    const std::string name = customerName(customer);
    const std::string email = normalizeEmail(customer.email);

    return concat({name, " <", email, ">"});
}

std::string emailDomain(const Customer& customer) {
    const std::string email = normalizeEmail(customer.email);
    const std::size_t atPosition = positionSql("@", email);

    if (atPosition == 0) {
        return "";
    }

    return substringSql(email, atPosition + 1);
}

TicketCategory classifyTicket(const Ticket& ticket) {
    /*
     * LOWER is applied before regex classification so that a ticket written
     * as "PAYMENT failed" is treated consistently with "payment failed".
     */
    const std::string searchable = lower(
        concat({ticket.subject, " ", ticket.message})
    );

    static const std::regex security(
        "password|credential",
        std::regex_constants::icase
    );
    static const std::regex billing(
        "payment|order",
        std::regex_constants::icase
    );
    static const std::regex profile(
        "address|delivery",
        std::regex_constants::icase
    );
    static const std::regex email(
        "verification|email",
        std::regex_constants::icase
    );

    if (regexMatches(searchable, security)) {
        return TicketCategory::AccountSecurity;
    }

    if (regexMatches(searchable, billing)) {
        return TicketCategory::Billing;
    }

    if (regexMatches(searchable, profile)) {
        return TicketCategory::CustomerProfile;
    }

    if (regexMatches(searchable, email)) {
        return TicketCategory::Email;
    }

    return TicketCategory::General;
}

std::string categoryName(TicketCategory category) {
    switch (category) {
        case TicketCategory::AccountSecurity:
            return "account-security";
        case TicketCategory::Billing:
            return "billing";
        case TicketCategory::CustomerProfile:
            return "customer-profile";
        case TicketCategory::Email:
            return "email";
        case TicketCategory::General:
            return "general";
    }

    throw std::logic_error("Unknown ticket category");
}

void printCustomerReport(const std::vector<Customer>& customers) {
    std::cout << "\n=== CUSTOMER NORMALIZATION REPORT ===\n";

    for (const Customer& customer : customers) {
        const std::string name = customerName(customer);
        const std::string normalizedEmail =
            normalizeEmail(customer.email);

        std::cout
            << "Customer " << customer.id
            << "\n  Name: " << name
            << "\n  Contact: " << contactLabel(customer)
            << "\n  Email domain: " << emailDomain(customer)
            << "\n  Phone digits: " << normalizePhone(customer.phone)
            << "\n";
    }
}

void printTicketReport(const std::vector<Ticket>& tickets) {
    std::cout << "\n=== SUPPORT-TICKET TEXT ANALYSIS ===\n";

    /*
     * ORD-2026-1234 is treated as a structured identifier. The bounded
     * quantifiers prevent arbitrary text from being interpreted as an order
     * number.
     */
    const std::regex orderPattern(
        R"(\bORD-[0-9]{4}-[0-9]{4}\b)"
    );

    for (const Ticket& ticket : tickets) {
        const std::string preview =
            substringSql(ticket.message, 1, 32);

        const std::size_t customerPosition =
            positionSql("customer", lower(ticket.message));

        const auto orderCode =
            regexExtract(ticket.message, orderPattern);

        std::cout
            << "\nTicket " << ticket.id
            << "\n  Subject: " << ticket.subject
            << "\n  Preview: " << preview
            << "\n  'customer' position: " << customerPosition
            << "\n  Category: " << categoryName(classifyTicket(ticket))
            << "\n  Order code: "
            << (orderCode.has_value() ? orderCode.value() : "(none)")
            << "\n";
    }
}

void demonstrateFunctionComposition() {
    std::cout << "\n=== FUNCTION COMPOSITION ===\n";

    const std::string raw =
        "   PAYMENT FAILED for ORD-2026-1042   ";

    const std::string cleaned = trim(raw);
    const std::string normalized = lower(cleaned);
    const std::string redacted =
        replaceAll(normalized, "ord-2026-1042", "[order-id]");

    std::cout
        << "Raw:        [" << raw << "]\n"
        << "TRIM:       [" << cleaned << "]\n"
        << "LOWER:      [" << normalized << "]\n"
        << "REPLACE:    [" << redacted << "]\n";
}

void demonstrateRegexValidation() {
    std::cout << "\n=== REGULAR-EXPRESSION VALIDATION ===\n";

    /*
     * This pattern validates the common structural shape of an email.
     * It is intentionally not presented as a complete implementation of
     * RFC-level email validation.
     */
    const std::regex emailPattern(
        R"(^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$)"
    );

    const std::vector<std::string> emails = {
        "analyst@example.com",
        "invalid-address",
        "person+alerts@example.co.in"
    };

    for (const std::string& email : emails) {
        std::cout
            << std::left
            << std::setw(35)
            << email
            << " -> "
            << (regexMatches(email, emailPattern) ? "valid shape"
                                                  : "invalid shape")
            << "\n";
    }
}

void demonstrateEdgeCases() {
    std::cout << "\n=== EDGE CASES ===\n";

    std::cout
        << "POSITION missing text: "
        << positionSql("xyz", "database")
        << "\n";

    std::cout
        << "SUBSTRING beyond end: ["
        << substringSql("database", 100, 5)
        << "]\n";

    std::cout
        << "REPLACE repeated literal: "
        << replaceAll("ORD ORD ORD", "ORD", "ORDER")
        << "\n";

    std::cout
        << "TRIM all whitespace: ["
        << trim("     ")
        << "]\n";
}

void demonstrateSecurityAndProductionRules() {
    std::cout << "\n=== SECURITY AND PRODUCTION CONSIDERATIONS ===\n";

    std::cout
        << "Literal REPLACE is kept separate from regex replacement so that "
           "data containing regex metacharacters is not accidentally treated "
           "as a pattern.\n";

    std::cout
        << "Regex patterns should be controlled when possible. "
           "Untrusted patterns can consume excessive CPU in some regex "
           "engines.\n";

    std::cout
        << "Normalization before comparison must match the database collation "
           "and Unicode requirements used by the production system.\n";

    std::cout
        << "Frequently queried normalized values may justify a stored "
           "canonical column or an expression index supported by the target "
           "database.\n";
}

int main() {
    const std::vector<Customer> customers = {
        {
            1,
            "  Atul  ",
            "Pandey",
            "ATUL.PANDEY@EXAMPLE.COM",
            "+91-98765-43210"
        },
        {
            2,
            "Priya",
            "Sharma",
            " priya.sharma@example.com ",
            "+91-91234-56789"
        },
        {
            3,
            "Rohan",
            "Mehta",
            "ROHAN.MEHTA@EXAMPLE.COM",
            "+91-99887-77665"
        },
        {
            4,
            "Neha",
            "Verma",
            "neha.verma@example.com",
            "+91-90000-11122"
        }
    };

    const std::vector<Ticket> tickets = {
        {
            1001,
            1,
            "Password Reset",
            "Customer requested a password reset for the account."
        },
        {
            1002,
            2,
            "Payment Failed",
            "Payment failed while processing order ORD-2026-1042."
        },
        {
            1003,
            3,
            "Address Change",
            "Customer wants to change the registered delivery address."
        },
        {
            1004,
            4,
            "Email Verification",
            "Verification link was sent but customer reports an error."
        }
    };

    try {
        std::cout
            << "SQL STRING FUNCTIONS: CUSTOMER SUPPORT CASE STUDY\n";

        printCustomerReport(customers);
        printTicketReport(tickets);
        demonstrateFunctionComposition();
        demonstrateRegexValidation();
        demonstrateEdgeCases();
        demonstrateSecurityAndProductionRules();
    } catch (const std::exception& error) {
        std::cerr
            << "Processing error: "
            << error.what()
            << "\n";
        return 1;
    }

    return 0;
}

#include <algorithm>
#include <cctype>
#include <exception>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct PullDataRecord {
    int customerId;
    std::string name;
    std::string age;
    std::string email;
    std::string city;
    std::string segment;
    std::string signupDate;
    std::string orders;
};

struct CleanCustomer {
    int customerId;
    std::string name;
    std::optional<int> age;
    std::optional<std::string> email;
    std::string city;
    std::string segment;
    std::optional<std::string> signupDate;
    std::optional<int> orders;
};

struct GovernanceMetrics {
    int invalidValues = 0;
    int duplicateRows = 0;
};

class CustomerDataQualityEngine {
private:
    GovernanceMetrics metrics;

    static std::string trim(const std::string& value) {
        const auto first = value.find_first_not_of(" \t\r\n");
        if (first == std::string::npos) return "";

        const auto last = value.find_last_not_of(" \t\r\n");
        return value.substr(first, last - first + 1);
    }

    static std::string collapseSpaces(const std::string& value) {
        std::string result;
        bool previousSpace = false;

        for (unsigned char character : value) {
            if (std::isspace(character)) {
                if (!previousSpace) {
                    result += ' ';
                    previousSpace = true;
                }
            } else {
                result += static_cast<char>(character);
                previousSpace = false;
            }
        }

        return trim(result);
    }

    static std::string lower(std::string value) {
        std::transform(
            value.begin(),
            value.end(),
            value.begin(),
            [](unsigned char character) {
                return static_cast<char>(std::tolower(character));
            }
        );
        return value;
    }

    static std::string titleCase(const std::string& value) {
        std::string result = lower(value);
        bool capitalize = true;

        for (char& character : result) {
            if (std::isspace(static_cast<unsigned char>(character))) {
                capitalize = true;
            } else if (capitalize) {
                character = static_cast<char>(
                    std::toupper(static_cast<unsigned char>(character))
                );
                capitalize = false;
            }
        }

        return result;
    }

    std::optional<int> parseInteger(
        const std::string& value,
        int minimum,
        int maximum
    ) {
        const std::string normalized = trim(value);

        if (normalized.empty() || lower(normalized) == "unknown") {
            return std::nullopt;
        }

        try {
            std::size_t consumed = 0;
            const int parsed = std::stoi(normalized, &consumed);

            if (consumed != normalized.size() ||
                parsed < minimum ||
                parsed > maximum) {
                metrics.invalidValues++;
                return std::nullopt;
            }

            return parsed;
        } catch (const std::exception&) {
            metrics.invalidValues++;
            return std::nullopt;
        }
    }

    std::optional<std::string> normalizeEmail(const std::string& value) {
        const std::string normalized = lower(collapseSpaces(value));

        if (normalized.empty() || normalized == "unknown") {
            return std::nullopt;
        }

        static const std::regex emailPattern(
            R"(^[^\s@]+@[^\s@]+\.[^\s@]+$)"
        );

        if (!std::regex_match(normalized, emailPattern)) {
            metrics.invalidValues++;
            return std::nullopt;
        }

        return normalized;
    }

    std::optional<std::string> normalizeDate(const std::string& value) {
        std::string normalized = trim(value);

        if (normalized.empty()) {
            return std::nullopt;
        }

        std::replace(normalized.begin(), normalized.end(), '/', '-');

        static const std::regex datePattern(R"(^\d{4}-\d{2}-\d{2}$)");

        if (!std::regex_match(normalized, datePattern)) {
            metrics.invalidValues++;
            return std::nullopt;
        }

        return normalized;
    }

    CleanCustomer normalize(const PullDataRecord& record) {
        std::string normalizedSegment = titleCase(
            collapseSpaces(record.segment)
        );

        const std::set<std::string> allowedSegments{
            "Standard", "Premium", "Enterprise"
        };

        if (!allowedSegments.contains(normalizedSegment)) {
            throw std::runtime_error(
                "Unsupported customer segment: " + record.segment
            );
        }

        const std::string normalizedName =
            titleCase(collapseSpaces(record.name));

        return {
            record.customerId,
            normalizedName.empty() ? "Unknown Customer" : normalizedName,
            parseInteger(record.age, 18, 100),
            normalizeEmail(record.email),
            titleCase(collapseSpaces(record.city)).empty()
                ? "Unknown"
                : titleCase(collapseSpaces(record.city)),
            normalizedSegment,
            normalizeDate(record.signupDate),
            parseInteger(record.orders, 0, 1000000)
        };
    }

public:
    std::vector<CleanCustomer> clean(
        const std::vector<PullDataRecord>& records
    ) {
        std::vector<CleanCustomer> result;
        std::set<int> customerIds;
        std::set<std::string> emails;

        for (const auto& record : records) {
            CleanCustomer customer = normalize(record);

            // customer_id is the authoritative identity key.
            if (!customerIds.insert(customer.customerId).second) {
                metrics.duplicateRows++;
                continue;
            }

            // Email uniqueness is applied only when an email exists.
            if (customer.email.has_value() &&
                !emails.insert(*customer.email).second) {
                metrics.duplicateRows++;
                continue;
            }

            result.push_back(std::move(customer));
        }

        /*
         * Median imputation is calculated after duplicate removal so that
         * repeated source rows cannot distort the replacement value.
         */
        std::vector<int> ages;
        std::vector<int> orders;

        for (const auto& customer : result) {
            if (customer.age) ages.push_back(*customer.age);
            if (customer.orders) orders.push_back(*customer.orders);
        }

        auto median = [](std::vector<int> values) -> std::optional<int> {
            if (values.empty()) return std::nullopt;

            std::sort(values.begin(), values.end());
            const std::size_t middle = values.size() / 2;

            if (values.size() % 2 == 1) {
                return values[middle];
            }

            return static_cast<int>(
                std::round((values[middle - 1] + values[middle]) / 2.0)
            );
        };

        const auto ageMedian = median(ages);
        const auto orderMedian = median(orders);

        for (auto& customer : result) {
            if (!customer.age && ageMedian) {
                customer.age = ageMedian;
            }

            if (!customer.orders && orderMedian) {
                customer.orders = orderMedian;
            }
        }

        return result;
    }

    GovernanceMetrics getMetrics() const {
        return metrics;
    }
};

int main() {
    const std::vector<PullDataRecord> source{
        {101, " Alice  Sharma ", "29", " ALICE.SHARMA@EXAMPLE.COM ",
         "Lucknow", "Premium", "2026-01-15", "12"},
        {102, "Bob Khan", "", "bob.khan@example.com",
         "Delhi", "Standard", "2026/02/20", "5"},
        {103, "Charlie  Rao", "34", "",
         "Mumbai", "Premium", "2026-03-10", "8"},
        {104, "Alice  Sharma", "29", "alice.sharma@example.com",
         "Lucknow", "Premium", "2026-01-15", "12"},
        {105, "David Mehta", "unknown", "david.mehta@example.com",
         "Delhi", "standard", "2026-04-05", "3"},
        {106, "Esha Patel", "41", "esha.patel@example.com",
         " ", "Enterprise", "2026-05-11", "21"},
        {107, "Farhan Ali", "37", "farhan.ali@example.com",
         "Bengaluru", "Standard", "invalid", "7"},
        {108, "", "26", "neha@example.com",
         "Pune", "Standard", "2026-06-30", "2"},
        {109, "George Sen", "-5", "george.sen@example.com",
         "Chennai", "Premium", "2026-07-01", "15"},
        {110, "Hina Roy", "30", "hina.roy@example.com",
         "Kolkata", "premium", "2026-07-18", "10"}
    };

    try {
        CustomerDataQualityEngine engine;
        const auto cleaned = engine.clean(source);

        std::cout << std::left
                  << std::setw(8) << "ID"
                  << std::setw(22) << "Name"
                  << std::setw(7) << "Age"
                  << std::setw(32) << "Email"
                  << std::setw(15) << "City"
                  << std::setw(14) << "Segment"
                  << std::setw(14) << "Signup"
                  << "Orders\n";

        std::cout << std::string(130, '-') << '\n';

        for (const auto& customer : cleaned) {
            std::cout << std::setw(8) << customer.customerId
                      << std::setw(22) << customer.name
                      << std::setw(7)
                      << (customer.age
                              ? std::to_string(*customer.age)
                              : "NULL")
                      << std::setw(32)
                      << (customer.email
                              ? *customer.email
                              : "NULL")
                      << std::setw(15) << customer.city
                      << std::setw(14) << customer.segment
                      << std::setw(14)
                      << (customer.signupDate
                              ? *customer.signupDate
                              : "NULL")
                      << (customer.orders
                              ? std::to_string(*customer.orders)
                              : "NULL")
                      << '\n';
        }

        const GovernanceMetrics metrics = engine.getMetrics();

        std::cout << "\nInvalid values: "
                  << metrics.invalidValues << '\n';
        std::cout << "Duplicate rows removed: "
                  << metrics.duplicateRows << '\n';
        std::cout << "Clean rows: "
                  << cleaned.size() << '\n';

        /*
         * Complexity:
         * normalization is O(n) apart from set operations,
         * duplicate detection is O(n log n),
         * median calculation is O(n log n).
         *
         * The engine deliberately preserves missing email values rather than
         * inventing identities that could corrupt customer records.
         */
    } catch (const std::exception& error) {
        std::cerr << "Data cleaning failed: "
                  << error.what() << '\n';
        return 1;
    }

    return 0;
}

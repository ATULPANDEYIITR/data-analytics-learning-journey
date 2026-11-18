#include <algorithm>
#include <cmath>
#include <functional>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;

enum class DataType {
    TEXT,
    INTEGER,
    DECIMAL,
    DATE,
    BOOLEAN
};

enum class JoinType {
    INNER,
    LEFT,
    FULL
};

using Value = optional<string>;
using Row = unordered_map<string, Value>;

struct Table {
    string name;
    vector<string> columns;
    vector<Row> rows;

    void validate() const {
        if (columns.empty()) {
            throw invalid_argument("Table has no columns.");
        }

        set<string> unique(columns.begin(), columns.end());

        if (unique.size() != columns.size()) {
            throw invalid_argument("Duplicate columns.");
        }

        for (const auto& row : rows) {
            for (const auto& column : columns) {
                if (!row.count(column)) {
                    throw invalid_argument(
                        "Row does not match table schema."
                    );
                }
            }
        }
    }

    void display() const {
        cout << "\n" << name
             << " (" << rows.size() << " rows)\n";

        for (const auto& column : columns) {
            cout << setw(18) << column;
        }

        cout << '\n';

        for (const auto& row : rows) {
            for (const auto& column : columns) {
                const auto& value = row.at(column);

                cout << setw(18)
                     << (value ? *value : "NULL");
            }

            cout << '\n';
        }
    }
};

class PowerQueryEngine {
private:
    unordered_map<string, function<Table()>> queries;
    unordered_map<string, vector<string>> dependencies;
    unordered_map<string, Table> results;

    static string normalize(const string& value) {
        size_t start = value.find_first_not_of(" \t\r\n");

        if (start == string::npos) {
            return "";
        }

        size_t end = value.find_last_not_of(" \t\r\n");

        return value.substr(start, end - start + 1);
    }

    static double parseDecimal(const string& value) {
        size_t position = 0;
        double result;

        try {
            result = stod(value, &position);
        } catch (...) {
            throw invalid_argument("Invalid decimal: " + value);
        }

        if (position != value.size() || !isfinite(result)) {
            throw invalid_argument("Invalid decimal: " + value);
        }

        return result;
    }

public:
    static string convert(
        const Value& value,
        DataType type
    ) {
        if (!value.has_value()) return "NULL";

        const string& input = *value;

        switch (type) {
            case DataType::TEXT:
                return normalize(input);

            case DataType::INTEGER: {
                size_t position = 0;
                long long number;

                try {
                    number = stoll(input, &position);
                } catch (...) {
                    throw invalid_argument("Invalid integer.");
                }

                if (position != input.size()) {
                    throw invalid_argument("Invalid integer.");
                }

                return to_string(number);
            }

            case DataType::DECIMAL: {
                ostringstream output;
                output << fixed << setprecision(2)
                       << parseDecimal(input);
                return output.str();
            }

            case DataType::DATE: {
                if (input.size() != 10 ||
                    input[4] != '-' ||
                    input[7] != '-') {
                    throw invalid_argument("Invalid ISO date.");
                }

                return input;
            }

            case DataType::BOOLEAN:
                if (input == "true" || input == "1" ||
                    input == "yes") return "true";

                if (input == "false" || input == "0" ||
                    input == "no") return "false";

                throw invalid_argument("Invalid boolean.");
        }

        throw invalid_argument("Unknown data type.");
    }

    static Table clean(Table table) {
        for (auto& row : table.rows) {
            for (auto& column : table.columns) {
                if (row[column].has_value()) {
                    row[column] = normalize(*row[column]);

                    if (row[column]->empty()) {
                        row[column] = nullopt;
                    }
                }
            }
        }

        set<string> seen;
        vector<Row> uniqueRows;

        for (const auto& row : table.rows) {
            string key;

            for (const auto& column : table.columns) {
                key += row.at(column).value_or("<NULL>") + "\x1F";
            }

            if (seen.insert(key).second) {
                uniqueRows.push_back(row);
            }
        }

        table.rows = move(uniqueRows);
        return table;
    }

    static Table changeTypes(
        Table table,
        const map<string, DataType>& schema
    ) {
        for (const auto& [column, type] : schema) {
            if (find(
                table.columns.begin(),
                table.columns.end(),
                column
            ) == table.columns.end()) {
                throw invalid_argument("Unknown type column.");
            }

            for (auto& row : table.rows) {
                auto value = row.at(column);

                if (value.has_value()) {
                    row[column] = convert(value, type);
                }
            }
        }

        return table;
    }

    static Table filter(
        const Table& table,
        function<bool(const Row&)> predicate
    ) {
        Table result = table;
        result.rows.clear();

        copy_if(
            table.rows.begin(),
            table.rows.end(),
            back_inserter(result.rows),
            predicate
        );

        return result;
    }

    static Table merge(
        const Table& left,
        const Table& right,
        const string& leftKey,
        const string& rightKey,
        JoinType joinType
    ) {
        if (find(left.columns.begin(), left.columns.end(),
                 leftKey) == left.columns.end() ||
            find(right.columns.begin(), right.columns.end(),
                 rightKey) == right.columns.end()) {
            throw invalid_argument("Invalid join key.");
        }

        vector<string> rightColumns;

        for (const auto& column : right.columns) {
            if (column != rightKey) {
                rightColumns.push_back(column);
            }
        }

        unordered_map<string, string> renamed;

        for (const auto& column : rightColumns) {
            string output = column;

            if (find(left.columns.begin(), left.columns.end(),
                     output) != left.columns.end()) {
                output += "_right";
            }

            if (renamed.count(output)) {
                throw invalid_argument("Column collision.");
            }

            renamed[column] = output;
        }

        unordered_map<string, vector<size_t>> index;

        for (size_t i = 0; i < right.rows.size(); ++i) {
            const auto& key = right.rows[i].at(rightKey);

            if (key.has_value()) {
                index[*key].push_back(i);
            }
        }

        Table result;
        result.name = left.name + "_merged";
        result.columns = left.columns;

        for (const auto& column : rightColumns) {
            result.columns.push_back(renamed[column]);
        }

        set<size_t> matchedRight;

        for (const auto& leftRow : left.rows) {
            const auto& key = leftRow.at(leftKey);

            vector<size_t> matches;

            if (key.has_value() && index.count(*key)) {
                matches = index.at(*key);
            }

            if (matches.empty()) {
                if (joinType == JoinType::LEFT ||
                    joinType == JoinType::FULL) {
                    Row output = leftRow;

                    for (const auto& column : rightColumns) {
                        output[renamed[column]] = nullopt;
                    }

                    result.rows.push_back(move(output));
                }

                continue;
            }

            for (size_t position : matches) {
                matchedRight.insert(position);

                Row output = leftRow;

                for (const auto& column : rightColumns) {
                    output[renamed[column]] =
                        right.rows[position].at(column);
                }

                result.rows.push_back(move(output));
            }
        }

        if (joinType == JoinType::FULL) {
            for (size_t i = 0; i < right.rows.size(); ++i) {
                if (matchedRight.count(i)) continue;

                Row output;

                for (const auto& column : left.columns) {
                    output[column] = nullopt;
                }

                for (const auto& column : rightColumns) {
                    output[renamed[column]] =
                        right.rows[i].at(column);
                }

                result.rows.push_back(move(output));
            }
        }

        return result;
    }

    static Table append(const vector<Table>& tables) {
        if (tables.empty()) {
            throw invalid_argument("No tables to append.");
        }

        Table result;
        result.name = "appended";

        for (const auto& table : tables) {
            table.validate();

            for (const auto& column : table.columns) {
                if (find(result.columns.begin(),
                         result.columns.end(),
                         column) == result.columns.end()) {
                    result.columns.push_back(column);
                }
            }
        }

        for (const auto& table : tables) {
            for (const auto& row : table.rows) {
                Row output;

                for (const auto& column : result.columns) {
                    auto it = row.find(column);

                    output[column] = (
                        it == row.end()
                        ? nullopt
                        : it->second
                    );
                }

                result.rows.push_back(move(output));
            }
        }

        return result;
    }

    void registerQuery(
        const string& name,
        vector<string> required,
        function<Table()> transform
    ) {
        if (queries.count(name)) {
            throw invalid_argument("Duplicate query.");
        }

        queries[name] = move(transform);
        dependencies[name] = move(required);
    }

    void execute() {
        unordered_set<string> completed;
        unordered_set<string> active;

        function<void(const string&)> visit =
            [&](const string& name) {
                if (!queries.count(name)) {
                    throw runtime_error("Missing query: " + name);
                }

                if (active.count(name)) {
                    throw runtime_error("Dependency cycle detected.");
                }

                if (completed.count(name)) return;

                active.insert(name);

                for (const auto& dependency : dependencies[name]) {
                    visit(dependency);
                }

                Table result = queries[name]();
                result.validate();

                results[name] = move(result);

                active.erase(name);
                completed.insert(name);

                cout << "Executed query: " << name << '\n';
            };

        for (const auto& [name, transform] : queries) {
            visit(name);
        }
    }

    const Table& getResult(const string& name) const {
        auto it = results.find(name);

        if (it == results.end()) {
            throw runtime_error("Query result unavailable.");
        }

        return it->second;
    }
};

int main() {
    try {
        Table customers{
            "customers",
            {"customer_id", "name", "region"},
            {
                {
                    {"customer_id", "1"},
                    {"name", " Alice "},
                    {"region", "North"}
                },
                {
                    {"customer_id", "2"},
                    {"name", "Bob"},
                    {"region", "South"}
                },
                {
                    {"customer_id", "3"},
                    {"name", "Carol"},
                    {"region", "North"}
                }
            }
        };

        Table orders{
            "orders",
            {"order_id", "customer_id", "amount"},
            {
                {
                    {"order_id", "101"},
                    {"customer_id", "1"},
                    {"amount", "1250.50"}
                },
                {
                    {"order_id", "102"},
                    {"customer_id", "2"},
                    {"amount", "800.00"}
                },
                {
                    {"order_id", "103"},
                    {"customer_id", "1"},
                    {"amount", "450.25"}
                },
                {
                    {"order_id", "104"},
                    {"customer_id", "99"},
                    {"amount", "300.00"}
                }
            }
        };

        Table archived{
            "archived",
            {"order_id", "customer_id", "amount"},
            {
                {
                    {"order_id", "90"},
                    {"customer_id", "2"},
                    {"amount", "500.00"}
                }
            }
        };

        customers = PowerQueryEngine::clean(customers);
        orders = PowerQueryEngine::clean(orders);
        archived = PowerQueryEngine::clean(archived);

        map<string, DataType> customerTypes{
            {"customer_id", DataType::INTEGER},
            {"name", DataType::TEXT},
            {"region", DataType::TEXT}
        };

        map<string, DataType> orderTypes{
            {"order_id", DataType::INTEGER},
            {"customer_id", DataType::INTEGER},
            {"amount", DataType::DECIMAL}
        };

        customers = PowerQueryEngine::changeTypes(
            customers, customerTypes
        );

        orders = PowerQueryEngine::changeTypes(
            orders, orderTypes
        );

        archived = PowerQueryEngine::changeTypes(
            archived, orderTypes
        );

        cout << "\n1. LEFT MERGE\n";

        Table merged = PowerQueryEngine::merge(
            orders,
            customers,
            "customer_id",
            "customer_id",
            JoinType::LEFT
        );

        merged.display();

        cout << "\n2. APPEND\n";

        Table combined = PowerQueryEngine::append({
            orders, archived
        });

        combined.display();

        cout << "\n3. FILTER\n";

        Table filtered = PowerQueryEngine::filter(
            combined,
            [](const Row& row) {
                return stod(*row.at("amount")) >= 500.0;
            }
        );

        filtered.display();

        cout << "\n4. QUERY DEPENDENCIES\n";

        PowerQueryEngine engine;

        engine.registerQuery(
            "source",
            {},
            [orders]() { return orders; }
        );

        engine.registerQuery(
            "filtered",
            {"source"},
            [orders]() {
                return PowerQueryEngine::filter(
                    orders,
                    [](const Row& row) {
                        return stod(*row.at("amount")) >= 500.0;
                    }
                );
            }
        );

        engine.execute();

        engine.getResult("source").display();
        engine.getResult("filtered").display();

        cout << "\n5. VALIDATION\n";

        if (merged.rows.size() != 4) {
            throw runtime_error("Merge validation failed.");
        }

        if (combined.rows.size() != 5) {
            throw runtime_error("Append validation failed.");
        }

        cout << "All checks passed.\n";

    } catch (const exception& error) {
        cerr << "Processing error: "
             << error.what() << '\n';

        return 1;
    }

    return 0;
}

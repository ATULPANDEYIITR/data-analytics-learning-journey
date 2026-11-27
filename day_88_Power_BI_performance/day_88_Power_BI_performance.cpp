#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

/*
 * Power BI Performance Governance Engine
 *
 * C++17 implementation covering:
 * - Semantic model design
 * - Table and column cardinality
 * - Storage modes
 * - Relationship evaluation
 * - DAX execution characteristics
 * - Query performance metrics
 * - Model optimization
 * - Performance thresholds
 * - Workload prioritization
 *
 * No external dependencies.
 */

namespace powerbi {

// ============================================================
// 1. ENUMERATIONS
// ============================================================

enum class StorageMode {
    Import,
    DirectQuery,
    Dual,
    DirectLake
};

enum class TableRole {
    Fact,
    Dimension,
    Bridge
};

enum class Severity {
    Critical,
    High,
    Medium,
    Low
};

enum class DaxExecution {
    StorageEngine,
    FormulaEngine,
    Mixed
};

enum class QueryStatus {
    Pending,
    Running,
    Completed,
    Failed
};

std::string toString(StorageMode mode) {
    switch (mode) {
        case StorageMode::Import: return "Import";
        case StorageMode::DirectQuery: return "DirectQuery";
        case StorageMode::Dual: return "Dual";
        case StorageMode::DirectLake: return "DirectLake";
    }
    throw std::invalid_argument("Unknown storage mode");
}

std::string toString(Severity severity) {
    switch (severity) {
        case Severity::Critical: return "Critical";
        case Severity::High: return "High";
        case Severity::Medium: return "Medium";
        case Severity::Low: return "Low";
    }
    throw std::invalid_argument("Unknown severity");
}


// ============================================================
// 2. VALIDATION
// ============================================================

void validateNonNegative(
    double value,
    const std::string& field
) {
    if (!std::isfinite(value) || value < 0) {
        throw std::invalid_argument(
            field + " must be finite and non-negative"
        );
    }
}

void validateName(const std::string& name) {
    if (name.empty()) {
        throw std::invalid_argument(
            "Name cannot be empty"
        );
    }
}

double safeRatio(double numerator, double denominator) {
    if (denominator == 0) return 0.0;
    return numerator / denominator;
}


// ============================================================
// 3. COLUMN DOMAIN MODEL
// ============================================================

struct Column {
    std::string name;
    std::string dataType;
    std::uint64_t cardinality;
    bool used;
    bool key;

    void validate(std::uint64_t rowCount) const {
        validateName(name);

        if (cardinality > rowCount) {
            throw std::invalid_argument(
                "Column cardinality exceeds table rows: " + name
            );
        }

        if (
            dataType != "integer" &&
            dataType != "decimal" &&
            dataType != "string" &&
            dataType != "date" &&
            dataType != "boolean"
        ) {
            throw std::invalid_argument(
                "Unsupported column type: " + dataType
            );
        }
    }
};


// ============================================================
// 4. TABLE DOMAIN MODEL
// ============================================================

class Table {

private:
    std::string name_;
    TableRole role_;
    std::uint64_t rows_;
    StorageMode storageMode_;
    std::vector<Column> columns_;
    bool queryFolding_;

public:

    Table(
        std::string name,
        TableRole role,
        std::uint64_t rows,
        StorageMode storageMode,
        std::vector<Column> columns,
        bool queryFolding
    )
        : name_(std::move(name)),
          role_(role),
          rows_(rows),
          storageMode_(storageMode),
          columns_(std::move(columns)),
          queryFolding_(queryFolding) {

        validateName(name_);

        std::map<std::string, bool> seen;

        for (const auto& column : columns_) {
            column.validate(rows_);

            if (seen.count(column.name)) {
                throw std::invalid_argument(
                    "Duplicate column: " + column.name
                );
            }

            seen[column.name] = true;
        }
    }

    const std::string& name() const {
        return name_;
    }

    TableRole role() const {
        return role_;
    }

    std::uint64_t rows() const {
        return rows_;
    }

    StorageMode storageMode() const {
        return storageMode_;
    }

    bool queryFolding() const {
        return queryFolding_;
    }

    const std::vector<Column>& columns() const {
        return columns_;
    }

    double estimateMemoryMB() const {
        if (
            storageMode_ == StorageMode::DirectQuery ||
            storageMode_ == StorageMode::DirectLake
        ) {
            return 0.0;
        }

        std::uint64_t bytes = 0;

        for (const auto& column : columns_) {
            const int bits = std::max(
                1,
                static_cast<int>(
                    std::ceil(
                        std::log2(
                            std::max<std::uint64_t>(
                                2, column.cardinality
                            )
                        )
                    )
                )
            );

            const std::uint64_t encoded =
                (rows_ * bits + 7) / 8;

            const std::uint64_t dictionary =
                column.cardinality *
                (column.dataType == "string" ? 24 : 8);

            bytes += encoded + dictionary;
        }

        return static_cast<double>(bytes) /
            (1024.0 * 1024.0);
    }

    std::vector<std::string> unusedColumns() const {
        std::vector<std::string> result;

        for (const auto& column : columns_) {
            if (!column.used && !column.key) {
                result.push_back(column.name);
            }
        }

        return result;
    }
};


// ============================================================
// 5. RELATIONSHIP MODEL
// ============================================================

struct Relationship {
    std::string fromTable;
    std::string fromColumn;
    std::string toTable;
    std::string toColumn;
    bool bidirectional;
    bool manyToMany;
};


// ============================================================
// 6. SEMANTIC MODEL REGISTRY
// ============================================================

class SemanticModel {

private:
    std::string name_;
    std::map<std::string, Table> tables_;
    std::vector<Relationship> relationships_;

public:

    explicit SemanticModel(std::string name)
        : name_(std::move(name)) {
        validateName(name_);
    }

    void addTable(const Table& table) {
        if (tables_.count(table.name())) {
            throw std::invalid_argument(
                "Duplicate table: " + table.name()
            );
        }

        tables_.emplace(table.name(), table);
    }

    bool containsColumn(
        const Table& table,
        const std::string& columnName
    ) const {
        return std::any_of(
            table.columns().begin(),
            table.columns().end(),
            [&](const Column& column) {
                return column.name == columnName;
            }
        );
    }

    void addRelationship(const Relationship& relationship) {
        auto source = tables_.find(relationship.fromTable);
        auto target = tables_.find(relationship.toTable);

        if (
            source == tables_.end() ||
            target == tables_.end()
        ) {
            throw std::invalid_argument(
                "Relationship references unknown table"
            );
        }

        if (
            !containsColumn(source->second, relationship.fromColumn) ||
            !containsColumn(target->second, relationship.toColumn)
        ) {
            throw std::invalid_argument(
                "Relationship references unknown column"
            );
        }

        relationships_.push_back(relationship);
    }

    const std::map<std::string, Table>& tables() const {
        return tables_;
    }

    const std::vector<Relationship>& relationships() const {
        return relationships_;
    }

    double estimatedMemoryMB() const {
        double total = 0;

        for (const auto& entry : tables_) {
            total += entry.second.estimateMemoryMB();
        }

        return total;
    }

    void printStatistics() const {
        std::uint64_t totalRows = 0;
        std::size_t totalColumns = 0;

        for (const auto& entry : tables_) {
            totalRows += entry.second.rows();
            totalColumns += entry.second.columns().size();
        }

        std::cout
            << "\nMODEL STATISTICS\n"
            << "Model: " << name_ << '\n'
            << "Tables: " << tables_.size() << '\n'
            << "Relationships: " << relationships_.size() << '\n'
            << "Rows: " << totalRows << '\n'
            << "Columns: " << totalColumns << '\n'
            << "Estimated Import Memory: "
            << std::fixed << std::setprecision(2)
            << estimatedMemoryMB() << " MB\n";
    }
};


// ============================================================
// 7. OPTIMIZATION FINDINGS
// ============================================================

struct Finding {
    std::string category;
    std::string subject;
    Severity severity;
    std::string description;
    std::string recommendation;
};

class ModelOptimizer {

public:

    std::vector<Finding> analyze(
        const SemanticModel& model
    ) const {

        std::vector<Finding> findings;

        for (const auto& entry : model.tables()) {
            const Table& table = entry.second;

            if (!table.unusedColumns().empty()) {
                findings.push_back({
                    "Model Size",
                    table.name(),
                    Severity::High,
                    "Unused columns detected",
                    "Remove unused fields from the semantic model"
                });
            }

            if (
                table.role() == TableRole::Fact &&
                table.rows() > 1000000 &&
                !table.queryFolding()
            ) {
                findings.push_back({
                    "Refresh",
                    table.name(),
                    Severity::High,
                    "Large fact table does not fold its source query",
                    "Push supported transformations to the source"
                });
            }

            for (const auto& column : table.columns()) {
                if (
                    column.dataType == "string" &&
                    column.cardinality > 50000
                ) {
                    findings.push_back({
                        "Cardinality",
                        table.name() + "." + column.name,
                        Severity::Medium,
                        "High-cardinality text column",
                        "Review business necessity and encoding cost"
                    });
                }
            }
        }

        for (const auto& relationship : model.relationships()) {
            if (relationship.bidirectional) {
                findings.push_back({
                    "Relationship",
                    relationship.fromTable,
                    Severity::Medium,
                    "Bidirectional filter propagation",
                    "Prefer single-direction filtering when possible"
                });
            }

            if (relationship.manyToMany) {
                findings.push_back({
                    "Relationship",
                    relationship.fromTable,
                    Severity::High,
                    "Many-to-many relationship",
                    "Evaluate bridge-table modeling"
                });
            }
        }

        return findings;
    }
};


// ============================================================
// 8. DAX EXECUTION MODEL
// ============================================================

struct DaxMeasure {
    std::string name;
    std::string expression;
    DaxExecution execution;
    std::uint64_t iterations;
    std::uint32_t repeatedExpressions;
};

class DaxAnalyzer {

public:

    std::vector<std::string> analyze(
        const DaxMeasure& measure
    ) const {

        std::vector<std::string> findings;

        if (measure.iterations > 1000000) {
            findings.push_back(
                "Large iterator workload: test storage-engine "
                "aggregation alternatives."
            );
        }

        if (measure.repeatedExpressions > 1) {
            findings.push_back(
                "Repeated expressions: evaluate variable reuse "
                "within the same filter context."
            );
        }

        if (
            measure.execution == DaxExecution::FormulaEngine
        ) {
            findings.push_back(
                "Formula Engine-heavy execution: inspect complex "
                "iterators, context transitions, and virtual tables."
            );
        }

        if (
            measure.execution == DaxExecution::Mixed
        ) {
            findings.push_back(
                "Mixed execution: inspect Storage Engine requests "
                "and Formula Engine post-processing."
            );
        }

        if (findings.empty()) {
            findings.push_back(
                "No structural DAX issue identified by this model."
            );
        }

        return findings;
    }
};


// ============================================================
// 9. QUERY METRICS
// ============================================================

struct QueryMetrics {
    std::string name;
    double storageEngineMs;
    double formulaEngineMs;
    double sourceMs;
    double visualRenderMs;
    std::uint64_t rowsScanned;
    std::uint64_t rowsReturned;
    bool cacheHit;

    double totalMs() const {
        return storageEngineMs +
            formulaEngineMs +
            sourceMs +
            visualRenderMs;
    }

    void validate() const {
        validateName(name);

        validateNonNegative(
            storageEngineMs, "Storage Engine time"
        );

        validateNonNegative(
            formulaEngineMs, "Formula Engine time"
        );

        validateNonNegative(sourceMs, "Source time");
        validateNonNegative(visualRenderMs, "Visual time");

        if (rowsReturned > rowsScanned) {
            throw std::invalid_argument(
                "Returned rows exceed scanned rows"
            );
        }
    }
};


// ============================================================
// 10. QUERY PERFORMANCE POLICY
// ============================================================

struct PerformanceThresholds {
    double maxFormulaShare = 0.40;
    double maxSourceMs = 500;
    double maxVisualMs = 300;
};

struct QueryEvaluation {
    std::string queryName;
    double totalMs;
    bool eligible;
    std::vector<std::string> violations;
};

class QueryEvaluator {

private:
    PerformanceThresholds thresholds_;

public:

    explicit QueryEvaluator(
        PerformanceThresholds thresholds = {}
    )
        : thresholds_(thresholds) {

        if (
            thresholds_.maxFormulaShare < 0 ||
            thresholds_.maxFormulaShare > 1 ||
            thresholds_.maxSourceMs < 0 ||
            thresholds_.maxVisualMs < 0
        ) {
            throw std::invalid_argument(
                "Invalid performance thresholds"
            );
        }
    }

    QueryEvaluation evaluate(
        const QueryMetrics& metrics
    ) const {

        metrics.validate();

        QueryEvaluation result{
            metrics.name,
            metrics.totalMs(),
            true,
            {}
        };

        const double formulaShare = safeRatio(
            metrics.formulaEngineMs,
            metrics.totalMs()
        );

        if (formulaShare > thresholds_.maxFormulaShare) {
            result.violations.push_back(
                "Formula Engine share exceeds threshold"
            );
        }

        if (metrics.sourceMs > thresholds_.maxSourceMs) {
            result.violations.push_back(
                "Source execution exceeds threshold"
            );
        }

        if (
            metrics.visualRenderMs >
            thresholds_.maxVisualMs
        ) {
            result.violations.push_back(
                "Visual rendering exceeds threshold"
            );
        }

        result.eligible = result.violations.empty();

        return result;
    }
};


// ============================================================
// 11. WORKLOAD MANAGEMENT
// ============================================================

struct QueryTask {
    std::string id;
    double estimatedMs;
    int priority;
    QueryStatus status = QueryStatus::Pending;
};

class WorkloadManager {

private:
    std::vector<QueryTask> tasks_;

public:

    void submit(QueryTask task) {
        validateName(task.id);
        validateNonNegative(
            task.estimatedMs,
            "Estimated execution time"
        );

        if (
            std::any_of(
                tasks_.begin(),
                tasks_.end(),
                [&](const QueryTask& existing) {
                    return existing.id == task.id;
                }
            )
        ) {
            throw std::invalid_argument(
                "Duplicate query task ID"
            );
        }

        tasks_.push_back(std::move(task));
    }

    void prioritize() {
        std::stable_sort(
            tasks_.begin(),
            tasks_.end(),
            [](const QueryTask& a, const QueryTask& b) {
                if (a.priority != b.priority) {
                    return a.priority > b.priority;
                }

                return a.estimatedMs < b.estimatedMs;
            }
        );
    }

    const std::vector<QueryTask>& tasks() const {
        return tasks_;
    }
};


// ============================================================
// 12. SAMPLE MODEL
// ============================================================

SemanticModel buildSampleModel() {

    SemanticModel model("Enterprise Sales Analytics");

    model.addTable(
        Table(
            "Sales",
            TableRole::Fact,
            2000000,
            StorageMode::Import,
            {
                {"SalesID", "integer", 2000000, true, true},
                {"ProductKey", "integer", 5000, true, false},
                {"CustomerKey", "integer", 180000, true, false},
                {"DateKey", "integer", 1825, true, false},
                {"SalesAmount", "decimal", 250000, true, false},
                {"TransactionReference", "string", 1900000, true, false},
                {"UnusedDescription", "string", 2000, false, false}
            },
            true
        )
    );

    model.addTable(
        Table(
            "Product",
            TableRole::Dimension,
            5000,
            StorageMode::Import,
            {
                {"ProductKey", "integer", 5000, true, true},
                {"Category", "string", 12, true, false}
            },
            true
        )
    );

    model.addTable(
        Table(
            "Date",
            TableRole::Dimension,
            1825,
            StorageMode::Import,
            {
                {"DateKey", "integer", 1825, true, true},
                {"Year", "integer", 5, true, false}
            },
            true
        )
    );

    model.addRelationship({
        "Sales",
        "ProductKey",
        "Product",
        "ProductKey",
        false,
        false
    });

    model.addRelationship({
        "Sales",
        "DateKey",
        "Date",
        "DateKey",
        false,
        false
    });

    return model;
}


// ============================================================
// 13. REPORTING
// ============================================================

void printFindings(
    const std::vector<Finding>& findings
) {
    std::cout << "\nMODEL OPTIMIZATION FINDINGS\n";

    if (findings.empty()) {
        std::cout << "No findings.\n";
        return;
    }

    for (const auto& finding : findings) {
        std::cout
            << "\n[" << toString(finding.severity) << "] "
            << finding.category
            << " | " << finding.subject << '\n'
            << "Finding: " << finding.description << '\n'
            << "Action: " << finding.recommendation << '\n';
    }
}

void printEvaluation(
    const QueryEvaluation& evaluation
) {
    std::cout
        << "\nQUERY: " << evaluation.queryName << '\n'
        << "Total: " << evaluation.totalMs << " ms\n"
        << "Policy: "
        << (evaluation.eligible ? "PASS" : "FAIL")
        << '\n';

    for (const auto& violation : evaluation.violations) {
        std::cout << "- " << violation << '\n';
    }
}


// ============================================================
// 14. TESTS AND MAIN
// ============================================================

void runTests() {

    QueryMetrics valid{
        "Test",
        100,
        50,
        0,
        20,
        10000,
        10,
        false
    };

    valid.validate();

    if (valid.totalMs() != 170) {
        throw std::runtime_error("Query duration test failed");
    }

    if (safeRatio(10, 0) != 0) {
        throw std::runtime_error("Safe ratio test failed");
    }

    bool rejected = false;

    try {
        validateNonNegative(-5, "Test");
    } catch (const std::invalid_argument&) {
        rejected = true;
    }

    if (!rejected) {
        throw std::runtime_error(
            "Negative value validation test failed"
        );
    }

    std::cout << "All C++ validation tests passed.\n";
}

} // namespace powerbi


int main() {

    try {

        using namespace powerbi;

        runTests();

        SemanticModel model = buildSampleModel();

        model.printStatistics();

        ModelOptimizer optimizer;

        printFindings(
            optimizer.analyze(model)
        );

        DaxAnalyzer daxAnalyzer;

        DaxMeasure measure{
            "Extended Revenue",
            "SUMX(Sales, Sales[Quantity] * Sales[UnitPrice])",
            DaxExecution::FormulaEngine,
            2000000,
            1
        };

        std::cout << "\nDAX ANALYSIS\n";

        for (const auto& finding :
             daxAnalyzer.analyze(measure)) {
            std::cout << "- " << finding << '\n';
        }

        QueryEvaluator evaluator({
            0.40,
            500,
            300
        });

        std::vector<QueryMetrics> queries = {
            {
                "Monthly Sales",
                120, 80, 0, 100,
                2000000, 24, false
            },
            {
                "Customer Detail",
                180, 350, 700, 120,
                500000, 250, false
            },
            {
                "Product Summary",
                90, 25, 0, 70,
                200000, 20, true
            }
        };

        std::cout << "\nQUERY PERFORMANCE EVALUATION\n";

        for (const auto& query : queries) {
            printEvaluation(
                evaluator.evaluate(query)
            );
        }

        WorkloadManager workload;

        workload.submit({
            "Q-101", 350, 2
        });

        workload.submit({
            "Q-102", 100, 5
        });

        workload.submit({
            "Q-103", 200, 3
        });

        workload.prioritize();

        std::cout << "\nPRIORITIZED QUERY WORKLOAD\n";

        for (const auto& task : workload.tasks()) {
            std::cout
                << task.id
                << " | Priority: " << task.priority
                << " | Estimated: " << task.estimatedMs
                << " ms\n";
        }

        std::cout
            << "\nPerformance evaluation completed.\n";

    } catch (const std::exception& error) {

        std::cerr
            << "Execution error: "
            << error.what()
            << '\n';

        return 1;
    }

    return 0;
}

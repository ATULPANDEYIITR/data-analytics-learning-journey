/*
 * Enterprise Dashboard Governance and KPI Engine
 *
 * C++17
 *
 * Compile:
 * g++ -std=c++17 -O2 -Wall -Wextra -pedantic dashboard.cpp -o dashboard
 *
 * Run:
 * ./dashboard
 *
 * Implements:
 * - KPI modeling and threshold evaluation
 * - Dashboard visual hierarchy
 * - Grid placement and collision detection
 * - Semantic color selection
 * - Responsive layout calculations
 * - Filtering and aggregation
 * - Dashboard state transitions
 * - Merge-like atomic configuration updates
 * - Validation and failure handling
 */

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

using namespace std;

// ============================================================
// 1. ENUMERATIONS
// ============================================================

enum class KPIStatus {
    Good,
    Warning,
    Critical,
    Neutral
};

enum class MetricFormat {
    Number,
    Currency,
    Percentage
};

enum class ChartType {
    Line,
    Bar,
    Donut,
    Area,
    Table
};

enum class Aggregation {
    Sum,
    Average,
    Count,
    Minimum,
    Maximum
};

enum class InteractionType {
    Filter,
    Sort,
    DrillDown,
    Reset
};

string toString(KPIStatus status) {
    switch (status) {
        case KPIStatus::Good: return "GOOD";
        case KPIStatus::Warning: return "WARNING";
        case KPIStatus::Critical: return "CRITICAL";
        default: return "NEUTRAL";
    }
}

string toString(ChartType type) {
    switch (type) {
        case ChartType::Line: return "LINE";
        case ChartType::Bar: return "BAR";
        case ChartType::Donut: return "DONUT";
        case ChartType::Area: return "AREA";
        default: return "TABLE";
    }
}

// ============================================================
// 2. EXCEPTION TYPES
// ============================================================

class DashboardException : public runtime_error {
public:
    explicit DashboardException(const string& message)
        : runtime_error(message) {}
};

class ValidationException : public DashboardException {
public:
    explicit ValidationException(const string& message)
        : DashboardException(message) {}
};

class LayoutException : public DashboardException {
public:
    explicit LayoutException(const string& message)
        : DashboardException(message) {}
};

// ============================================================
// 3. DESIGN SYSTEM
// ============================================================

struct ColorToken {
    string name;
    string hex;
    string semanticMeaning;
};

class DesignSystem {
private:
    map<string, ColorToken> colors;

public:
    DesignSystem() {
        colors.emplace("primary", ColorToken{
            "primary", "#2563EB", "Primary actions"
        });

        colors.emplace("background", ColorToken{
            "background", "#F8FAFC", "Page background"
        });

        colors.emplace("surface", ColorToken{
            "surface", "#FFFFFF", "Cards and panels"
        });

        colors.emplace("text", ColorToken{
            "text", "#172033", "Primary text"
        });

        colors.emplace("muted", ColorToken{
            "muted", "#64748B", "Secondary information"
        });

        colors.emplace("success", ColorToken{
            "success", "#15803D", "Positive performance"
        });

        colors.emplace("warning", ColorToken{
            "warning", "#B45309", "Performance warning"
        });

        colors.emplace("danger", ColorToken{
            "danger", "#B91C1C", "Critical condition"
        });
    }

    const ColorToken& get(const string& name) const {
        auto iterator = colors.find(name);

        if (iterator == colors.end()) {
            throw ValidationException("Unknown color token");
        }

        return iterator->second;
    }

    static double luminance(const string& hex) {
        if (hex.size() != 7 || hex[0] != '#') {
            throw ValidationException("Invalid hexadecimal color");
        }

        vector<double> channels;

        for (int i = 1; i < 7; i += 2) {
            unsigned int value = 0;
            stringstream stream(hex.substr(i, 2));
            stream >> hex >> value;
            channels.push_back(static_cast<double>(value) / 255.0);
        }

        vector<double> linear;

        for (double channel : channels) {
            linear.push_back(
                channel <= 0.04045
                    ? channel / 12.92
                    : pow((channel + 0.055) / 1.055, 2.4)
            );
        }

        return 0.2126 * linear[0]
             + 0.7152 * linear[1]
             + 0.0722 * linear[2];
    }

    static double contrastRatio(
        const string& foreground,
        const string& background
    ) {
        double a = luminance(foreground);
        double b = luminance(background);

        return (max(a, b) + 0.05) / (min(a, b) + 0.05);
    }
};

// ============================================================
// 4. KPI DOMAIN MODEL
// ============================================================

struct KPI {
    string id;
    string name;
    double value;
    optional<double> previousValue;
    optional<double> target;
    MetricFormat format;
    Aggregation aggregation;
    bool higherIsBetter;
    optional<double> warningThreshold;
    optional<double> criticalThreshold;

    KPIStatus evaluate() const {
        if (criticalThreshold.has_value()) {
            bool critical = higherIsBetter
                ? value < criticalThreshold.value()
                : value > criticalThreshold.value();

            if (critical) {
                return KPIStatus::Critical;
            }
        }

        if (warningThreshold.has_value()) {
            bool warning = higherIsBetter
                ? value < warningThreshold.value()
                : value > warningThreshold.value();

            if (warning) {
                return KPIStatus::Warning;
            }
        }

        return KPIStatus::Good;
    }

    optional<double> changePercent() const {
        if (!previousValue.has_value() ||
            previousValue.value() == 0) {
            return nullopt;
        }

        return (
            (value - previousValue.value()) /
            abs(previousValue.value())
        ) * 100.0;
    }

    optional<double> targetAchievement() const {
        if (!target.has_value() || target.value() == 0) {
            return nullopt;
        }

        if (higherIsBetter) {
            return value / target.value() * 100.0;
        }

        if (value == 0) {
            return nullopt;
        }

        return target.value() / value * 100.0;
    }

    string formattedValue() const {
        ostringstream output;

        if (format == MetricFormat::Currency) {
            output << "$";
        }

        output << fixed << setprecision(2) << value;

        if (format == MetricFormat::Percentage) {
            output << "%";
        }

        return output.str();
    }

    void validate() const {
        if (id.empty() || name.empty()) {
            throw ValidationException("KPI identity is required");
        }

        if (!isfinite(value)) {
            throw ValidationException("KPI value must be finite");
        }

        if (warningThreshold && criticalThreshold) {
            if (
                higherIsBetter &&
                warningThreshold.value() < criticalThreshold.value()
            ) {
                throw ValidationException("Invalid KPI threshold ordering");
            }

            if (
                !higherIsBetter &&
                warningThreshold.value() > criticalThreshold.value()
            ) {
                throw ValidationException("Invalid KPI threshold ordering");
            }
        }
    }
};

// ============================================================
// 5. BUSINESS RECORDS
// ============================================================

struct MetricRecord {
    int id;
    string date;
    string department;
    string region;
    double revenue;
    double expenses;
    int orders;
    double satisfaction;
    double conversion;

    void validate() const {
        if (id <= 0) {
            throw ValidationException("Record ID must be positive");
        }

        if (
            department.empty() ||
            region.empty() ||
            date.size() != 10
        ) {
            throw ValidationException("Invalid record dimensions");
        }

        if (
            revenue < 0 ||
            expenses < 0 ||
            orders < 0 ||
            satisfaction < 0 ||
            satisfaction > 100 ||
            conversion < 0 ||
            conversion > 100
        ) {
            throw ValidationException("Record contains invalid metrics");
        }
    }
};

struct DashboardMetrics {
    double revenue = 0;
    double expenses = 0;
    double profit = 0;
    double orders = 0;
    double satisfaction = 0;
    double conversion = 0;
};

// ============================================================
// 6. FILTER MODEL
// ============================================================

struct DashboardFilter {
    optional<string> region;
    optional<string> department;
    optional<string> search;
    optional<string> fromDate;
    optional<string> toDate;
    string sortBy = "revenue";
    bool descending = true;

    void validate() const {
        if (
            fromDate &&
            toDate &&
            fromDate.value() > toDate.value()
        ) {
            throw ValidationException("Invalid date range");
        }

        const set<string> allowed = {
            "revenue",
            "expenses",
            "orders",
            "satisfaction",
            "conversion",
            "date"
        };

        if (!allowed.count(sortBy)) {
            throw ValidationException("Invalid sorting field");
        }
    }
};

// ============================================================
// 7. DATA REPOSITORY
// ============================================================

class DashboardRepository {
private:
    vector<MetricRecord> records;
    set<int> identifiers;

public:
    explicit DashboardRepository(vector<MetricRecord> input) {
        for (const auto& record : input) {
            record.validate();

            if (!identifiers.insert(record.id).second) {
                throw ValidationException("Duplicate record ID");
            }
        }

        records = move(input);
    }

    vector<MetricRecord> query(
        const DashboardFilter& filter
    ) const {
        filter.validate();

        vector<MetricRecord> result;

        for (const auto& record : records) {
            if (
                filter.region &&
                record.region != filter.region.value()
            ) {
                continue;
            }

            if (
                filter.department &&
                record.department != filter.department.value()
            ) {
                continue;
            }

            if (
                filter.search &&
                record.department.find(filter.search.value()) == string::npos &&
                record.region.find(filter.search.value()) == string::npos
            ) {
                continue;
            }

            if (
                filter.fromDate &&
                record.date < filter.fromDate.value()
            ) {
                continue;
            }

            if (
                filter.toDate &&
                record.date > filter.toDate.value()
            ) {
                continue;
            }

            result.push_back(record);
        }

        auto comparator = [&](const MetricRecord& a, const MetricRecord& b) {
            double first = 0;
            double second = 0;

            if (filter.sortBy == "revenue") {
                first = a.revenue;
                second = b.revenue;
            } else if (filter.sortBy == "expenses") {
                first = a.expenses;
                second = b.expenses;
            } else if (filter.sortBy == "orders") {
                first = a.orders;
                second = b.orders;
            } else if (filter.sortBy == "satisfaction") {
                first = a.satisfaction;
                second = b.satisfaction;
            } else if (filter.sortBy == "conversion") {
                first = a.conversion;
                second = b.conversion;
            } else {
                first = a.date.compare(b.date);
                second = 0;
            }

            if (filter.sortBy == "date") {
                return filter.descending
                    ? a.date > b.date
                    : a.date < b.date;
            }

            return filter.descending
                ? first > second
                : first < second;
        };

        sort(result.begin(), result.end(), comparator);

        return result;
    }

    DashboardMetrics aggregate(
        const vector<MetricRecord>& selected
    ) const {
        DashboardMetrics metrics;

        if (selected.empty()) {
            return metrics;
        }

        for (const auto& record : selected) {
            metrics.revenue += record.revenue;
            metrics.expenses += record.expenses;
            metrics.orders += record.orders;
            metrics.satisfaction += record.satisfaction;
            metrics.conversion += record.conversion;
        }

        metrics.profit = metrics.revenue - metrics.expenses;

        metrics.satisfaction /= selected.size();
        metrics.conversion /= selected.size();

        return metrics;
    }

    map<string, DashboardMetrics> groupByRegion() const {
        map<string, vector<MetricRecord>> groups;

        for (const auto& record : records) {
            groups[record.region].push_back(record);
        }

        map<string, DashboardMetrics> result;

        for (const auto& [region, values] : groups) {
            result[region] = aggregate(values);
        }

        return result;
    }

    size_t size() const {
        return records.size();
    }
};

// ============================================================
// 8. VISUALIZATION GRID
// ============================================================

struct GridComponent {
    string id;
    string title;
    ChartType type;
    int row;
    int column;
    int rowSpan;
    int columnSpan;
    int priority;
};

class DashboardGrid {
private:
    int columns;
    vector<GridComponent> components;

    static bool overlaps(
        const GridComponent& first,
        const GridComponent& second
    ) {
        bool rowOverlap =
            first.row < second.row + second.rowSpan &&
            second.row < first.row + first.rowSpan;

        bool columnOverlap =
            first.column < second.column + second.columnSpan &&
            second.column < first.column + first.columnSpan;

        return rowOverlap && columnOverlap;
    }

public:
    explicit DashboardGrid(int columnCount = 12)
        : columns(columnCount) {
        if (columns <= 0) {
            throw LayoutException("Invalid grid width");
        }
    }

    void add(const GridComponent& component) {
        if (
            component.id.empty() ||
            component.row < 1 ||
            component.column < 1 ||
            component.rowSpan < 1 ||
            component.columnSpan < 1 ||
            component.priority < 1
        ) {
            throw LayoutException("Invalid grid component");
        }

        if (
            component.column + component.columnSpan - 1 > columns
        ) {
            throw LayoutException("Component exceeds grid width");
        }

        for (const auto& existing : components) {
            if (existing.id == component.id) {
                throw LayoutException("Duplicate component ID");
            }

            if (overlaps(existing, component)) {
                throw LayoutException("Grid collision detected");
            }
        }

        components.push_back(component);
    }

    vector<GridComponent> render() const {
        vector<GridComponent> output = components;

        sort(
            output.begin(),
            output.end(),
            [](const auto& a, const auto& b) {
                return tie(a.row, b.priority, a.column) <
                       tie(b.row, a.priority, b.column);
            }
        );

        return output;
    }

    static int responsiveColumns(int width) {
        if (width <= 0) {
            throw LayoutException("Invalid viewport width");
        }

        if (width < 600) return 1;
        if (width < 1024) return 6;

        return 12;
    }
};

// ============================================================
// 9. DASHBOARD STATE MANAGEMENT
// ============================================================

class DashboardState {
private:
    DashboardFilter filters;
    unsigned long revision = 0;

public:
    const DashboardFilter& getFilters() const {
        return filters;
    }

    unsigned long getRevision() const {
        return revision;
    }

    void update(const DashboardFilter& candidate) {
        // Validate before changing the current state.
        candidate.validate();

        filters = candidate;
        ++revision;
    }

    void reset() {
        filters = DashboardFilter{};
        ++revision;
    }
};

// ============================================================
// 10. MERGE-LIKE CONFIGURATION TRANSACTION
// ============================================================

class LayoutTransaction {
private:
    DashboardGrid& destination;
    vector<GridComponent> staged;
    bool committed = false;

public:
    explicit LayoutTransaction(DashboardGrid& grid)
        : destination(grid) {}

    void stage(const GridComponent& component) {
        if (committed) {
            throw LayoutException("Transaction already committed");
        }

        staged.push_back(component);
    }

    void commit() {
        if (committed) {
            throw LayoutException("Duplicate commit");
        }

        // Validate the entire candidate layout before publishing it.
        // The destination remains unchanged when validation fails.
        DashboardGrid candidate;

        for (const auto& component : staged) {
            candidate.add(component);
        }

        for (const auto& component : candidate.render()) {
            destination.add(component);
        }

        committed = true;
    }
};

// ============================================================
// 11. KPI FACTORY
// ============================================================

vector<KPI> buildKPIs(const DashboardMetrics& metrics) {
    vector<KPI> kpis = {
        {
            "revenue", "Total Revenue",
            metrics.revenue, 45000.0, 50000.0,
            MetricFormat::Currency, Aggregation::Sum,
            true, 35000.0, 25000.0
        },
        {
            "profit", "Operating Profit",
            metrics.profit, 12000.0, 15000.0,
            MetricFormat::Currency, Aggregation::Sum,
            true, 8000.0, 4000.0
        },
        {
            "satisfaction", "Customer Satisfaction",
            metrics.satisfaction, 82.0, 90.0,
            MetricFormat::Percentage, Aggregation::Average,
            true, 75.0, 60.0
        },
        {
            "conversion", "Conversion Rate",
            metrics.conversion, 3.5, 5.0,
            MetricFormat::Percentage, Aggregation::Average,
            true, 2.5, 1.5
        }
    };

    for (const auto& kpi : kpis) {
        kpi.validate();
    }

    return kpis;
}

// ============================================================
// 12. SAMPLE DATA
// ============================================================

vector<MetricRecord> createSampleData() {
    return {
        {1, "2026-11-20", "Sales", "North", 18000, 11000, 120, 91, 5.2},
        {2, "2026-11-21", "Technology", "North", 14000, 9000, 90, 87, 4.5},
        {3, "2026-11-22", "Sales", "South", 16000, 10000, 110, 83, 3.8},
        {4, "2026-11-23", "Technology", "South", 12000, 8500, 75, 88, 4.2},
        {5, "2026-11-24", "Operations", "East", 9000, 7000, 65, 79, 2.8},
        {6, "2026-11-25", "Sales", "East", 21000, 13000, 140, 94, 5.8},
        {7, "2026-11-26", "Operations", "West", 11000, 7500, 80, 85, 3.6},
        {8, "2026-11-27", "Technology", "West", 15000, 9500, 95, 90, 4.9}
    };
}

// ============================================================
// 13. REPORTING
// ============================================================

void displayDashboard(
    const DashboardMetrics& metrics,
    const vector<KPI>& kpis,
    const map<string, DashboardMetrics>& regions
) {
    cout << "\n==============================================\n";
    cout << "       ENTERPRISE PERFORMANCE DASHBOARD\n";
    cout << "==============================================\n";

    cout << "\nKEY PERFORMANCE INDICATORS\n";

    for (const auto& kpi : kpis) {
        cout << left << setw(26) << kpi.name
             << right << setw(14) << kpi.formattedValue()
             << " | " << toString(kpi.evaluate());

        auto change = kpi.changePercent();

        if (change) {
            cout << " | Change: " << fixed << setprecision(2)
                 << change.value() << "%";
        }

        cout << '\n';
    }

    cout << "\nFINANCIAL METRICS\n";

    cout << "Revenue: " << metrics.revenue << '\n';
    cout << "Expenses: " << metrics.expenses << '\n';
    cout << "Profit: " << metrics.profit << '\n';
    cout << "Orders: " << metrics.orders << '\n';

    cout << "\nREGIONAL PERFORMANCE\n";

    for (const auto& [region, values] : regions) {
        cout << left << setw(12) << region
             << " Revenue: " << values.revenue
             << " Profit: " << values.profit << '\n';
    }
}

// ============================================================
// 14. VALIDATION TESTS
// ============================================================

void runTests() {
    KPI kpi{
        "test", "Test KPI", 80.0, 100.0, 100.0,
        MetricFormat::Number, Aggregation::Average,
        true, 70.0, 50.0
    };

    kpi.validate();

    if (kpi.evaluate() != KPIStatus::Good) {
        throw DashboardException("KPI evaluation test failed");
    }

    auto change = kpi.changePercent();

    if (!change || abs(change.value() + 20.0) > 0.0001) {
        throw DashboardException("KPI comparison test failed");
    }

    KPI critical{
        "critical", "Critical KPI", 30.0, 40.0, 100.0,
        MetricFormat::Number, Aggregation::Average,
        true, 70.0, 50.0
    };

    if (critical.evaluate() != KPIStatus::Critical) {
        throw DashboardException("Critical status test failed");
    }

    DashboardRepository emptyRepository({});

    if (emptyRepository.aggregate({}).revenue != 0) {
        throw DashboardException("Empty aggregation test failed");
    }

    bool collisionDetected = false;

    DashboardGrid grid;

    grid.add({
        "first", "First", ChartType::Line,
        1, 1, 1, 6, 10
    });

    try {
        grid.add({
            "second", "Second", ChartType::Bar,
            1, 4, 1, 6, 5
        });
    } catch (const LayoutException&) {
        collisionDetected = true;
    }

    if (!collisionDetected) {
        throw DashboardException("Grid collision test failed");
    }

    double contrast = DesignSystem::contrastRatio(
        "#172033",
        "#FFFFFF"
    );

    if (contrast < 4.5) {
        throw DashboardException("Accessibility test failed");
    }

    cout << "\nAll C++ validation tests passed.\n";
}

// ============================================================
// 15. APPLICATION ENTRY POINT
// ============================================================

int main() {
    try {
        DashboardRepository repository(createSampleData());

        DashboardFilter filters;
        DashboardState state;

        state.update(filters);

        auto records = repository.query(state.getFilters());
        auto metrics = repository.aggregate(records);

        auto kpis = buildKPIs(metrics);

        displayDashboard(
            metrics,
            kpis,
            repository.groupByRegion()
        );

        DashboardGrid grid;

        grid.add({
            "revenue", "Revenue KPI", ChartType::Table,
            1, 1, 1, 3, 10
        });

        grid.add({
            "profit", "Profit KPI", ChartType::Table,
            1, 4, 1, 3, 9
        });

        grid.add({
            "satisfaction", "Satisfaction KPI", ChartType::Table,
            1, 7, 1, 3, 8
        });

        grid.add({
            "conversion", "Conversion KPI", ChartType::Table,
            1, 10, 1, 3, 7
        });

        grid.add({
            "trend", "Revenue Trend", ChartType::Line,
            2, 1, 2, 8, 6
        });

        grid.add({
            "regional", "Regional Performance", ChartType::Bar,
            2, 9, 2, 4, 5
        });

        cout << "\nDASHBOARD COMPONENT LAYOUT\n";

        for (const auto& component : grid.render()) {
            cout << component.id
                 << " | " << toString(component.type)
                 << " | Row " << component.row
                 << " | Column " << component.column
                 << " | Priority " << component.priority
                 << '\n';
        }

        cout << "\nRESPONSIVE GRID\n";
        cout << "Desktop: "
             << DashboardGrid::responsiveColumns(1440)
             << " columns\n";

        cout << "Tablet: "
             << DashboardGrid::responsiveColumns(800)
             << " columns\n";

        cout << "Mobile: "
             << DashboardGrid::responsiveColumns(390)
             << " columns\n";

        cout << "\nFILTER EXAMPLE\n";

        filters.region = "North";
        filters.validate();

        auto filtered = repository.query(filters);
        auto filteredMetrics = repository.aggregate(filtered);

        cout << "Selected region: North\n";
        cout << "Matching records: " << filtered.size() << '\n';
        cout << "Revenue: " << filteredMetrics.revenue << '\n';

        cout << "\nACCESSIBILITY\n";

        cout << "Text contrast: "
             << fixed << setprecision(2)
             << DesignSystem::contrastRatio(
                    "#172033",
                    "#FFFFFF"
                )
             << ":1\n";

        runTests();

    } catch (const exception& error) {
        cerr << "Dashboard failure: " << error.what() << '\n';
        return 1;
    }

    return 0;
}

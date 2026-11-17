#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

/*
 * POWER BI DATA LOADING
 *
 * C++17 repository-style data ingestion and storage-mode engine.
 *
 * Models:
 * - CSV and Excel-exported CSV files
 * - Database connection adapters
 * - Web source metadata and connection validation
 * - Import, DirectQuery, and Live Connection modes
 * - Data transformation and quality checks
 * - Refresh management
 * - Reporting and aggregation
 *
 * No external libraries.
 */

using namespace std;


// ---------------------------------------------------------
// Enumerations
// ---------------------------------------------------------

enum class SourceType {
    CSV,
    EXCEL_EXPORT,
    DATABASE,
    WEB
};

enum class StorageMode {
    IMPORT,
    DIRECT_QUERY,
    LIVE_CONNECTION
};

enum class ConnectionStatus {
    CREATED,
    CONNECTED,
    LOADING,
    READY,
    FAILED,
    DISABLED
};


// ---------------------------------------------------------
// Exceptions
// ---------------------------------------------------------

class DataLoadingException : public runtime_error {
public:
    explicit DataLoadingException(const string& message)
        : runtime_error(message) {}
};

class ValidationException : public DataLoadingException {
public:
    explicit ValidationException(const string& message)
        : DataLoadingException(message) {}
};

class ConnectionException : public DataLoadingException {
public:
    explicit ConnectionException(const string& message)
        : DataLoadingException(message) {}
};


// ---------------------------------------------------------
// Domain models
// ---------------------------------------------------------

struct SalesRecord {
    string product;
    int quantity;
    double revenue;
};

struct DataConnection {
    string id;
    SourceType type;
    string location;
    bool enabled = true;
    int timeoutSeconds = 15;
    ConnectionStatus status = ConnectionStatus::CREATED;
};

struct LoadResult {
    vector<SalesRecord> rows;
    size_t rejectedRows = 0;
    string sourceId;
    bool successful = false;
    string error;
};

struct BranchStatistics {
    size_t totalRows = 0;
    size_t rejectedRows = 0;
    double totalRevenue = 0.0;
    long long totalQuantity = 0;
};


// ---------------------------------------------------------
// CSV parsing
// ---------------------------------------------------------

class CSVReader {

public:

    static vector<string> parseLine(
        const string& line,
        char delimiter = ','
    ) {

        vector<string> fields;

        string field;
        bool quoted = false;

        for (size_t i = 0; i < line.size(); ++i) {

            char current = line[i];

            if (quoted) {

                if (current == '"') {

                    if (
                        i + 1 < line.size() &&
                        line[i + 1] == '"'
                    ) {
                        field += '"';
                        ++i;
                    } else {
                        quoted = false;
                    }

                } else {
                    field += current;
                }

            } else if (current == '"') {

                if (!field.empty()) {
                    throw ValidationException(
                        "Unexpected quote in CSV."
                    );
                }

                quoted = true;

            } else if (current == delimiter) {

                fields.push_back(field);
                field.clear();

            } else {
                field += current;
            }
        }

        if (quoted) {
            throw ValidationException(
                "Unclosed quoted CSV field."
            );
        }

        fields.push_back(field);

        return fields;
    }

    static vector<SalesRecord> read(
        const string& filename
    ) {

        ifstream input(filename);

        if (!input.is_open()) {
            throw ConnectionException(
                "Unable to open CSV file: " + filename
            );
        }

        string line;

        if (!getline(input, line)) {
            throw ValidationException(
                "CSV file is empty."
            );
        }

        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }

        vector<string> headers = parseLine(line);

        unordered_map<string, size_t> positions;

        for (size_t i = 0; i < headers.size(); ++i) {

            string header = headers[i];

            transform(
                header.begin(),
                header.end(),
                header.begin(),
                [](unsigned char c) {
                    return static_cast<char>(tolower(c));
                }
            );

            if (!positions.emplace(header, i).second) {
                throw ValidationException(
                    "Duplicate CSV header."
                );
            }
        }

        if (
            !positions.count("product") ||
            !positions.count("quantity") ||
            !positions.count("revenue")
        ) {
            throw ValidationException(
                "CSV requires product, quantity, and revenue."
            );
        }

        vector<SalesRecord> records;

        while (getline(input, line)) {

            if (!line.empty() && line.back() == '\r') {
                line.pop_back();
            }

            if (line.empty()) {
                continue;
            }

            vector<string> values = parseLine(line);

            if (values.size() != headers.size()) {
                throw ValidationException(
                    "CSV row has incorrect column count."
                );
            }

            try {

                string product = values[
                    positions.at("product")
                ];

                int quantity = stoi(
                    values[positions.at("quantity")]
                );

                size_t parsed = 0;

                double revenue = stod(
                    values[positions.at("revenue")],
                    &parsed
                );

                if (
                    parsed != values[
                        positions.at("revenue")
                    ].size()
                ) {
                    throw ValidationException(
                        "Revenue contains invalid characters."
                    );
                }

                records.push_back({
                    product,
                    quantity,
                    revenue
                });

            } catch (const exception&) {
                // Invalid records are counted by the loader.
                continue;
            }
        }

        return records;
    }
};


// ---------------------------------------------------------
// Data validation
// ---------------------------------------------------------

class DataValidator {

public:

    static bool valid(const SalesRecord& record) {

        return
            !record.product.empty() &&
            record.quantity >= 0 &&
            isfinite(record.revenue) &&
            record.revenue >= 0.0;
    }

    static vector<SalesRecord> clean(
        const vector<SalesRecord>& input,
        size_t& rejected
    ) {

        vector<SalesRecord> output;

        rejected = 0;

        output.reserve(input.size());

        for (const auto& record : input) {

            if (valid(record)) {
                output.push_back(record);
            } else {
                ++rejected;
            }
        }

        if (output.empty()) {
            throw ValidationException(
                "No valid sales records remain."
            );
        }

        return output;
    }
};


// ---------------------------------------------------------
// Abstract source adapter
// ---------------------------------------------------------

class SourceAdapter {

public:

    virtual ~SourceAdapter() = default;

    virtual vector<SalesRecord> read(
        const DataConnection& connection
    ) = 0;
};


class FileSourceAdapter : public SourceAdapter {

public:

    vector<SalesRecord> read(
        const DataConnection& connection
    ) override {

        return CSVReader::read(
            connection.location
        );
    }
};


// ---------------------------------------------------------
// Database adapter
// ---------------------------------------------------------

class DatabaseSourceAdapter : public SourceAdapter {

private:

    map<string, vector<SalesRecord>> tables;

public:

    explicit DatabaseSourceAdapter(
        map<string, vector<SalesRecord>> sourceTables
    ) : tables(move(sourceTables)) {}

    vector<SalesRecord> read(
        const DataConnection& connection
    ) override {

        auto iterator = tables.find(
            connection.location
        );

        if (iterator == tables.end()) {
            throw ConnectionException(
                "Database table does not exist."
            );
        }

        return iterator->second;
    }
};


// ---------------------------------------------------------
// Web connection configuration
// ---------------------------------------------------------

class WebSourceConfiguration {

public:

    static void validateURL(
        const string& url,
        int timeoutSeconds
    ) {

        if (url.rfind("https://", 0) != 0) {
            throw ValidationException(
                "Web sources must use HTTPS."
            );
        }

        if (timeoutSeconds <= 0) {
            throw ValidationException(
                "Invalid web timeout."
            );
        }

        if (url.size() > 2048) {
            throw ValidationException(
                "Web URL exceeds maximum length."
            );
        }
    }
};


// ---------------------------------------------------------
// Connection registry
// ---------------------------------------------------------

class ConnectionRegistry {

private:

    unordered_map<string, DataConnection> connections;

public:

    void registerConnection(
        const DataConnection& connection
    ) {

        if (
            connection.id.empty() ||
            connection.location.empty()
        ) {
            throw ValidationException(
                "Connection ID and location are required."
            );
        }

        if (connection.timeoutSeconds <= 0) {
            throw ValidationException(
                "Connection timeout must be positive."
            );
        }

        if (
            connections.count(connection.id)
        ) {
            throw ValidationException(
                "Duplicate connection identifier."
            );
        }

        connections.emplace(
            connection.id,
            connection
        );
    }

    DataConnection& get(const string& id) {

        auto iterator = connections.find(id);

        if (iterator == connections.end()) {
            throw ConnectionException(
                "Connection not found."
            );
        }

        return iterator->second;
    }

    void disable(const string& id) {

        auto& connection = get(id);

        connection.enabled = false;
        connection.status = ConnectionStatus::DISABLED;
    }
};


// ---------------------------------------------------------
// Data loading service
// ---------------------------------------------------------

class DataLoadingService {

private:

    ConnectionRegistry& registry;

    FileSourceAdapter fileAdapter;

    DatabaseSourceAdapter databaseAdapter;

public:

    DataLoadingService(
        ConnectionRegistry& registryRef,
        DatabaseSourceAdapter database
    )
        : registry(registryRef),
          databaseAdapter(move(database)) {}

    LoadResult load(const string& connectionId) {

        LoadResult result;

        result.sourceId = connectionId;

        auto& connection = registry.get(
            connectionId
        );

        try {

            if (!connection.enabled) {
                throw ConnectionException(
                    "Connection is disabled."
                );
            }

            connection.status = ConnectionStatus::CONNECTED;

            connection.status = ConnectionStatus::LOADING;

            vector<SalesRecord> raw;

            switch (connection.type) {

                case SourceType::CSV:
                case SourceType::EXCEL_EXPORT:

                    raw = fileAdapter.read(connection);
                    break;

                case SourceType::DATABASE:

                    raw = databaseAdapter.read(connection);
                    break;

                case SourceType::WEB:

                    WebSourceConfiguration::validateURL(
                        connection.location,
                        connection.timeoutSeconds
                    );

                    throw ConnectionException(
                        "HTTP transport is not included in "
                        "the standard-library demonstration."
                    );
            }

            result.rows = DataValidator::clean(
                raw,
                result.rejectedRows
            );

            result.successful = true;

            connection.status = ConnectionStatus::READY;

        } catch (const exception& error) {

            result.successful = false;
            result.error = error.what();

            connection.status = ConnectionStatus::FAILED;
        }

        return result;
    }
};


// ---------------------------------------------------------
// Semantic model
// ---------------------------------------------------------

class SemanticModel {

private:

    unordered_map<
        string,
        vector<SalesRecord>
    > importedTables;

    vector<string> refreshHistory;

public:

    void importTable(
        const string& tableName,
        const LoadResult& result
    ) {

        if (!result.successful) {
            throw DataLoadingException(
                "Cannot import unsuccessful load."
            );
        }

        if (tableName.empty()) {
            throw ValidationException(
                "Table name cannot be empty."
            );
        }

        // Copy-on-replacement preserves the old table
        // when validation or loading fails.
        importedTables.insert_or_assign(
            tableName,
            result.rows
        );

        refreshHistory.push_back(
            result.sourceId
        );
    }

    const vector<SalesRecord>& getTable(
        const string& tableName
    ) const {

        auto iterator = importedTables.find(
            tableName
        );

        if (iterator == importedTables.end()) {
            throw DataLoadingException(
                "Imported table does not exist."
            );
        }

        return iterator->second;
    }

    vector<SalesRecord> directQuery(
        DataLoadingService& loader,
        const string& connectionId
    ) const {

        // Source retrieval happens on each execution.
        LoadResult result = loader.load(connectionId);

        if (!result.successful) {
            throw DataLoadingException(result.error);
        }

        return result.rows;
    }

    void liveConnection(
        bool externalModelAvailable
    ) const {

        if (!externalModelAvailable) {
            throw ConnectionException(
                "External semantic model unavailable."
            );
        }
    }

    size_t tableCount() const {
        return importedTables.size();
    }

    const vector<string>& history() const {
        return refreshHistory;
    }
};


// ---------------------------------------------------------
// Reporting engine
// ---------------------------------------------------------

class ReportingEngine {

public:

    static BranchStatistics calculate(
        const vector<SalesRecord>& records
    ) {

        BranchStatistics statistics;

        for (const auto& record : records) {

            statistics.totalRows++;

            statistics.totalQuantity +=
                record.quantity;

            statistics.totalRevenue +=
                record.revenue;
        }

        return statistics;
    }

    static map<string, double> revenueByProduct(
        const vector<SalesRecord>& records
    ) {

        map<string, double> totals;

        for (const auto& record : records) {

            totals[record.product] +=
                record.revenue;
        }

        return totals;
    }
};


// ---------------------------------------------------------
// Demo file creation
// ---------------------------------------------------------

void createDemoCSV(const string& filename) {

    ofstream output(filename);

    if (!output) {
        throw ConnectionException(
            "Unable to create demonstration CSV."
        );
    }

    output
        << "product,quantity,revenue\n"
        << "Laptop,5,250000\n"
        << "Monitor,8,120000\n"
        << "Keyboard,20,40000\n"
        << "Mouse,-2,10000\n";
}


// ---------------------------------------------------------
// Main application
// ---------------------------------------------------------

int main() {

    try {

        cout << fixed << setprecision(2);

        const string filename =
            "powerbi_cpp_sales.csv";

        createDemoCSV(filename);

        vector<SalesRecord> databaseRecords = {
            {"Desktop", 3, 180000},
            {"Printer", 2, 30000}
        };

        DatabaseSourceAdapter database({
            {"sales", databaseRecords}
        });

        ConnectionRegistry registry;

        registry.registerConnection({
            "csv_connection",
            SourceType::CSV,
            filename,
            true,
            15
        });

        registry.registerConnection({
            "database_connection",
            SourceType::DATABASE,
            "sales",
            true,
            15
        });

        registry.registerConnection({
            "excel_export_connection",
            SourceType::EXCEL_EXPORT,
            filename,
            true,
            15
        });

        registry.registerConnection({
            "web_connection",
            SourceType::WEB,
            "https://example.com/api/sales",
            true,
            10
        });

        DataLoadingService loader(
            registry,
            move(database)
        );

        SemanticModel model;

        cout << "\nPOWER BI DATA LOADING ENGINE\n";
        cout << "============================\n";

        vector<string> sourceIds = {
            "csv_connection",
            "database_connection",
            "excel_export_connection"
        };

        vector<SalesRecord> combined;

        for (const auto& sourceId : sourceIds) {

            LoadResult result = loader.load(
                sourceId
            );

            cout << "\nSource: " << sourceId << "\n";

            if (!result.successful) {

                cout << "FAILED: "
                     << result.error << "\n";

                continue;
            }

            cout << "Loaded records: "
                 << result.rows.size() << "\n";

            cout << "Rejected records: "
                 << result.rejectedRows << "\n";

            model.importTable(
                sourceId,
                result
            );

            combined.insert(
                combined.end(),
                result.rows.begin(),
                result.rows.end()
            );
        }

        cout << "\nIMPORT MODE\n";

        cout << "Imported tables: "
             << model.tableCount() << "\n";

        cout << "\nDIRECTQUERY-STYLE MODE\n";

        vector<SalesRecord> liveRows =
            model.directQuery(
                loader,
                "csv_connection"
            );

        cout << "Fresh source records: "
             << liveRows.size() << "\n";

        cout << "\nLIVE CONNECTION MODE\n";

        model.liveConnection(true);

        cout << "External semantic model is available.\n";

        cout << "\nSALES REPORT\n";

        BranchStatistics report =
            ReportingEngine::calculate(combined);

        cout << "Records: "
             << report.totalRows << "\n";

        cout << "Quantity: "
             << report.totalQuantity << "\n";

        cout << "Revenue: "
             << report.totalRevenue << "\n";

        cout << "\nREVENUE BY PRODUCT\n";

        auto productTotals =
            ReportingEngine::revenueByProduct(combined);

        for (const auto& entry : productTotals) {

            cout << left
                 << setw(15)
                 << entry.first
                 << right
                 << entry.second
                 << "\n";
        }

        cout << "\nWEB CONNECTION VALIDATION\n";

        try {

            WebSourceConfiguration::validateURL(
                "http://insecure.example.com",
                10
            );

        } catch (const exception& error) {

            cout << "Expected failure: "
                 << error.what() << "\n";
        }

        cout << "\nREFRESH HISTORY\n";

        for (const auto& entry : model.history()) {
            cout << entry << "\n";
        }

        cout << "\nProcessing completed.\n";

    } catch (const exception& error) {

        cerr << "Fatal error: "
             << error.what() << "\n";

        return 1;
    }

    return 0;
}

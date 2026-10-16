#include <algorithm>
#include <charconv>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;

/*
 * Repository-equipment file ingestion case study.
 *
 * This program models a field-inspection service that receives a CSV export,
 * validates each asset record, creates a JSON report and a plain-text audit
 * trail, and publishes output through temporary files.
 *
 * Build:
 *   g++ -std=c++17 -Wall -Wextra -Wpedantic file_handling.cpp -o file_handling
 *
 * Run:
 *   ./file_handling
 *   ./file_handling ./inspection_workspace
 */

struct Asset {
    std::string id;
    std::string department;
    long long replacementCostPaise{};
};

struct RejectedRecord {
    std::size_t recordNumber{};
    std::string reason;
};

struct DepartmentSummary {
    std::size_t assetCount{};
    long long totalCostPaise{};
};

struct ImportReport {
    std::vector<Asset> accepted;
    std::vector<RejectedRecord> rejected;
    std::map<std::string, DepartmentSummary> departments;
};

void require(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

std::string trim(const std::string& value) {
    const auto first = value.find_first_not_of(" \t\r\n");

    if (first == std::string::npos) {
        return "";
    }

    const auto last = value.find_last_not_of(" \t\r\n");
    return value.substr(first, last - first + 1);
}

fs::path safePath(const fs::path& root, const fs::path& relative) {
    if (relative.empty() || relative.is_absolute() ||
        relative.has_root_name() || relative.has_root_directory()) {
        throw std::runtime_error("Expected a non-empty relative file path.");
    }

    for (const auto& component : relative) {
        if (component == "..") {
            throw std::runtime_error("Parent-directory traversal is forbidden.");
        }
    }

    const fs::path resolvedRoot = fs::absolute(root).lexically_normal();
    const fs::path resolvedTarget =
        (resolvedRoot / relative).lexically_normal();

    auto rootIt = resolvedRoot.begin();
    auto targetIt = resolvedTarget.begin();

    for (; rootIt != resolvedRoot.end(); ++rootIt, ++targetIt) {
        if (targetIt == resolvedTarget.end() || *rootIt != *targetIt) {
            throw std::runtime_error("Path escapes the workspace.");
        }
    }

    return resolvedTarget;
}

void ensureDirectory(const fs::path& directory) {
    std::error_code error;
    fs::create_directories(directory, error);

    if (error) {
        throw std::runtime_error(
            "Cannot create directory: " + directory.string() +
            ": " + error.message()
        );
    }

    if (!fs::is_directory(directory)) {
        throw std::runtime_error("Path is not a directory: " + directory.string());
    }
}

std::string readTextFile(const fs::path& path) {
    std::ifstream input(path, std::ios::binary);

    if (!input) {
        throw std::runtime_error("Cannot open text file: " + path.string());
    }

    std::ostringstream buffer;
    buffer << input.rdbuf();

    if (input.bad()) {
        throw std::runtime_error("Error while reading: " + path.string());
    }

    // The standard library does not provide a portable Unicode conversion
    // policy for every text encoding. This workflow treats file contents as
    // UTF-8 bytes and expects the producer to supply valid UTF-8.
    return buffer.str();
}

void writeAtomically(const fs::path& destination, const std::string& contents) {
    ensureDirectory(destination.parent_path());

    fs::path temporary = destination;
    temporary += ".tmp";

    // This educational writer uses a deterministic temporary name. A
    // concurrent production writer should use a unique exclusive-create name.
    {
        std::ofstream output(
            temporary,
            std::ios::binary | std::ios::trunc
        );

        if (!output) {
            throw std::runtime_error(
                "Cannot create temporary file: " + temporary.string()
            );
        }

        output.write(
            contents.data(),
            static_cast<std::streamsize>(contents.size())
        );
        output.flush();

        if (!output) {
            throw std::runtime_error("Failed while writing temporary file.");
        }
    }

    std::error_code error;
    fs::rename(temporary, destination, error);

    if (error) {
        // Some platforms do not replace an existing destination with rename.
        // Do not delete the previous destination as a fallback: doing so would
        // create a data-loss window if the second operation failed.
        fs::remove(temporary);
        throw std::runtime_error(
            "Cannot publish file " + destination.string() +
            ": " + error.message()
        );
    }
}

std::vector<std::string> parseCsvRecord(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool quoted = false;
    bool quoteClosed = false;

    for (std::size_t index = 0; index < line.size(); ++index) {
        const char character = line[index];

        if (quoted) {
            if (character == '"') {
                if (index + 1 < line.size() && line[index + 1] == '"') {
                    field += '"';
                    ++index;
                } else {
                    quoted = false;
                    quoteClosed = true;
                }
            } else {
                field += character;
            }
            continue;
        }

        if (quoteClosed && character != ',') {
            throw std::runtime_error(
                "Unexpected character after a quoted CSV field."
            );
        }

        if (character == ',') {
            fields.push_back(field);
            field.clear();
            quoteClosed = false;
        } else if (character == '"') {
            if (!field.empty() || quoteClosed) {
                throw std::runtime_error("Unexpected quote in CSV field.");
            }
            quoted = true;
        } else {
            field += character;
        }
    }

    if (quoted) {
        throw std::runtime_error("Unterminated quoted CSV field.");
    }

    fields.push_back(field);
    return fields;
}

std::vector<std::string> parseCsvDocument(const std::string& contents) {
    std::vector<std::string> records;
    std::string record;
    bool quoted = false;

    // Record boundaries inside quoted CSV fields are data, not separators.
    for (std::size_t index = 0; index < contents.size(); ++index) {
        const char character = contents[index];

        if (character == '"') {
            if (quoted && index + 1 < contents.size() &&
                contents[index + 1] == '"') {
                record += "\"\"";
                ++index;
                continue;
            }
            quoted = !quoted;
            record += character;
        } else if ((character == '\n' || character == '\r') && !quoted) {
            if (character == '\r' && index + 1 < contents.size() &&
                contents[index + 1] == '\n') {
                ++index;
            }

            if (!record.empty()) {
                records.push_back(record);
                record.clear();
            }
        } else {
            record += character;
        }
    }

    require(!quoted, "CSV document ends inside a quoted field.");

    if (!record.empty()) {
        records.push_back(record);
    }

    return records;
}

long long parseCostPaise(const std::string& text) {
    const std::string value = trim(text);
    require(!value.empty(), "Replacement cost cannot be empty.");

    const auto decimal = value.find('.');
    const std::string whole = value.substr(0, decimal);
    std::string fraction =
        decimal == std::string::npos ? "" : value.substr(decimal + 1);

    require(!whole.empty(), "Replacement cost requires an integer part.");
    require(fraction.size() <= 2, "Cost supports at most two decimal places.");

    while (fraction.size() < 2) {
        fraction += '0';
    }

    long long rupees = 0;
    const auto parsed = std::from_chars(
        whole.data(),
        whole.data() + whole.size(),
        rupees
    );

    require(
        parsed.ec == std::errc{} &&
        parsed.ptr == whole.data() + whole.size(),
        "Replacement cost contains an invalid integer."
    );

    long long paise = 0;

    if (!fraction.empty()) {
        const auto fractionResult = std::from_chars(
            fraction.data(),
            fraction.data() + fraction.size(),
            paise
        );

        require(
            fractionResult.ec == std::errc{} &&
            fractionResult.ptr == fraction.data() + fraction.size(),
            "Replacement cost contains an invalid decimal part."
        );
    }

    require(rupees >= 0, "Replacement cost cannot be negative.");
    require(
        rupees <= (1000000000000LL - paise) / 100,
        "Replacement cost exceeds the supported range."
    );

    return rupees * 100 + paise;
}

Asset validateAsset(const std::vector<std::string>& fields) {
    require(fields.size() == 3, "Expected exactly three CSV columns.");

    Asset asset{
        trim(fields[0]),
        trim(fields[1]),
        parseCostPaise(fields[2])
    };

    require(
        asset.id.size() >= 4 &&
        asset.id.size() <= 20 &&
        asset.id.rfind("AST-", 0) == 0,
        "Asset ID must begin with AST- and have a valid length."
    );

    require(
        !asset.department.empty() && asset.department.size() <= 80,
        "Department must contain 1 to 80 bytes."
    );

    require(
        asset.replacementCostPaise <= 100000000000000LL,
        "Replacement cost exceeds the configured limit."
    );

    return asset;
}

ImportReport importAssets(const fs::path& csvPath) {
    const auto records = parseCsvDocument(readTextFile(csvPath));
    require(!records.empty(), "CSV document is empty.");

    const auto headers = parseCsvRecord(records.front());
    require(
        headers == std::vector<std::string>{
            "asset_id", "department", "replacement_cost"
        },
        "Unexpected CSV schema."
    );

    ImportReport report;
    std::set<std::string> seenIds;

    for (std::size_t index = 1; index < records.size(); ++index) {
        try {
            const auto fields = parseCsvRecord(records[index]);
            Asset asset = validateAsset(fields);

            if (!seenIds.insert(asset.id).second) {
                throw std::runtime_error("Duplicate asset identifier.");
            }

            auto& department = report.departments[asset.department];

            if (department.totalCostPaise >
                100000000000000LL - asset.replacementCostPaise) {
                throw std::runtime_error("Department total would overflow.");
            }

            ++department.assetCount;
            department.totalCostPaise += asset.replacementCostPaise;
            report.accepted.push_back(std::move(asset));
        } catch (const std::exception& error) {
            report.rejected.push_back({index + 1, error.what()});
        }
    }

    return report;
}

std::string jsonEscape(const std::string& input) {
    std::ostringstream output;

    for (unsigned char character : input) {
        switch (character) {
            case '"': output << "\\\""; break;
            case '\\': output << "\\\\"; break;
            case '\b': output << "\\b"; break;
            case '\f': output << "\\f"; break;
            case '\n': output << "\\n"; break;
            case '\r': output << "\\r"; break;
            case '\t': output << "\\t"; break;
            default:
                if (character < 0x20) {
                    output << "\\u"
                           << std::hex << std::setw(4) << std::setfill('0')
                           << static_cast<int>(character)
                           << std::dec;
                } else {
                    output << static_cast<char>(character);
                }
        }
    }

    return output.str();
}

std::string moneyString(long long paise) {
    std::ostringstream output;
    output << paise / 100 << '.'
           << std::setw(2) << std::setfill('0') << paise % 100;
    return output.str();
}

std::string makeJsonReport(const ImportReport& report) {
    std::ostringstream output;

    output << "{\n"
           << "  \"accepted_count\": " << report.accepted.size() << ",\n"
           << "  \"rejected_count\": " << report.rejected.size() << ",\n"
           << "  \"assets\": [";

    for (std::size_t index = 0; index < report.accepted.size(); ++index) {
        const auto& asset = report.accepted[index];

        if (index > 0) {
            output << ',';
        }

        output << "\n    {\"asset_id\":\"" << jsonEscape(asset.id)
               << "\",\"department\":\"" << jsonEscape(asset.department)
               << "\",\"replacement_cost\":\""
               << moneyString(asset.replacementCostPaise) << "\"}";
    }

    if (!report.accepted.empty()) {
        output << '\n' << "  ";
    }

    output << "],\n"
           << "  \"rejected_records\": [";

    for (std::size_t index = 0; index < report.rejected.size(); ++index) {
        const auto& rejected = report.rejected[index];

        if (index > 0) {
            output << ',';
        }

        output << "\n    {\"record\": " << rejected.recordNumber
               << ", \"reason\": \"" << jsonEscape(rejected.reason) << "\"}";
    }

    if (!report.rejected.empty()) {
        output << '\n' << "  ";
    }

    output << "]\n}\n";
    return output.str();
}

std::string makeTextSummary(const ImportReport& report) {
    std::ostringstream output;

    output << "Asset import audit\n"
           << "Accepted records: " << report.accepted.size() << '\n'
           << "Rejected records: " << report.rejected.size() << '\n';

    for (const auto& [department, summary] : report.departments) {
        output << department
               << " | assets=" << summary.assetCount
               << " | replacement_cost=" << moneyString(summary.totalCostPaise)
               << '\n';
    }

    for (const auto& rejected : report.rejected) {
        output << "Rejected record " << rejected.recordNumber
               << ": " << rejected.reason << '\n';
    }

    return output.str();
}

void demonstratePathErrors(const fs::path& root) {
    std::cout << "\nPath validation\n";

    for (const fs::path candidate : {
        fs::path("input/assets.csv"),
        fs::path("../outside.csv"),
        fs::path("/tmp/outside.csv")
    }) {
        try {
            std::cout << safePath(root, candidate).string() << '\n';
        } catch (const std::exception& error) {
            std::cout << "Rejected " << candidate.string()
                      << ": " << error.what() << '\n';
        }
    }
}

void demonstrateStreaming(const fs::path& logPath) {
    std::ifstream input(logPath, std::ios::binary);

    if (!input) {
        throw std::runtime_error("Cannot open service log.");
    }

    std::size_t errors = 0;
    std::string line;

    // getline holds only the current record in memory rather than the entire log.
    while (std::getline(input, line)) {
        if (line.find("ERROR") != std::string::npos) {
            ++errors;
        }
    }

    if (input.bad()) {
        throw std::runtime_error("Error while streaming the service log.");
    }

    std::cout << "Error events found: " << errors << '\n';
}

int main(int argc, char* argv[]) {
    try {
        const fs::path root =
            fs::absolute(argc > 1 ? argv[1] : "inspection_workspace")
                .lexically_normal();

        ensureDirectory(root);
        ensureDirectory(root / "input");
        ensureDirectory(root / "output");

        std::cout << "Workspace: " << root.string() << '\n';

        const fs::path csvPath = safePath(root, "input/assets.csv");

        const std::string sampleCsv =
            "asset_id,department,replacement_cost\r\n"
            "AST-1001,Water Operations,45000.50\r\n"
            "AST-1002,Power Operations,175000.00\r\n"
            "AST-1003,Water Operations,62000.00\r\n"
            "AST-1004,Power Operations,-25.00\r\n"
            "AST-1001,Water Operations,100.00\r\n"
            "AST-1005,Water Operations,12.345\r\n";

        writeAtomically(csvPath, sampleCsv);

        const ImportReport report = importAssets(csvPath);

        std::cout << "\nImport results\n"
                  << "Accepted: " << report.accepted.size() << '\n'
                  << "Rejected: " << report.rejected.size() << '\n';

        for (const auto& [department, summary] : report.departments) {
            std::cout << department
                      << ": count=" << summary.assetCount
                      << ", total=" << moneyString(summary.totalCostPaise)
                      << '\n';
        }

        const fs::path jsonPath =
            safePath(root, "output/asset_report.json");
        const fs::path summaryPath =
            safePath(root, "output/import_audit.txt");

        writeAtomically(jsonPath, makeJsonReport(report));
        writeAtomically(summaryPath, makeTextSummary(report));

        const fs::path logPath = safePath(root, "input/service.log");
        writeAtomically(
            logPath,
            "INFO inspection_started\n"
            "ERROR sensor_timeout\n"
            "INFO retry_started\n"
            "ERROR sensor_unavailable\n"
        );

        demonstrateStreaming(logPath);
        demonstratePathErrors(root);

        // Validate key invariants before reporting success.
        require(
            report.accepted.size() + report.rejected.size() == 5,
            "Import record accounting is inconsistent."
        );

        require(
            fs::file_size(jsonPath) > 0,
            "JSON report was not written."
        );

        std::cout << "\nJSON report: "
                  << jsonPath.lexically_relative(root).string() << '\n'
                  << "Audit text: "
                  << summaryPath.lexically_relative(root).string() << '\n'
                  << "Import invariants passed.\n";

        return 0;
    } catch (const std::exception& error) {
        std::cerr << "File processing failed: " << error.what() << '\n';
        return 1;
    }
}

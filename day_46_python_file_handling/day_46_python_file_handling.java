import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.FileAlreadyExistsException;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.regex.Pattern;
import java.util.stream.Stream;

/*
 * Enterprise asset-file ingestion service.
 *
 * Java 17 or later; standard library only.
 *
 * Compile:
 *   javac FileHandling.java
 *
 * Run:
 *   java FileHandling
 *   java FileHandling ./enterprise_file_workspace
 */
public class FileHandling {

    private static final Pattern ASSET_ID =
            Pattern.compile("AST-[0-9]{4,8}");

    private static final long MAX_REPLACEMENT_COST_PAISE =
            100_000_000_000L;

    private FileHandling() {
    }

    private static void heading(String title) {
        System.out.println("\n" + "=".repeat(68));
        System.out.println(title);
        System.out.println("=".repeat(68));
    }

    private static Path safePath(Path root, String relativeName) {
        Path relative;

        try {
            relative = Path.of(relativeName);
        } catch (InvalidPathException exception) {
            throw new IllegalArgumentException("Invalid file path.", exception);
        }

        if (relative.isAbsolute()) {
            throw new IllegalArgumentException("Absolute paths are not permitted.");
        }

        for (Path component : relative) {
            if (component.toString().equals("..")) {
                throw new IllegalArgumentException(
                        "Parent-directory traversal is not permitted."
                );
            }
        }

        Path resolvedRoot = root.toAbsolutePath().normalize();
        Path target = resolvedRoot.resolve(relative).normalize();

        if (!target.startsWith(resolvedRoot)) {
            throw new IllegalArgumentException(
                    "Resolved path escapes the workspace."
            );
        }

        return target;
    }

    private static void ensureDirectory(Path directory) throws IOException {
        Files.createDirectories(directory);

        if (!Files.isDirectory(directory, LinkOption.NOFOLLOW_LINKS)) {
            throw new IOException("Expected a directory: " + directory);
        }
    }

    private static String readUtf8Strictly(Path path) throws IOException {
        byte[] bytes = Files.readAllBytes(path);

        try {
            return StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes))
                    .toString();
        } catch (CharacterCodingException exception) {
            throw new IOException("File is not valid UTF-8: " + path, exception);
        }
    }

    private static void writeAtomically(Path destination, String content)
            throws IOException {
        ensureDirectory(destination.getParent());

        Path temporary = Files.createTempFile(
                destination.getParent(),
                "." + destination.getFileName() + ".",
                ".tmp"
        );

        boolean published = false;

        try {
            try (BufferedWriter writer = Files.newBufferedWriter(
                    temporary,
                    StandardCharsets.UTF_8,
                    StandardOpenOption.TRUNCATE_EXISTING,
                    StandardOpenOption.WRITE
            )) {
                writer.write(content);
            }

            try {
                Files.move(
                        temporary,
                        destination,
                        StandardCopyOption.ATOMIC_MOVE,
                        StandardCopyOption.REPLACE_EXISTING
                );
                published = true;
            } catch (AtomicMoveNotSupportedException exception) {
                // This fallback remains a replacement operation but does not
                // promise atomic visibility. Production callers should decide
                // whether to fail closed instead on unsupported filesystems.
                Files.move(
                        temporary,
                        destination,
                        StandardCopyOption.REPLACE_EXISTING
                );
                published = true;
            }
        } finally {
            if (!published) {
                Files.deleteIfExists(temporary);
            }
        }
    }

    private record Asset(
            String assetId,
            String department,
            long replacementCostPaise
    ) {
        Asset {
            if (assetId == null || !ASSET_ID.matcher(assetId).matches()) {
                throw new IllegalArgumentException("Invalid asset identifier.");
            }

            if (department == null ||
                    department.isBlank() ||
                    department.length() > 80) {
                throw new IllegalArgumentException("Invalid department.");
            }

            if (replacementCostPaise < 0 ||
                    replacementCostPaise > MAX_REPLACEMENT_COST_PAISE) {
                throw new IllegalArgumentException("Invalid replacement cost.");
            }
        }
    }

    private record RejectedRow(int lineNumber, String reason, String rawRecord) {
    }

    private record DepartmentAggregate(int assetCount, long totalCostPaise) {
        DepartmentAggregate add(long cost) {
            return new DepartmentAggregate(
                    Math.addExact(assetCount, 1),
                    Math.addExact(totalCostPaise, cost)
            );
        }
    }

    private record ImportReport(
            Instant generatedAt,
            List<Asset> accepted,
            List<RejectedRow> rejected,
            Map<String, DepartmentAggregate> departmentTotals
    ) {
        ImportReport {
            accepted = List.copyOf(accepted);
            rejected = List.copyOf(rejected);
            departmentTotals = Map.copyOf(departmentTotals);
        }
    }

    private static List<String> parseCsvRecord(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder field = new StringBuilder();
        boolean inQuotes = false;
        boolean closedQuote = false;

        for (int index = 0; index < line.length(); index++) {
            char character = line.charAt(index);

            if (inQuotes) {
                if (character == '"') {
                    if (index + 1 < line.length() &&
                            line.charAt(index + 1) == '"') {
                        field.append('"');
                        index++;
                    } else {
                        inQuotes = false;
                        closedQuote = true;
                    }
                } else {
                    field.append(character);
                }
                continue;
            }

            if (closedQuote && character != ',') {
                throw new IllegalArgumentException(
                        "Unexpected content after a quoted field."
                );
            }

            if (character == ',') {
                fields.add(field.toString());
                field.setLength(0);
                closedQuote = false;
            } else if (character == '"') {
                if (!field.isEmpty() || closedQuote) {
                    throw new IllegalArgumentException("Unexpected quote.");
                }
                inQuotes = true;
            } else {
                field.append(character);
            }
        }

        if (inQuotes) {
            throw new IllegalArgumentException("Unterminated CSV quote.");
        }

        fields.add(field.toString());
        return fields;
    }

    private static long parseRupeesToPaise(String rawValue) {
        String value = rawValue.strip();

        if (!value.matches("[0-9]+(?:\\.[0-9]{1,2})?")) {
            throw new IllegalArgumentException(
                    "Cost must be a non-negative amount with at most two decimals."
            );
        }

        String[] parts = value.split("\\.", -1);
        long rupees = Long.parseLong(parts[0]);
        String fractional = parts.length == 1 ? "" : parts[1];

        if (fractional.length() == 1) {
            fractional += "0";
        }

        long paise = fractional.isEmpty() ? 0 : Long.parseLong(fractional);
        return Math.addExact(Math.multiplyExact(rupees, 100L), paise);
    }

    private static Asset validateAsset(List<String> fields) {
        if (fields.size() != 3) {
            throw new IllegalArgumentException("Expected three CSV columns.");
        }

        return new Asset(
                fields.get(0).strip(),
                fields.get(1).strip(),
                parseRupeesToPaise(fields.get(2))
        );
    }

    private static ImportReport importCsv(Path csvPath) throws IOException {
        List<String> lines = Files.readAllLines(
                csvPath,
                StandardCharsets.UTF_8
        );

        if (lines.isEmpty()) {
            throw new IOException("The asset CSV is empty.");
        }

        if (!parseCsvRecord(lines.get(0)).equals(
                List.of("asset_id", "department", "replacement_cost"))) {
            throw new IOException("Unexpected CSV header.");
        }

        List<Asset> accepted = new ArrayList<>();
        List<RejectedRow> rejected = new ArrayList<>();
        Map<String, DepartmentAggregate> aggregates = new TreeMap<>();
        Set<String> identifiers = new HashSet<>();

        for (int index = 1; index < lines.size(); index++) {
            String rawRecord = lines.get(index);

            if (rawRecord.isBlank()) {
                continue;
            }

            try {
                Asset asset = validateAsset(parseCsvRecord(rawRecord));

                if (!identifiers.add(asset.assetId())) {
                    throw new IllegalArgumentException(
                            "Duplicate asset identifier."
                    );
                }

                DepartmentAggregate current = aggregates.getOrDefault(
                        asset.department(),
                        new DepartmentAggregate(0, 0)
                );

                aggregates.put(
                        asset.department(),
                        current.add(asset.replacementCostPaise())
                );

                accepted.add(asset);
            } catch (IllegalArgumentException | ArithmeticException exception) {
                rejected.add(new RejectedRow(
                        index + 1,
                        exception.getMessage(),
                        rawRecord
                ));
            }
        }

        return new ImportReport(
                Instant.now(),
                accepted,
                rejected,
                aggregates
        );
    }

    private static String jsonEscape(String value) {
        StringBuilder result = new StringBuilder("\"");

        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);

            switch (character) {
                case '"' -> result.append("\\\"");
                case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b");
                case '\f' -> result.append("\\f");
                case '\n' -> result.append("\\n");
                case '\r' -> result.append("\\r");
                case '\t' -> result.append("\\t");
                default -> {
                    if (character < 0x20) {
                        result.append(String.format("\\u%04x", (int) character));
                    } else {
                        result.append(character);
                    }
                }
            }
        }

        return result.append('"').toString();
    }

    private static String formatMoney(long paise) {
        return (paise / 100) + "." + String.format("%02d", paise % 100);
    }

    private static String toJson(ImportReport report) {
        StringBuilder json = new StringBuilder();

        json.append("{\n")
                .append("  \"generated_at\": ")
                .append(jsonEscape(report.generatedAt().toString()))
                .append(",\n")
                .append("  \"accepted_count\": ")
                .append(report.accepted().size())
                .append(",\n")
                .append("  \"rejected_count\": ")
                .append(report.rejected().size())
                .append(",\n")
                .append("  \"assets\": [");

        for (int index = 0; index < report.accepted().size(); index++) {
            Asset asset = report.accepted().get(index);

            json.append(index == 0 ? "\n" : ",\n")
                    .append("    {\"asset_id\": ")
                    .append(jsonEscape(asset.assetId()))
                    .append(", \"department\": ")
                    .append(jsonEscape(asset.department()))
                    .append(", \"replacement_cost\": ")
                    .append(jsonEscape(formatMoney(asset.replacementCostPaise())))
                    .append("}");
        }

        if (!report.accepted().isEmpty()) {
            json.append('\n');
        }

        json.append("  ],\n")
                .append("  \"rejected_rows\": [");

        for (int index = 0; index < report.rejected().size(); index++) {
            RejectedRow row = report.rejected().get(index);

            json.append(index == 0 ? "\n" : ",\n")
                    .append("    {\"line\": ")
                    .append(row.lineNumber())
                    .append(", \"reason\": ")
                    .append(jsonEscape(row.reason()))
                    .append(", \"record\": ")
                    .append(jsonEscape(row.rawRecord()))
                    .append("}");
        }

        if (!report.rejected().isEmpty()) {
            json.append('\n');
        }

        json.append("  ]\n}\n");
        return json.toString();
    }

    private static String toTextAudit(ImportReport report) {
        StringBuilder text = new StringBuilder();

        text.append("Asset import audit\n")
                .append("Generated at: ").append(report.generatedAt()).append('\n')
                .append("Accepted: ").append(report.accepted().size()).append('\n')
                .append("Rejected: ").append(report.rejected().size()).append('\n');

        report.departmentTotals().forEach((department, aggregate) ->
                text.append(department)
                        .append(" | count=").append(aggregate.assetCount())
                        .append(" | total=")
                        .append(formatMoney(aggregate.totalCostPaise()))
                        .append('\n')
        );

        for (RejectedRow row : report.rejected()) {
            text.append("Rejected line ")
                    .append(row.lineNumber())
                    .append(": ")
                    .append(row.reason())
                    .append('\n');
        }

        return text.toString();
    }

    private static void demonstratePaths(Path root) {
        heading("Path validation");

        for (String candidate : List.of(
                "input/assets.csv",
                "../outside.csv",
                root.resolve("outside.csv").toString()
        )) {
            try {
                System.out.println(safePath(root, candidate));
            } catch (IllegalArgumentException exception) {
                System.out.println(
                        "Rejected " + candidate + ": " + exception.getMessage()
                );
            }
        }
    }

    private static void demonstrateBinaryFile(Path root) throws IOException {
        heading("Binary data and strict text decoding");

        Path binary = safePath(root, "output/instrument_snapshot.bin");

        Files.write(
                binary,
                new byte[]{0, 1, 127, (byte) 128, (byte) 255},
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING
        );

        System.out.println("Binary bytes: " + Files.size(binary));

        Path malformedUtf8 = safePath(root, "input/invalid_utf8.txt");
        Files.write(
                malformedUtf8,
                new byte[]{(byte) 0xC3, 0x28},
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING
        );

        try {
            readUtf8Strictly(malformedUtf8);
            throw new AssertionError("Malformed UTF-8 was accepted.");
        } catch (IOException exception) {
            System.out.println("Invalid UTF-8 rejected.");
        }
    }

    private static void selfTest(Path root) throws IOException {
        heading("Assertions");

        Asset valid = validateAsset(
                List.of("AST-1001", "Water Operations", "45000.50")
        );

        if (valid.replacementCostPaise() != 4_500_050L) {
            throw new AssertionError("Currency conversion failed.");
        }

        try {
            validateAsset(List.of("AST-1002", "Operations", "-10"));
            throw new AssertionError("Negative cost was accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println("Negative cost rejected.");
        }

        try {
            safePath(root, "../outside.txt");
            throw new AssertionError("Path traversal was accepted.");
        } catch (IllegalArgumentException expected) {
            System.out.println("Path traversal rejected.");
        }

        Path jsonPath = safePath(root, "output/test.json");
        writeAtomically(jsonPath, "{\"status\":\"valid\",\"unicode\":\"café\"}\n");

        if (!readUtf8Strictly(jsonPath).contains("café")) {
            throw new AssertionError("UTF-8 round trip failed.");
        }

        System.out.println("Assertions passed.");
    }

    public static void main(String[] args) {
        try {
            Path root = Path.of(
                    args.length == 0 ? "enterprise_file_workspace" : args[0]
            ).toAbsolutePath().normalize();

            ensureDirectory(root);
            ensureDirectory(safePath(root, "input"));
            ensureDirectory(safePath(root, "output"));

            heading("Enterprise asset-file ingestion");
            System.out.println("Workspace: " + root);

            Path csvPath = safePath(root, "input/assets.csv");

            String csv = """
                    asset_id,department,replacement_cost
                    AST-1001,Water Operations,45000.50
                    AST-1002,Power Operations,175000.00
                    AST-1003,Water Operations,62000.00
                    AST-1004,Power Operations,-25.00
                    AST-1001,Water Operations,100.00
                    """;

            writeAtomically(csvPath, csv);
            ImportReport report = importCsv(csvPath);

            System.out.println("Accepted: " + report.accepted().size());
            System.out.println("Rejected: " + report.rejected().size());

            Path jsonPath = safePath(root, "output/asset_report.json");
            Path auditPath = safePath(root, "output/import_audit.txt");

            writeAtomically(jsonPath, toJson(report));
            writeAtomically(auditPath, toTextAudit(report));

            demonstratePaths(root);
            demonstrateBinaryFile(root);
            selfTest(root);

            heading("Generated files");

            try (Stream<Path> paths = Files.walk(root)) {
                paths.filter(Files::isRegularFile)
                        .sorted(Comparator.comparing(Path::toString))
                        .forEach(file -> {
                            try {
                                System.out.println(
                                        root.relativize(file) +
                                        " (" + Files.size(file) + " bytes)"
                                );
                            } catch (IOException exception) {
                                throw new java.io.UncheckedIOException(exception);
                            }
                        });
            }

        } catch (IOException | IllegalArgumentException exception) {
            System.err.println("File processing failed: " + exception.getMessage());
            System.exit(1);
        }
    }
}

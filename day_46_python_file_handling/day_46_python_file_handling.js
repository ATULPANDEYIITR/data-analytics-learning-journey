"use strict";

/*
 * Node.js file handling with TXT, CSV, JSON, paths, encodings, and atomic writes.
 *
 * Run:
 *   node file_handling.js
 *   node file_handling.js ./file_handling_workspace
 *
 * Uses only Node.js built-in modules.
 */

const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");
const assert = require("node:assert/strict");
const { TextDecoder } = require("node:util");

function heading(title) {
    console.log(`\n${"=".repeat(68)}\n${title}\n${"=".repeat(68)}`);
}

function workspacePath(root, relativeName) {
    if (typeof relativeName !== "string" || relativeName.length === 0) {
        throw new TypeError("A non-empty relative path is required.");
    }

    if (relativeName.includes("\0")) {
        throw new Error("A path cannot contain a null character.");
    }

    // path.resolve normalizes traversal components using the current platform.
    const resolvedRoot = path.resolve(root);
    const resolvedTarget = path.resolve(resolvedRoot, relativeName);
    const relative = path.relative(resolvedRoot, resolvedTarget);

    if (
        path.isAbsolute(relative) ||
        relative === ".." ||
        relative.startsWith(`..${path.sep}`)
    ) {
        throw new Error("Path escapes the workspace.");
    }

    return resolvedTarget;
}

async function ensureDirectory(directory) {
    await fsp.mkdir(directory, { recursive: true });
    const metadata = await fsp.stat(directory);

    if (!metadata.isDirectory()) {
        throw new Error(`Not a directory: ${directory}`);
    }
}

async function readUtf8(filePath) {
    // Buffer.toString replaces malformed UTF-8 sequences. Use TextDecoder
    // with fatal=true when invalid byte sequences must be rejected.
    const bytes = await fsp.readFile(filePath);
    const decoder = new TextDecoder("utf-8", { fatal: true });
    return decoder.decode(bytes);
}

async function writeAtomically(filePath, content) {
    await ensureDirectory(path.dirname(filePath));

    // A unique temporary file in the same directory avoids cross-filesystem
    // rename failures and prevents concurrent writers sharing a temp name.
    const temporaryPath = path.join(
        path.dirname(filePath),
        `.${path.basename(filePath)}.${process.pid}.${Date.now()}.${Math.random()
            .toString(16)
            .slice(2)}.tmp`
    );

    let handle;

    try {
        handle = await fsp.open(temporaryPath, "wx", 0o600);
        await handle.writeFile(content, { encoding: "utf8" });
        await handle.sync();
        await handle.close();
        handle = undefined;

        // On common local filesystems, rename replaces a destination atomically.
        // Replacement and durability guarantees can differ across platforms.
        await fsp.rename(temporaryPath, filePath);
    } catch (error) {
        if (handle) {
            await handle.close().catch(() => {});
        }

        await fsp.unlink(temporaryPath).catch(() => {});
        throw error;
    }
}

function csvEscape(value) {
    const text = String(value ?? "");

    // Quote fields containing delimiters, quote characters, or newlines.
    if (/[",\r\n]/.test(text)) {
        return `"${text.replace(/"/g, '""')}"`;
    }

    return text;
}

function serializeCsv(columns, rows) {
    if (!Array.isArray(columns) || columns.length === 0) {
        throw new TypeError("CSV columns must be a non-empty array.");
    }

    if (
        columns.some((column) => typeof column !== "string" || !column.trim()) ||
        new Set(columns).size !== columns.length
    ) {
        throw new Error("CSV column names must be non-empty and unique.");
    }

    const lines = [columns.map(csvEscape).join(",")];

    for (const row of rows) {
        const unknownColumns = Object.keys(row).filter(
            (key) => !columns.includes(key)
        );

        if (unknownColumns.length > 0) {
            throw new Error(
                `Unexpected CSV columns: ${unknownColumns.join(", ")}`
            );
        }

        lines.push(columns.map((column) => csvEscape(row[column])).join(","));
    }

    return `${lines.join("\r\n")}\r\n`;
}

function parseCsv(text) {
    /*
     * Small state-machine parser supporting quoted fields, escaped quotes,
     * commas, CRLF/LF records, and embedded newlines in quoted fields.
     * This parser intentionally rejects malformed quoting and inconsistent
     * row widths instead of silently shifting column values.
     */
    const rows = [];
    let row = [];
    let field = "";
    let inQuotes = false;
    let afterQuote = false;

    for (let index = 0; index < text.length; index += 1) {
        const character = text[index];

        if (inQuotes) {
            if (character === '"') {
                if (text[index + 1] === '"') {
                    field += '"';
                    index += 1;
                } else {
                    inQuotes = false;
                    afterQuote = true;
                }
            } else {
                field += character;
            }
            continue;
        }

        if (afterQuote && character !== "," && character !== "\r" &&
            character !== "\n") {
            throw new Error(`Unexpected character after quote at offset ${index}.`);
        }

        if (character === '"') {
            if (field.length !== 0 || afterQuote) {
                throw new Error(`Unexpected quote at offset ${index}.`);
            }
            inQuotes = true;
        } else if (character === ",") {
            row.push(field);
            field = "";
            afterQuote = false;
        } else if (character === "\n" || character === "\r") {
            if (character === "\r" && text[index + 1] === "\n") {
                index += 1;
            }

            row.push(field);
            rows.push(row);
            row = [];
            field = "";
            afterQuote = false;
        } else {
            field += character;
        }
    }

    if (inQuotes) {
        throw new Error("CSV ends inside a quoted field.");
    }

    if (field.length > 0 || row.length > 0 || afterQuote) {
        row.push(field);
        rows.push(row);
    }

    // A final line ending is not an additional empty record.
    const normalizedRows = rows.filter(
        (record) => !(record.length === 1 && record[0] === "")
    );

    if (normalizedRows.length === 0) {
        return [];
    }

    const headers = normalizedRows[0];

    if (headers.some((header) => header.trim() === "")) {
        throw new Error("CSV headers cannot be blank.");
    }

    if (new Set(headers).size !== headers.length) {
        throw new Error("CSV headers must be unique.");
    }

    return normalizedRows.slice(1).map((values, rowIndex) => {
        if (values.length !== headers.length) {
            throw new Error(
                `CSV record ${rowIndex + 2} has ${values.length} fields; ` +
                `expected ${headers.length}.`
            );
        }

        return Object.fromEntries(
            headers.map((header, index) => [header, values[index]])
        );
    });
}

function validateAsset(record) {
    const assetId = String(record.asset_id ?? "").trim();
    const department = String(record.department ?? "").trim();
    const replacementCost = Number(record.replacement_cost);

    if (!/^AST-[0-9]{4,8}$/.test(assetId)) {
        throw new Error("asset_id must match AST- followed by 4 to 8 digits.");
    }

    if (!department || department.length > 80) {
        throw new Error("department must contain 1 to 80 characters.");
    }

    if (
        !Number.isFinite(replacementCost) ||
        replacementCost < 0 ||
        replacementCost > 1_000_000_000
    ) {
        throw new Error("replacement_cost must be a valid non-negative amount.");
    }

    return {
        asset_id: assetId,
        department,
        replacement_cost: replacementCost
    };
}

async function processAssets(root) {
    heading("CSV asset processing");

    const source = workspacePath(root, "input/assets.csv");
    const columns = ["asset_id", "department", "replacement_cost"];

    const assets = [
        { asset_id: "AST-1001", department: "Water Operations", replacement_cost: "45000.50" },
        { asset_id: "AST-1002", department: "Power Operations", replacement_cost: "175000" },
        { asset_id: "AST-1003", department: "Water Operations", replacement_cost: "62000" },
        { asset_id: "AST-1004", department: "Power Operations", replacement_cost: "-25" }
    ];

    await writeAtomically(source, serializeCsv(columns, assets));
    const parsedAssets = parseCsv(await readUtf8(source));

    const validAssets = [];
    const rejectedRows = [];
    const seenIds = new Set();

    for (const [index, record] of parsedAssets.entries()) {
        try {
            const asset = validateAsset(record);

            if (seenIds.has(asset.asset_id)) {
                throw new Error("Duplicate asset identifier.");
            }

            seenIds.add(asset.asset_id);
            validAssets.push(asset);
        } catch (error) {
            rejectedRows.push({
                record: index + 2,
                asset_id: record.asset_id,
                reason: error.message
            });
        }
    }

    const departmentTotals = new Map();

    for (const asset of validAssets) {
        const current = departmentTotals.get(asset.department) ?? {
            count: 0,
            replacement_cost: 0
        };

        current.count += 1;
        current.replacement_cost += asset.replacement_cost;
        departmentTotals.set(asset.department, current);
    }

    const report = {
        generated_at: new Date().toISOString(),
        accepted_count: validAssets.length,
        rejected_count: rejectedRows.length,
        assets: validAssets,
        rejected_rows: rejectedRows,
        department_totals: Object.fromEntries(departmentTotals)
    };

    await writeAtomically(
        workspacePath(root, "output/asset_report.json"),
        `${JSON.stringify(report, null, 2)}\n`
    );

    console.log(JSON.stringify(report, null, 2));
    return report;
}

async function demonstrateStreaming(root) {
    heading("Asynchronous streaming and backpressure");

    const source = workspacePath(root, "input/service.log");
    const destination = workspacePath(root, "output/service_errors.txt");

    await writeAtomically(
        source,
        [
            "2026-10-16 INFO inspection_started",
            "2026-10-16 ERROR sensor_timeout",
            "2026-10-16 INFO retry_started",
            "2026-10-16 ERROR sensor_unavailable",
            "2026-10-16 INFO inspection_finished",
            ""
        ].join("\n")
    );

    // Streams process records incrementally. Respecting the writable stream's
    // drain event prevents an unbounded queue when the destination is slower.
    const input = fs.createReadStream(source, {
        encoding: "utf8",
        highWaterMark: 32
    });

    const output = fs.createWriteStream(destination, {
        encoding: "utf8",
        flags: "w",
        mode: 0o600
    });

    let pending = "";
    let errorsFound = 0;

    try {
        for await (const chunk of input) {
            pending += chunk;
            const lines = pending.split(/\r?\n/);
            pending = lines.pop() ?? "";

            for (const line of lines) {
                if (line.includes(" ERROR ")) {
                    errorsFound += 1;

                    if (!output.write(`${line}\n`)) {
                        await new Promise((resolve, reject) => {
                            output.once("drain", resolve);
                            output.once("error", reject);
                        });
                    }
                }
            }
        }

        if (pending.includes(" ERROR ")) {
            errorsFound += 1;
            if (!output.write(`${pending}\n`)) {
                await new Promise((resolve, reject) => {
                    output.once("drain", resolve);
                    output.once("error", reject);
                });
            }
        }

        output.end();
        await new Promise((resolve, reject) => {
            output.once("finish", resolve);
            output.once("error", reject);
        });

        console.log(`Error records extracted: ${errorsFound}`);
        console.log(await readUtf8(destination));
    } catch (error) {
        input.destroy();
        output.destroy();
        throw error;
    }
}

async function demonstrateJson(root) {
    heading("JSON configuration and validation");

    const configPath = workspacePath(root, "input/service_config.json");
    const config = {
        service: "asset-inspection",
        retry_limit: 3,
        enabled: true,
        allowed_departments: ["Water Operations", "Power Operations"],
        thresholds: {
            warning_temperature_c: 65,
            critical_temperature_c: 85
        }
    };

    if (
        !Number.isInteger(config.retry_limit) ||
        config.retry_limit < 0 ||
        config.retry_limit > 10
    ) {
        throw new Error("retry_limit is outside the permitted range.");
    }

    await writeAtomically(configPath, `${JSON.stringify(config, null, 2)}\n`);

    const loaded = JSON.parse(await readUtf8(configPath));

    if (loaded.thresholds.warning_temperature_c >=
        loaded.thresholds.critical_temperature_c) {
        throw new Error("Warning threshold must be below critical threshold.");
    }

    console.log(`Service configuration loaded: ${loaded.service}`);

    const malformedPath = workspacePath(root, "input/broken.json");
    await writeAtomically(malformedPath, '{"retry_limit": 3,}');

    try {
        JSON.parse(await readUtf8(malformedPath));
    } catch (error) {
        console.log(`Malformed JSON rejected: ${error.message}`);
    }
}

async function demonstrateTextAndBinary(root) {
    heading("Text encodings, append mode, and binary files");

    const notesPath = workspacePath(root, "output/inspection_notes.txt");
    await writeAtomically(
        notesPath,
        "Inspection completed.\nTechnician: José Kumar.\n"
    );

    const notes = await readUtf8(notesPath);
    console.log(notes);

    await fsp.appendFile(
        notesPath,
        "Follow-up required for sensor calibration.\n",
        { encoding: "utf8", flag: "a" }
    );

    const binaryPath = workspacePath(root, "output/instrument_snapshot.bin");
    await fsp.writeFile(binaryPath, Buffer.from([0, 1, 127, 128, 255]));
    const bytes = await fsp.readFile(binaryPath);
    console.log(`Binary byte count: ${bytes.length}`);
    console.log(`Binary contents: ${Array.from(bytes).join(", ")}`);

    // Buffer data is not automatically valid UTF-8. Fatal decoding avoids
    // silently accepting corrupted text when integrity is important.
    try {
        new TextDecoder("utf-8", { fatal: true }).decode(
            Buffer.from([0xc3, 0x28])
        );
    } catch (error) {
        console.log(`Invalid UTF-8 detected: ${error.name}`);
    }
}

async function demonstratePathValidation(root) {
    heading("Path validation");

    for (const candidate of [
        "output/report.json",
        "../outside.txt",
        path.resolve(os.tmpdir(), "outside.txt")
    ]) {
        try {
            console.log(workspacePath(root, candidate));
        } catch (error) {
            console.log(`Rejected ${candidate}: ${error.message}`);
        }
    }
}

async function selfTest(root) {
    heading("Assertions");

    const serialized = serializeCsv(
        ["asset_id", "description"],
        [
            { asset_id: "AST-1001", description: 'Pump, "north wing"\nchecked' }
        ]
    );

    const parsed = parseCsv(serialized);
    assert.equal(parsed[0].description, 'Pump, "north wing"\nchecked');

    assert.throws(
        () => validateAsset({
            asset_id: "AST-1001",
            department: "Operations",
            replacement_cost: "-1"
        }),
        /non-negative/
    );

    assert.throws(() => workspacePath(root, "../outside.txt"), /escapes/);

    console.log("All assertions passed.");
}

async function main() {
    const root = path.resolve(
        process.argv[2] ?? "./file_handling_workspace"
    );

    await ensureDirectory(root);
    await ensureDirectory(workspacePath(root, "input"));
    await ensureDirectory(workspacePath(root, "output"));

    console.log(`Workspace: ${root}`);

    await processAssets(root);
    await demonstrateStreaming(root);
    await demonstrateJson(root);
    await demonstrateTextAndBinary(root);
    await demonstratePathValidation(root);
    await selfTest(root);

    heading("Workspace files");
    async function listFiles(directory) {
        const entries = await fsp.readdir(directory, { withFileTypes: true });

        for (const entry of entries) {
            const fullPath = path.join(directory, entry.name);

            if (entry.isDirectory()) {
                await listFiles(fullPath);
            } else {
                const metadata = await fsp.stat(fullPath);
                console.log(
                    `${path.relative(root, fullPath)} (${metadata.size} bytes)`
                );
            }
        }
    }

    await listFiles(root);
}

main().catch((error) => {
    console.error(`File handling failed: ${error.message}`);
    process.exitCode = 1;
});

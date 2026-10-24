"use strict";

/*
 * Pandas-style combining concepts implemented with native JavaScript
 * data structures:
 *   - merge: relational key-based combination
 *   - join: index/key-oriented combination
 *   - concat: row and column concatenation
 *   - append alternative: concat
 *   - relational operations: matched/unmatched records and aggregation
 *
 * The implementation intentionally uses Maps and Sets to make key
 * relationships explicit rather than relying on external packages.
 */

class ValidationError extends Error {}

function cloneRecord(record) {
    return { ...record };
}

function requireFields(record, fields, recordName) {
    for (const field of fields) {
        if (!(field in record)) {
            throw new ValidationError(
                `${recordName} is missing required field '${field}'.`
            );
        }
    }
}

function groupBy(records, key) {
    const groups = new Map();

    for (const record of records) {
        requireFields(record, [key], "record");

        const value = record[key];
        if (!groups.has(value)) {
            groups.set(value, []);
        }

        groups.get(value).push(record);
    }

    return groups;
}

function merge(left, right, options = {}) {
    const {
        on,
        how = "inner",
        suffixes = ["_left", "_right"],
        validate = null,
    } = options;

    if (!["inner", "left", "right", "outer"].includes(how)) {
        throw new ValidationError(`Unsupported merge mode: ${how}`);
    }

    if (!on) {
        throw new ValidationError("A merge key is required.");
    }

    const leftGroups = groupBy(left, on);
    const rightGroups = groupBy(right, on);

    if (validate === "one_to_one") {
        for (const [key, rows] of leftGroups) {
            if (rows.length > 1 && rightGroups.has(key)) {
                throw new ValidationError(
                    `Key '${key}' violates one-to-one validation.`
                );
            }
        }

        for (const [key, rows] of rightGroups) {
            if (rows.length > 1 && leftGroups.has(key)) {
                throw new ValidationError(
                    `Key '${key}' violates one-to-one validation.`
                );
            }
        }
    }

    if (validate === "one_to_many") {
        for (const [key, rows] of leftGroups) {
            if (rows.length > 1) {
                throw new ValidationError(
                    `Left key '${key}' violates one-to-many validation.`
                );
            }
        }
    }

    const leftColumns = new Set(left.flatMap((row) => Object.keys(row)));
    const rightColumns = new Set(right.flatMap((row) => Object.keys(row)));

    const overlapping = [...leftColumns].filter(
        (column) => column !== on && rightColumns.has(column)
    );

    function combine(leftRow, rightRow) {
        const result = {};

        if (leftRow) {
            for (const [key, value] of Object.entries(leftRow)) {
                if (key === on || !overlapping.includes(key)) {
                    result[key] = value;
                } else {
                    result[`${key}${suffixes[0]}`] = value;
                }
            }
        }

        if (rightRow) {
            for (const [key, value] of Object.entries(rightRow)) {
                if (key === on) {
                    if (!(key in result)) {
                        result[key] = value;
                    }
                } else if (overlapping.includes(key)) {
                    result[`${key}${suffixes[1]}`] = value;
                } else {
                    result[key] = value;
                }
            }
        }

        return result;
    }

    const output = [];
    const usedRightKeys = new Set();

    for (const leftRow of left) {
        const key = leftRow[on];
        const matches = rightGroups.get(key) || [];

        if (matches.length > 0) {
            for (const rightRow of matches) {
                output.push(combine(leftRow, rightRow));
            }
            usedRightKeys.add(key);
        } else if (how === "left" || how === "outer") {
            output.push(combine(leftRow, null));
        }
    }

    if (how === "right" || how === "outer") {
        for (const rightRow of right) {
            const key = rightRow[on];
            if (!leftGroups.has(key)) {
                output.push(combine(null, rightRow));
            }
        }
    }

    return output;
}

function join(left, right, key, how = "left") {
    return merge(left, right, {
        on: key,
        how,
        validate: "one_to_one",
    });
}

function concatRows(frames, options = {}) {
    const {
        ignoreIndex = true,
        verifyIntegrity = false,
    } = options;

    if (!Array.isArray(frames) || frames.length === 0) {
        throw new ValidationError("concat requires at least one data set.");
    }

    const result = [];
    const seenIds = new Set();

    for (const frame of frames) {
        for (const row of frame) {
            const copied = cloneRecord(row);

            if (verifyIntegrity && "order_id" in copied) {
                if (seenIds.has(copied.order_id)) {
                    throw new ValidationError(
                        `Duplicate order_id detected: ${copied.order_id}`
                    );
                }
                seenIds.add(copied.order_id);
            }

            if (!ignoreIndex && "_index" in copied) {
                copied._index = result.length;
            }

            result.push(copied);
        }
    }

    return result;
}

function concatColumns(left, right) {
    if (left.length !== right.length) {
        throw new ValidationError(
            "Column-wise concatenation requires aligned row counts."
        );
    }

    return left.map((row, index) => ({
        ...cloneRecord(row),
        ...cloneRecord(right[index]),
    }));
}

function aggregateByCustomer(orders) {
    const totals = new Map();

    for (const order of orders) {
        const current = totals.get(order.customer_id) || 0;
        totals.set(order.customer_id, current + order.amount);
    }

    return [...totals.entries()].map(([customer_id, total]) => ({
        customer_id,
        total_order_amount: total,
        segment: total >= 1500 ? "high" : "standard",
    }));
}

function relationalDifference(left, right, key) {
    const rightKeys = new Set(right.map((row) => row[key]));
    return left.filter((row) => !rightKeys.has(row[key]));
}

function print(title, rows) {
    console.log(`\n=== ${title} ===`);
    console.table(rows);
}

function main() {
    const customers = [
        { customer_id: 1, customer_name: "Atul", region: "North" },
        { customer_id: 2, customer_name: "Priya", region: "South" },
        { customer_id: 3, customer_name: "Rahul", region: "North" },
        { customer_id: 4, customer_name: "Neha", region: "West" },
    ];

    const orders = [
        { order_id: 101, customer_id: 1, amount: 1200, status: "paid" },
        { order_id: 102, customer_id: 2, amount: 850, status: "paid" },
        { order_id: 103, customer_id: 2, amount: 450, status: "pending" },
        { order_id: 104, customer_id: 5, amount: 700, status: "paid" },
        { order_id: 105, customer_id: 3, amount: 1500, status: "paid" },
    ];

    const contacts = [
        { customer_id: 1, email: "atul@example.com" },
        { customer_id: 2, email: "priya@example.com" },
        { customer_id: 3, email: "rahul@example.com" },
        { customer_id: 4, email: "neha@example.com" },
    ];

    const january = [
        { order_id: 101, month: "2026-01", amount: 1200 },
        { order_id: 102, month: "2026-01", amount: 850 },
    ];

    const february = [
        { order_id: 103, month: "2026-02", amount: 450 },
        { order_id: 104, month: "2026-02", amount: 700 },
        { order_id: 105, month: "2026-02", amount: 1500 },
    ];

    print(
        "merge: customers to orders",
        merge(customers, orders, {
            on: "customer_id",
            how: "left",
            validate: "one_to_many",
        })
    );

    print(
        "join: customer contacts",
        join(customers, contacts, "customer_id")
    );

    print(
        "concat: monthly order data",
        concatRows([january, february], {
            verifyIntegrity: true,
        })
    );

    // DataFrame.append() has no modern equivalent as a dedicated method.
    // Concatenation is the appropriate row-addition operation.
    print(
        "append alternative",
        concatRows([
            [{ order_id: 100, month: "2025-12", amount: 975 }],
            january,
        ])
    );

    print(
        "column concatenation",
        concatColumns(
            [{ customer_id: 1 }, { customer_id: 2 }],
            [{ region: "North" }, { region: "South" }]
        )
    );

    print(
        "unmatched customers",
        relationalDifference(customers, orders, "customer_id")
    );

    print(
        "unmatched orders",
        relationalDifference(orders, customers, "customer_id")
    );

    const matchedOrders = merge(customers, orders, {
        on: "customer_id",
        how: "inner",
        validate: "one_to_many",
    });

    print("customer totals", aggregateByCustomer(matchedOrders));

    try {
        const duplicateContacts = [
            ...contacts,
            { customer_id: 1, email: "duplicate@example.com" },
        ];

        join(customers, duplicateContacts, "customer_id");
    } catch (error) {
        if (error instanceof ValidationError) {
            console.log(`\nExpected validation failure: ${error.message}`);
        } else {
            throw error;
        }
    }

    const combined = merge(customers, orders, {
        on: "customer_id",
        how: "left",
        validate: "one_to_many",
    });

    if (combined.length !== 6) {
        throw new Error("Unexpected left-merge result size.");
    }

    console.log("\nAll JavaScript validation checks passed.");
}

main();

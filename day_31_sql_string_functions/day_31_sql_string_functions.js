"use strict";

/*
 * SQL String Functions
 *
 * This Node.js program models a small customer-data pipeline and provides
 * JavaScript equivalents of SQL-oriented string operations. It deliberately
 * uses JavaScript's own mechanisms to expose the relationship between
 * database expressions and application-side text processing.
 *
 * No external packages are required.
 */

const customers = [
  {
    id: 1,
    firstName: "  Atul  ",
    lastName: "Pandey",
    email: "ATUL.PANDEY@EXAMPLE.COM",
    phone: "+91-98765-43210",
    city: "Lucknow",
  },
  {
    id: 2,
    firstName: "Priya",
    lastName: "Sharma",
    email: " priya.sharma@example.com ",
    phone: "+91-91234-56789",
    city: "Delhi",
  },
  {
    id: 3,
    firstName: "Rohan",
    lastName: "Mehta",
    email: "ROHAN.MEHTA@EXAMPLE.COM",
    phone: "+91-99887-77665",
    city: "Mumbai",
  },
  {
    id: 4,
    firstName: "Neha",
    lastName: "Verma",
    email: "neha.verma@example.com",
    phone: "+91-90000-11122",
    city: "Bengaluru",
  },
];

const tickets = [
  {
    id: 1001,
    customerId: 1,
    subject: "Password Reset",
    message: "Customer requested a password reset for the account.",
  },
  {
    id: 1002,
    customerId: 2,
    subject: "Payment Failed",
    message: "Payment failed while processing order ORD-2026-1042.",
  },
  {
    id: 1003,
    customerId: 3,
    subject: "Address Change",
    message: "Customer wants to change the registered delivery address.",
  },
  {
    id: 1004,
    customerId: 4,
    subject: "Email Verification",
    message: "Verification link was sent but customer reports an error.",
  },
];

function sqlConcat(...values) {
  /*
   * SQL CONCAT semantics vary between database engines, especially around
   * NULL. This function explicitly rejects nullish values instead of silently
   * producing an ambiguous result.
   */
  if (values.some((value) => value === null || value === undefined)) {
    throw new TypeError("sqlConcat received a NULL-like value");
  }

  return values.map(String).join("");
}

function sqlSubstring(value, startPosition, length) {
  /*
   * SQL SUBSTRING positions are commonly one-based. JavaScript slice() is
   * zero-based, so the conversion is explicit instead of relying on
   * JavaScript's native indexing convention.
   */
  if (typeof value !== "string") {
    throw new TypeError("SUBSTRING requires a string");
  }

  if (!Number.isInteger(startPosition) || startPosition < 1) {
    throw new RangeError("SQL substring positions must start at 1 or greater");
  }

  if (length !== undefined && (!Number.isInteger(length) || length < 0)) {
    throw new RangeError("Substring length must be a non-negative integer");
  }

  const startIndex = startPosition - 1;

  if (length === undefined) {
    return value.slice(startIndex);
  }

  return value.slice(startIndex, startIndex + length);
}

function sqlPosition(needle, haystack) {
  /*
   * SQL POSITION returns a one-based position and usually returns zero when
   * the searched text is absent. JavaScript indexOf() returns -1, so the
   * conversion below models the SQL-style result.
   */
  if (typeof needle !== "string" || typeof haystack !== "string") {
    throw new TypeError("POSITION requires string arguments");
  }

  const zeroBasedPosition = haystack.indexOf(needle);
  return zeroBasedPosition === -1 ? 0 : zeroBasedPosition + 1;
}

function sqlReplace(value, search, replacement) {
  /*
   * String.prototype.replace() replaces only the first literal occurrence
   * when given a string. SQL REPLACE replaces every occurrence, so split()
   * and join() are used to model the SQL behavior safely for literal text.
   */
  if (![value, search, replacement].every((item) => typeof item === "string")) {
    throw new TypeError("REPLACE requires string arguments");
  }

  if (search === "") {
    return value;
  }

  return value.split(search).join(replacement);
}

function sqlLower(value) {
  if (typeof value !== "string") {
    throw new TypeError("LOWER requires a string");
  }

  return value.toLowerCase();
}

function sqlUpper(value) {
  if (typeof value !== "string") {
    throw new TypeError("UPPER requires a string");
  }

  return value.toUpperCase();
}

function sqlTrim(value) {
  if (typeof value !== "string") {
    throw new TypeError("TRIM requires a string");
  }

  return value.trim();
}

function regexp(value, pattern, flags = "") {
  if (typeof value !== "string") {
    throw new TypeError("REGEXP requires a string value");
  }

  const expression = new RegExp(pattern, flags);
  return expression.test(value);
}

function regexpReplace(value, pattern, replacement, flags = "g") {
  if (typeof value !== "string") {
    throw new TypeError("REGEXP_REPLACE requires a string value");
  }

  const expression = new RegExp(pattern, flags);
  return value.replace(expression, replacement);
}

function normalizeEmail(email) {
  return sqlLower(sqlTrim(email));
}

function normalizePhone(phone) {
  /*
   * A regex removes every non-digit character. This is more general than
   * replacing a single known separator such as '-'.
   */
  return regexpReplace(phone, "[^0-9]", "");
}

function formatCustomerName(customer) {
  const firstName = sqlTrim(customer.firstName);
  const lastName = sqlTrim(customer.lastName);

  return sqlConcat(firstName, " ", lastName);
}

function buildCustomerContact(customer) {
  return sqlConcat(
    formatCustomerName(customer),
    " <",
    normalizeEmail(customer.email),
    ">"
  );
}

function extractEmailDomain(email) {
  const atPosition = sqlPosition("@", email);

  if (atPosition === 0) {
    return null;
  }

  /*
   * POSITION returns one-based coordinates. SUBSTRING accepts the same
   * conceptual indexing here, so the character after '@' is at atPosition+1.
   */
  return sqlSubstring(email, atPosition + 1);
}

function findOrderCode(message) {
  const match = message.match(/\bORD-[0-9]{4}-[0-9]{4}\b/);
  return match ? match[0] : null;
}

function classifyTicket(ticket) {
  const searchableText = sqlLower(
    sqlConcat(ticket.subject, " ", ticket.message)
  );

  if (regexp(searchableText, "password|credential")) {
    return "account-security";
  }

  if (regexp(searchableText, "payment|order")) {
    return "billing";
  }

  if (regexp(searchableText, "address|delivery")) {
    return "customer-profile";
  }

  if (regexp(searchableText, "verification|email")) {
    return "email";
  }

  return "general";
}

function displayCustomerTransformations() {
  console.log("\n=== Customer string transformations ===");

  for (const customer of customers) {
    const name = formatCustomerName(customer);
    const email = normalizeEmail(customer.email);
    const phone = normalizePhone(customer.phone);
    const domain = extractEmailDomain(email);

    console.log({
      id: customer.id,
      name,
      email,
      phone,
      emailDomain: domain,
    });
  }
}

function demonstrateSubstringAndPosition() {
  console.log("\n=== SUBSTRING and POSITION behavior ===");

  for (const ticket of tickets) {
    const preview = sqlSubstring(ticket.message, 1, 32);
    const passwordPosition = sqlPosition(
      "password",
      sqlLower(ticket.message)
    );

    console.log({
      ticketId: ticket.id,
      preview,
      passwordPosition,
    });
  }
}

function demonstrateLiteralReplace() {
  console.log("\n=== REPLACE behavior ===");

  const source = "ORD-2026-1042 / ORD-2026-1042";
  const result = sqlReplace(source, "ORD-", "ORDER-");

  console.log({ source, result });
}

function demonstrateRegexValidation() {
  console.log("\n=== REGEXP validation ===");

  const emailPattern = "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$";

  for (const customer of customers) {
    const canonicalEmail = normalizeEmail(customer.email);

    console.log({
      email: canonicalEmail,
      validShape: regexp(canonicalEmail, emailPattern),
    });
  }
}

function demonstrateTicketClassification() {
  console.log("\n=== Event-driven ticket classification ===");

  /*
   * JavaScript callbacks make a useful model for application processing:
   * each incoming ticket is transformed, classified, and emitted to the
   * next stage without mixing the transformation rules together.
   */
  const classified = tickets.map((ticket) => ({
    ...ticket,
    category: classifyTicket(ticket),
    orderCode: findOrderCode(ticket.message),
  }));

  console.table(classified);
}

function demonstrateComposition() {
  console.log("\n=== Composed string operations ===");

  const records = customers.map((customer) => {
    const cleanedName = formatCustomerName(customer);
    const canonicalEmail = normalizeEmail(customer.email);

    return {
      customerId: customer.id,
      contactLabel: buildCustomerContact(customer),
      searchKey: sqlConcat(
        sqlLower(cleanedName.replace(/\s+/g, "")),
        ":",
        canonicalEmail
      ),
    };
  });

  console.table(records);
}

function demonstrateFailureConditions() {
  console.log("\n=== Validation and failure conditions ===");

  const failures = [
    () => sqlSubstring("database", 0, 3),
    () => sqlPosition("@", null),
    () => sqlReplace("abc", "a", null),
    () => regexp("customer@example.com", "["),
  ];

  for (const operation of failures) {
    try {
      operation();
    } catch (error) {
      console.log(`${error.constructor.name}: ${error.message}`);
    }
  }
}

function demonstrateRegexReplacement() {
  console.log("\n=== REGEXP_REPLACE behavior ===");

  for (const ticket of tickets) {
    const redacted = regexpReplace(
      ticket.message,
      "\\bORD-[0-9]{4}-[0-9]{4}\\b",
      "[ORDER-ID]"
    );

    console.log({
      ticketId: ticket.id,
      original: ticket.message,
      redacted,
    });
  }
}

async function simulateIncomingTicket() {
  console.log("\n=== Asynchronous ticket-processing workflow ===");

  const incomingTicket = {
    id: 1005,
    customerId: 1,
    subject: "Payment Failed",
    message: "Payment failed for order ORD-2026-2048.",
  };

  /*
   * Promise-based processing is intentionally asynchronous to model how a
   * Node.js service might receive text from an HTTP request or message queue.
   * The string functions themselves remain synchronous and deterministic.
   */
  const result = await Promise.resolve(incomingTicket).then((ticket) => ({
    ...ticket,
    normalizedSubject: sqlTrim(sqlLower(ticket.subject)),
    category: classifyTicket(ticket),
    orderCode: findOrderCode(ticket.message),
  }));

  console.log(result);
}

function performanceConsiderations() {
  console.log("\n=== Performance considerations ===");

  const largeText = "payment failure ".repeat(10000);

  const start = process.hrtime.bigint();
  const found = regexp(largeText, "payment\\s+failure");
  const elapsedNanoseconds = process.hrtime.bigint() - start;

  console.log({
    regexMatched: found,
    elapsedMicroseconds: Number(elapsedNanoseconds) / 1000,
  });

  console.log(
    "For database-scale filtering, prefer indexed normalized columns or " +
      "database-supported expression indexes when appropriate."
  );
}

async function main() {
  console.log("SQL STRING FUNCTIONS IN A CUSTOMER-DATA WORKFLOW");

  displayCustomerTransformations();
  demonstrateSubstringAndPosition();
  demonstrateLiteralReplace();
  demonstrateRegexValidation();
  demonstrateTicketClassification();
  demonstrateComposition();
  demonstrateFailureConditions();
  demonstrateRegexReplacement();
  performanceConsiderations();
  await simulateIncomingTicket();
}

main().catch((error) => {
  console.error("Processing failed:", error);
  process.exitCode = 1;
});

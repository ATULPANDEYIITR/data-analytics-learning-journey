"use strict";

/*
 * JavaScript Control Flow
 *
 * The program models a repository event processor. JavaScript-specific
 * behavior is emphasized through array iteration, event-driven callbacks,
 * asynchronous status checks, short-circuit decisions, and explicit loop
 * control.
 */

const section = (title) => {
    console.log(`\n${"=".repeat(72)}\n${title}\n${"=".repeat(72)}`);
};

function decisionExample() {
    section("if / else if / else");

    const changedFiles = 6;
    const checksPassed = true;
    const approvals = 2;

    let result;

    if (changedFiles === 0) {
        result = "blocked: no changes";
    } else if (!checksPassed) {
        result = "blocked: status checks failed";
    } else if (approvals < 2) {
        result = "blocked: approval requirement not satisfied";
    } else {
        result = "eligible for merge";
    }

    console.log(result);
}

function arrayIteration() {
    section("for...of and continue");

    const files = [
        "src/payment.js",
        "src/refund.js",
        "tests/payment.test.js",
        "README.md"
    ];

    for (const file of files) {
        if (file.startsWith("tests/")) {
            console.log(`test file: ${file}`);
            continue;
        }

        if (file.endsWith(".js")) {
            console.log(`source file: ${file}`);
        } else {
            console.log(`non-JavaScript file: ${file}`);
        }
    }
}

function breakExample() {
    section("break");

    const checks = [
        { name: "unit", passed: true },
        { name: "lint", passed: true },
        { name: "security", passed: false },
        { name: "integration", passed: true }
    ];

    for (const check of checks) {
        if (!check.passed) {
            console.log(`Blocking check: ${check.name}`);
            break;
        }

        console.log(`Passed check: ${check.name}`);
    }
}

function whileExample() {
    section("while");

    let attempts = 0;
    let connected = false;

    while (attempts < 4 && !connected) {
        attempts += 1;
        console.log(`Connection attempt ${attempts}`);

        if (attempts === 3) {
            connected = true;
        }
    }

    console.log(connected ? "Connected" : "Connection failed");
}

function passEquivalent() {
    section("Intentional no-operation in JavaScript");

    const events = [
        { type: "documentation", actionRequired: false },
        { type: "review", actionRequired: true },
        { type: "status", actionRequired: true }
    ];

    for (const event of events) {
        if (!event.actionRequired) {
            // JavaScript has no pass keyword. An empty block is the closest
            // language-level equivalent when intentionally doing nothing.
            continue;
        }

        console.log(`Processing ${event.type}`);
    }
}

function controlFlowWithArrayMethods() {
    section("JavaScript-specific collection control flow");

    const pullRequests = [
        { number: 301, draft: false, approvals: 2 },
        { number: 302, draft: true, approvals: 3 },
        { number: 303, draft: false, approvals: 1 }
    ];

    // every() expresses a universal condition without manually managing
    // a boolean flag. Some() stops once a matching condition is found.
    for (const pr of pullRequests) {
        if (pr.draft) {
            console.log(`PR #${pr.number}: draft`);
            continue;
        }

        const reviewersSatisfied = pr.approvals >= 2;

        if (reviewersSatisfied) {
            console.log(`PR #${pr.number}: review requirement satisfied`);
        } else {
            console.log(`PR #${pr.number}: review requirement missing`);
        }
    }

    const allReady = pullRequests
        .filter((pr) => !pr.draft)
        .every((pr) => pr.approvals >= 2);

    const hasDraft = pullRequests.some((pr) => pr.draft);

    console.log({ allReady, hasDraft });
}

async function asynchronousControlFlow() {
    section("Asynchronous control flow");

    const checks = [
        { name: "unit", delay: 40, passed: true },
        { name: "lint", delay: 20, passed: true },
        { name: "security", delay: 30, passed: false }
    ];

    async function executeCheck(check) {
        await new Promise((resolve) => setTimeout(resolve, check.delay));

        if (!check.passed) {
            throw new Error(`${check.name} check failed`);
        }

        return `${check.name} passed`;
    }

    for (const check of checks) {
        try {
            const message = await executeCheck(check);
            console.log(message);
        } catch (error) {
            console.log(`Stopping check pipeline: ${error.message}`);
            break;
        }
    }
}

function eventDrivenExample() {
    section("Event-driven control flow");

    class RepositoryEvents {
        constructor() {
            this.handlers = new Map();
        }

        on(eventName, handler) {
            if (!this.handlers.has(eventName)) {
                this.handlers.set(eventName, []);
            }

            this.handlers.get(eventName).push(handler);
        }

        emit(eventName, payload) {
            const handlers = this.handlers.get(eventName) ?? [];

            for (const handler of handlers) {
                handler(payload);
            }
        }
    }

    const events = new RepositoryEvents();

    events.on("pull_request", (pr) => {
        if (pr.draft) {
            console.log(`PR #${pr.number} remains outside final validation`);
            return;
        }

        if (pr.conflicts) {
            console.log(`PR #${pr.number} requires conflict resolution`);
            return;
        }

        console.log(`PR #${pr.number} can proceed to policy evaluation`);
    });

    events.emit("pull_request", {
        number: 401,
        draft: false,
        conflicts: false
    });

    events.emit("pull_request", {
        number: 402,
        draft: true,
        conflicts: false
    });

    events.emit("pull_request", {
        number: 403,
        draft: false,
        conflicts: true
    });
}

function validatePullRequest(pr) {
    if (!Number.isInteger(pr.number) || pr.number <= 0) {
        throw new TypeError("pull request number must be a positive integer");
    }

    if (typeof pr.source !== "string" || typeof pr.target !== "string") {
        throw new TypeError("source and target branches must be strings");
    }

    if (pr.source === pr.target) {
        return { eligible: false, reason: "source and target are identical" };
    }

    if (pr.draft) {
        return { eligible: false, reason: "pull request is a draft" };
    }

    if (pr.conflicts) {
        return { eligible: false, reason: "merge conflicts exist" };
    }

    if (!pr.checks.every((check) => check.passed)) {
        return { eligible: false, reason: "a required check failed" };
    }

    if (pr.approvals < pr.requiredApprovals) {
        return { eligible: false, reason: "insufficient approvals" };
    }

    return { eligible: true, reason: "all merge conditions passed" };
}

function policyEngine() {
    section("Integrated policy engine");

    const requests = [
        {
            number: 501,
            source: "feature/search",
            target: "main",
            draft: false,
            conflicts: false,
            approvals: 2,
            requiredApprovals: 2,
            checks: [
                { name: "unit", passed: true },
                { name: "lint", passed: true }
            ]
        },
        {
            number: 502,
            source: "feature/payments",
            target: "main",
            draft: false,
            conflicts: false,
            approvals: 3,
            requiredApprovals: 2,
            checks: [
                { name: "unit", passed: true },
                { name: "security", passed: false }
            ]
        },
        {
            number: 503,
            source: "feature/docs",
            target: "main",
            draft: true,
            conflicts: false,
            approvals: 3,
            requiredApprovals: 2,
            checks: [
                { name: "unit", passed: true }
            ]
        }
    ];

    for (const pr of requests) {
        try {
            const decision = validatePullRequest(pr);
            console.log(
                `PR #${pr.number}: ${decision.eligible ? "ELIGIBLE" : "BLOCKED"} - ${decision.reason}`
            );
        } catch (error) {
            console.error(`PR #${pr.number}: invalid input - ${error.message}`);
        }
    }
}

async function main() {
    decisionExample();
    arrayIteration();
    breakExample();
    whileExample();
    passEquivalent();
    controlFlowWithArrayMethods();
    eventDrivenExample();
    policyEngine();
    await asynchronousControlFlow();
}

main().catch((error) => {
    console.error(`Fatal error: ${error.message}`);
    process.exitCode = 1;
});

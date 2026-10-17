"use strict";

/*
 * Event-driven error handling for repository governance.
 * Run with Node.js 18 or later. No external packages are required.
 */

const { EventEmitter } = require("node:events");
const fs = require("node:fs/promises");
const path = require("node:path");
const os = require("node:os");

class GovernanceError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = new.target.name;
  }
}

class ValidationError extends GovernanceError {}
class InvalidTransitionError extends GovernanceError {}
class ReviewPolicyError extends GovernanceError {}
class MergeBlockedError extends GovernanceError {}
class PersistenceError extends GovernanceError {}
class TemporaryServiceError extends GovernanceError {}

const PullRequestState = Object.freeze({
  DRAFT: "draft",
  OPEN: "open",
  MERGED: "merged",
  CLOSED: "closed",
});

const ReviewState = Object.freeze({
  COMMENTED: "commented",
  APPROVED: "approved",
  CHANGES_REQUESTED: "changes_requested",
});

function requireNonEmptyString(value, field) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new ValidationError(`${field} must be a non-empty string.`);
  }
  return value.trim();
}

function validatePullRequestInput(input) {
  if (!Number.isSafeInteger(input.number) || input.number <= 0) {
    throw new ValidationError("Pull request number must be a positive safe integer.");
  }

  const title = requireNonEmptyString(input.title, "Title");
  const author = requireNonEmptyString(input.author, "Author");
  const sourceBranch = requireNonEmptyString(input.sourceBranch, "Source branch");
  const targetBranch = requireNonEmptyString(input.targetBranch, "Target branch");
  const headSha = requireNonEmptyString(input.headSha, "Head SHA");

  if (sourceBranch === targetBranch) {
    throw new ValidationError("Source and target branches must differ.");
  }

  return {
    number: input.number,
    title,
    author,
    sourceBranch,
    targetBranch,
    headSha,
  };
}

class PullRequest extends EventEmitter {
  #data;
  #reviews = [];
  #checks = new Map();
  #unresolvedThreads = 0;

  constructor(input) {
    super();
    this.#data = {
      ...validatePullRequestInput(input),
      state: PullRequestState.DRAFT,
    };
  }

  get snapshot() {
    // Return a copy so callers cannot mutate the private state accidentally.
    return Object.freeze({
      ...this.#data,
      reviews: this.#reviews.map((review) => ({ ...review })),
      checks: Object.fromEntries(this.#checks),
      unresolvedThreads: this.#unresolvedThreads,
    });
  }

  publish() {
    this.#transition(PullRequestState.DRAFT, PullRequestState.OPEN);
  }

  #transition(expected, next) {
    if (this.#data.state !== expected) {
      throw new InvalidTransitionError(
        `Cannot transition from ${this.#data.state} to ${next}.`,
      );
    }

    const previous = this.#data.state;
    this.#data.state = next;
    this.emit("stateChanged", {
      number: this.#data.number,
      previous,
      next,
    });
  }

  addReview({ reviewer, state, commitSha, comments = [] }) {
    if (this.#data.state !== PullRequestState.OPEN) {
      throw new InvalidTransitionError("Reviews require an open pull request.");
    }

    requireNonEmptyString(reviewer, "Reviewer");
    requireNonEmptyString(commitSha, "Review commit SHA");

    if (!Object.values(ReviewState).includes(state)) {
      throw new ValidationError(`Unknown review state: ${state}`);
    }
    if (reviewer === this.#data.author) {
      throw new ReviewPolicyError("Self-approval is not permitted.");
    }
    if (!Array.isArray(comments) || comments.some(
      (comment) => typeof comment !== "string" || !comment.trim(),
    )) {
      throw new ValidationError("Review comments must be non-empty strings.");
    }

    const review = Object.freeze({
      reviewer,
      state,
      commitSha,
      comments: [...comments],
      submittedAt: new Date().toISOString(),
    });

    this.#reviews.push(review);
    this.emit("reviewSubmitted", { number: this.#data.number, ...review });
  }

  setStatusCheck(name, passed) {
    if (this.#data.state !== PullRequestState.OPEN) {
      throw new InvalidTransitionError("Checks require an open pull request.");
    }
    requireNonEmptyString(name, "Check name");
    if (typeof passed !== "boolean") {
      throw new ValidationError("Status check result must be boolean.");
    }

    this.#checks.set(name, passed);
    this.emit("checkUpdated", {
      number: this.#data.number,
      name,
      passed,
    });
  }

  setUnresolvedThreads(count) {
    if (!Number.isSafeInteger(count) || count < 0) {
      throw new ValidationError("Thread count must be a non-negative integer.");
    }
    this.#unresolvedThreads = count;
  }

  synchronize(newHeadSha) {
    if (this.#data.state !== PullRequestState.OPEN) {
      throw new InvalidTransitionError("Only open pull requests can be synchronized.");
    }

    requireNonEmptyString(newHeadSha, "New head SHA");
    if (newHeadSha === this.#data.headSha) {
      throw new ValidationError("Synchronization requires a changed head SHA.");
    }

    const previousHead = this.#data.headSha;
    this.#data.headSha = newHeadSha;
    this.#checks.clear();

    this.emit("synchronized", {
      number: this.#data.number,
      previousHead,
      newHead: newHeadSha,
    });
  }

  close() {
    this.#transition(PullRequestState.OPEN, PullRequestState.CLOSED);
  }

  merge(policy) {
    const violations = evaluateMerge(this.snapshot, policy);
    if (violations.length > 0) {
      throw new MergeBlockedError(violations.join(" "));
    }

    this.#transition(PullRequestState.OPEN, PullRequestState.MERGED);
  }
}

function eligibleApprovals(pr, policy) {
  const decisions = new Map();

  for (const review of pr.reviews) {
    if (
      policy.dismissStaleApprovals &&
      review.commitSha !== pr.headSha
    ) {
      continue;
    }

    if (review.state === ReviewState.CHANGES_REQUESTED) {
      decisions.set(review.reviewer, ReviewState.CHANGES_REQUESTED);
    } else if (
      review.state === ReviewState.APPROVED &&
      decisions.get(review.reviewer) !== ReviewState.CHANGES_REQUESTED
    ) {
      decisions.set(review.reviewer, ReviewState.APPROVED);
    }
  }

  return [...decisions.entries()]
    .filter(([, state]) => state === ReviewState.APPROVED)
    .map(([reviewer]) => reviewer);
}

function evaluateMerge(pr, policy) {
  const violations = [];

  if (pr.state !== PullRequestState.OPEN) {
    violations.push("Pull request is not open.");
  }

  const approvals = eligibleApprovals(pr, policy);
  if (approvals.length < policy.requiredApprovals) {
    violations.push(
      `Requires ${policy.requiredApprovals} current approvals; found ${approvals.length}.`,
    );
  }

  for (const checkName of policy.requiredChecks) {
    if (pr.checks[checkName] !== true) {
      violations.push(`Required check failed or is missing: ${checkName}.`);
    }
  }

  if (policy.requireResolvedThreads && pr.unresolvedThreads !== 0) {
    violations.push("Review discussions remain unresolved.");
  }

  return violations;
}

const protectedBranchPolicy = Object.freeze({
  requiredApprovals: 2,
  requiredChecks: Object.freeze(["unit-tests", "security-scan"]),
  requireResolvedThreads: true,
  dismissStaleApprovals: true,
  prohibitDirectPushes: true,
  prohibitForcePushes: true,
  prohibitDeletion: true,
});

function evaluateBranchOperation(operation, branch, policy) {
  requireNonEmptyString(branch, "Branch name");

  if (branch !== "main") {
    return { allowed: true, reason: "Branch is not protected by this policy." };
  }

  const prohibited = {
    directPush: policy.prohibitDirectPushes,
    forcePush: policy.prohibitForcePushes,
    deleteBranch: policy.prohibitDeletion,
  };

  if (prohibited[operation] === undefined) {
    throw new ValidationError(`Unknown branch operation: ${operation}`);
  }
  if (prohibited[operation]) {
    return { allowed: false, reason: `${operation} is prohibited on main.` };
  }

  return { allowed: true, reason: "Policy permits the operation." };
}

async function loadPolicy(filePath) {
  let contents;

  try {
    contents = await fs.readFile(filePath, "utf8");
  } catch (cause) {
    throw new PersistenceError("Unable to read governance policy.", { cause });
  }

  let policy;
  try {
    policy = JSON.parse(contents);
  } catch (cause) {
    throw new PersistenceError("Governance policy contains invalid JSON.", { cause });
  }

  if (
    !policy ||
    !Number.isSafeInteger(policy.requiredApprovals) ||
    policy.requiredApprovals < 0 ||
    !Array.isArray(policy.requiredChecks) ||
    policy.requiredChecks.some(
      (name) => typeof name !== "string" || !name.trim(),
    )
  ) {
    throw new ValidationError("Governance policy has an invalid structure.");
  }

  return policy;
}

async function withTemporaryRetry(operation, attempts = 3) {
  if (!Number.isSafeInteger(attempts) || attempts < 1) {
    throw new ValidationError("Retry attempts must be a positive integer.");
  }

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      // Retry only a known transient failure. Policy and validation errors
      // must propagate immediately because retrying cannot correct them.
      if (!(error instanceof TemporaryServiceError) || attempt === attempts) {
        throw error;
      }

      await new Promise((resolve) => setTimeout(resolve, 10 * attempt));
    }
  }

  throw new Error("Unreachable retry state.");
}

async function demonstrate() {
  const policy = protectedBranchPolicy;
  const pr = new PullRequest({
    number: 106,
    title: "Reject unsafe deployment manifests",
    sourceBranch: "feature/manifest-guard",
    targetBranch: "main",
    author: "alex",
    headSha: "commit-a",
  });

  pr.on("stateChanged", ({ number, previous, next }) => {
    console.log(`PR #${number}: ${previous} -> ${next}`);
  });

  pr.on("reviewSubmitted", ({ reviewer, state }) => {
    console.log(`Review recorded: ${reviewer} (${state})`);
  });

  pr.on("synchronized", ({ previousHead, newHead }) => {
    console.log(`Head changed from ${previousHead} to ${newHead}.`);
  });

  pr.publish();

  try {
    pr.merge(policy);
  } catch (error) {
    if (error instanceof MergeBlockedError) {
      console.log("Initial merge blocked:", error.message);
    } else {
      throw error;
    }
  }

  pr.addReview({
    reviewer: "maya",
    state: ReviewState.APPROVED,
    commitSha: "commit-a",
    comments: ["The manifest schema is enforced before deployment."],
  });
  pr.addReview({
    reviewer: "raj",
    state: ReviewState.APPROVED,
    commitSha: "commit-a",
  });
  pr.setStatusCheck("unit-tests", true);
  pr.setStatusCheck("security-scan", true);

  console.log("Eligible before sync:", eligibleApprovals(pr.snapshot, policy));
  pr.synchronize("commit-b");
  console.log("Eligible after sync:", eligibleApprovals(pr.snapshot, policy));

  try {
    pr.merge(policy);
  } catch (error) {
    console.log("Stale approvals prevented merge:", error.message);
  }

  pr.addReview({
    reviewer: "maya",
    state: ReviewState.APPROVED,
    commitSha: "commit-b",
  });
  pr.addReview({
    reviewer: "raj",
    state: ReviewState.APPROVED,
    commitSha: "commit-b",
  });
  pr.setStatusCheck("unit-tests", true);
  pr.setStatusCheck("security-scan", true);
  pr.setUnresolvedThreads(0);

  console.log("Final policy evaluation:", evaluateMerge(pr.snapshot, policy));
  pr.merge(policy);

  const branchResult = evaluateBranchOperation("forcePush", "main", policy);
  console.log("Protected branch operation:", branchResult);

  const temporaryDirectory = await fs.mkdtemp(
    path.join(os.tmpdir(), "governance-"),
  );

  try {
    const policyPath = path.join(temporaryDirectory, "policy.json");
    await fs.writeFile(
      policyPath,
      JSON.stringify({ requiredApprovals: 2, requiredChecks: ["unit-tests"] }),
      { encoding: "utf8", flag: "wx" },
    );

    console.log("Loaded policy:", await loadPolicy(policyPath));

    let requests = 0;
    const response = await withTemporaryRetry(async () => {
      requests += 1;
      if (requests < 2) {
        throw new TemporaryServiceError("Review service is temporarily unavailable.");
      }
      return { status: "available", requests };
    });
    console.log("Retry result:", response);
  } finally {
    // finally is appropriate for cleanup even when policy parsing or retries fail.
    await fs.rm(temporaryDirectory, { recursive: true, force: true });
  }

  try {
    new PullRequest({
      number: 0,
      title: "",
      sourceBranch: "main",
      targetBranch: "main",
      author: "alex",
      headSha: "commit-x",
    });
  } catch (error) {
    console.log(`Invalid input rejected: ${error.name}: ${error.message}`);
  }

  console.log("JavaScript governance demonstration completed.");
}

demonstrate().catch((error) => {
  // A final process-level handler reports unexpected failures without
  // converting them into a false success.
  console.error("Fatal governance failure:", error);
  process.exitCode = 1;
});

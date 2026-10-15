# Python Modules, Imports, Packages, Standard Library, Virtual Environments, and Dependency Management

## Scope

This learning artifact treats Python's module system and dependency-management model as connected but distinct mechanisms.

A **module** is an importable Python unit, commonly represented by a `.py` file. A **package** provides a structured namespace for related modules. The **standard library** supplies modules distributed with Python itself. Third-party packages are installed separately into an environment. A **virtual environment** isolates an interpreter's installed packages from other project environments. **Dependency management** records and resolves the external software required by an application.

The five implementations approach these mechanisms from different technical perspectives:

| Implementation | Primary perspective |
|---|---|
| Python | Direct module inspection, package creation, environment diagnostics, dependency validation, and executable tests |
| JavaScript | Runtime module resolution, asynchronous dependency orchestration, manifest handling, and Python interpreter discovery |
| C++ | Dependency resolution and compatibility as a systems-oriented governance engine |
| Java | Enterprise-style domain modeling, explicit policies, immutable records, validation, and deployment eligibility |
| PostgreSQL | Relational representation of applications, dependencies, environments, installed packages, and validation results |

The central relationship is:

**imports consume importable modules, packages organize modules, environments determine where dependencies are installed, and dependency-management metadata defines which external versions an application is expected to use.**

These mechanisms should not be treated as interchangeable.

## Python Modules

A Python module is normally a `.py` file that can be imported as a namespace. When code executes an import, Python resolves the requested module using its import machinery and search path.

The Python implementation demonstrates this with standard-library modules such as `math`, `statistics`, `pathlib`, `json`, `configparser`, `hashlib`, and `importlib`.

The distinction between these forms matters:

`import statistics`

creates access through the `statistics` module namespace.

`import statistics as stats`

creates an alias for that module.

`from pathlib import Path`

places a selected object directly into the current namespace.

The artifact deliberately avoids wildcard imports because they make name ownership less explicit and can overwrite existing names.

### Module metadata

The program inspects:

- `__name__`
- `__file__`
- `__package__`
- `__loader__`
- `dir(module)`

These attributes help explain what Python actually loaded and where the module originated.

A module can be built into the interpreter, located in the filesystem, or supplied by an installed distribution. The location reported by `__file__` should therefore not be assumed to have one universal form.

## Import Resolution

The Python program uses `importlib.util.find_spec()` to determine whether an import specification can be found before attempting to load it.

It then uses `importlib.import_module()` for dynamic imports.

Dynamic imports are useful when the application chooses a component at runtime, supports optional functionality, or loads a plugin based on configuration. They should not be used merely to make ordinary imports less visible.

An import failure does not necessarily mean that a package-management problem exists. The failure can also arise because:

- the active interpreter differs from the intended interpreter;
- the import name differs from the distribution name;
- the package is installed into another environment;
- the project contains a module that shadows an intended dependency;
- the module genuinely is not installed;
- the import path does not contain the expected project directory.

The diagnostic portion of the Python implementation prints `sys.path`, making the search locations visible.

## Packages

A package gives related modules a namespace.

The Python implementation constructs a temporary `repository_tools` package containing:

- `__init__.py`
- `validation.py`
- `repository.py`

The repository module imports a function from its sibling module using a relative import:

`from .validation import valid_repository_name`

The leading dot expresses that `validation` belongs to the same package.

The demonstration also shows why temporary changes to `sys.path` should be controlled carefully. The example adds a temporary project directory only for the duration of the package demonstration and removes it afterward. It also removes the temporary package modules from `sys.modules` so that the demonstration does not leave stale imported objects behind.

## Standard Library

The Python standard library is different from an externally installed dependency.

The implementation uses standard-library facilities for configuration, filesystem operations, serialization, hashing, subprocess execution, module discovery, temporary directories, version inspection, and platform information.

The configuration example uses `configparser` to represent an application configuration file. `pathlib` handles filesystem paths. `json` serializes structured metadata. `hashlib` calculates a SHA-256 digest.

This illustrates an important dependency-management decision: an application should use a capable standard-library facility when it satisfies the requirement rather than adding a third-party dependency without a technical reason.

The standard library still has version-dependent behavior. Code that relies on a newer standard-library API may require a minimum Python runtime version even though no third-party package is involved.

## Virtual Environments

A virtual environment provides an isolated Python environment for project dependencies.

The Python implementation determines whether its interpreter is operating in an environment by comparing:

`sys.prefix`

with:

`sys.base_prefix`

When these differ in the normal CPython virtual-environment arrangement, the process is running with an environment-specific prefix.

The program also reports `sys.executable`. This is important when debugging dependency problems because the executable identifies which Python interpreter is actually running the program.

A practical environment workflow separates:

**project source**

from:

**Python interpreter**

and:

**installed dependency set**

A project can therefore contain correct import statements while still failing because its dependency was installed into another interpreter's environment.

## Dependency Management

Dependency management begins with declaring what an application requires.

The Python implementation models dependencies with the `Dependency` dataclass and represents declarations such as:

`httpx>=0.27,<1`

and:

`pydantic>=2.0,<3`

The declaration is not the same thing as the installed package. It expresses a compatibility policy.

The implementation also validates simple requirement-style strings. This is deliberately a small validation model rather than a replacement for Python packaging tools.

Real dependency resolution can involve:

- version constraints;
- transitive dependencies;
- environment markers;
- platform compatibility;
- Python-version requirements;
- optional dependencies;
- pre-release handling;
- package indexes;
- hashes;
- lock information.

The six files focus on the conceptual mechanics without pretending that a small educational parser implements the complete Python packaging ecosystem.

## Requirements and Reproducibility

A dependency declaration should communicate the range of versions an application supports.

An exact requirement such as:

`package==2.4.1`

is stricter than:

`package>=2.4,<3`

The appropriate choice depends on the application's compatibility strategy.

A requirements file can be useful for recording an installable dependency set, while other packaging approaches use project metadata and lock information for different reproducibility requirements.

The important distinction is between:

**declared compatibility**

and:

**the exact environment that was resolved and installed**.

Reproducible deployment requires controlling both.

## Python Dependency Diagnostics

The Python program uses:

`python -m pip`

rather than assuming that a separately resolved `pip` executable belongs to the same interpreter.

This distinction matters because a machine may contain multiple Python installations.

For example, the following two commands can theoretically address different environments when `pip` is independently resolved:

`pip install package`

and:

`python -m pip install package`

Using the selected interpreter with `-m pip` makes the relationship explicit.

The program intentionally performs read-only package-manager inspection. It reports the pip version and installed package metadata without silently changing the user's environment.

## Dependency Compatibility

The Python version-comparison functions normalize version components before comparing them.

For example, `2.0` and `2.0.0` are treated as equivalent by the educational comparison model.

The constraint demonstration evaluates an intersection of requirements. If one component requires:

`httpx>=0.27`

while another requires:

`httpx>=0.28`

the combined lower bound becomes effectively `0.28`.

A conflict occurs when constraints have no common valid version. An exact requirement such as `httpx==0.26.0` cannot satisfy a separate minimum requirement of `httpx>=0.27`.

The actual Python packaging ecosystem has substantially richer version semantics, so the implementation intentionally describes its version parser as a conservative educational model.

## Python Implementation

The Python program progresses from direct imports to package creation, module inspection, dependency metadata, environment diagnostics, dependency constraints, and testing.

The temporary package demonstrates the physical relationship between a package directory and its modules. The `repository.py` module depends on `validation.py`, which makes the dependency between importable modules concrete.

The `ApplicationManifest` class represents application-level dependency metadata and validates its declarations.

The `VersionConstraint` class represents the compatibility range for a package. Its `accepts()` method turns dependency policy into executable behavior.

The self-tests verify version comparison, requirement validation, and constraint behavior. This makes the learning artifact executable rather than relying solely on comments.

## JavaScript Implementation

The JavaScript file takes a different perspective: Node.js acts as an orchestration layer around dependency metadata and Python runtime discovery.

Node's built-in `node:` modules provide a useful comparison with Python's standard library. The example uses:

`node:fs`

`node:path`

`node:os`

`node:events`

and:

`node:child_process`

The module-resolution demonstration uses `require.resolve()` to show how Node identifies a module.

The `DependencyInstaller` class extends `EventEmitter`. Its asynchronous workflow models dependency-processing events without installing real packages. This demonstrates an event-driven mechanism that is natural to Node.js rather than translating the Python package example.

The JavaScript file also writes a temporary JSON manifest and executes Python version checks through child processes. It deliberately does not assume that a command named `python` necessarily identifies the environment used by the project.

## C++ Case Study

The C++ program models dependency resolution as a systems-level compatibility engine.

Its `Version` type parses and compares numeric versions. `DependencyConstraint` represents minimum, exact, and maximum-exclusive rules. `PackageRequirement` combines multiple constraints for a single package.

`DependencyCatalog` stores available versions. `DependencyResolver` selects the highest available version satisfying the complete constraint set.

The environment model is separate from the catalog. This distinction matters because an available version is not automatically an installed version.

The `Environment` class records the runtime and installed package inventory. `DependencyAuditor` then evaluates whether the installed state satisfies the declared requirements.

The case study also creates an explicit conflict:

- one service requires `httpx>=0.27,<1`;
- another requires `httpx==0.26.0`.

There is no version that satisfies both conditions, so the resolver reports a failure.

The selection process sorts available versions and then scans them from highest to lowest. With `V` available versions, sorting requires `O(V log V)` time. Real dependency resolvers must account for substantially more dimensions because dependencies can themselves depend on other packages.

The C++ model also makes an important conceptual distinction between distribution metadata and Python import namespaces. A package's distribution name and the name used in an `import` statement often correspond, but they are not guaranteed to be identical.

## Java Enterprise Model

The Java implementation treats environment validation as an enterprise policy problem.

`Version`, `DependencyConstraint`, `DependencyDeclaration`, `RuntimeRequirement`, and `InstalledPackage` are immutable records representing domain facts.

`PythonEnvironment` owns the installed environment state and evaluates it against declared policies.

The `EnvironmentPolicy` interface separates policy definition from the environment model. `ProductionDependencyPolicy` supplies the concrete dependency rules.

`ValidationFinding` records the severity, subject, and reason for each result. This avoids reducing validation to a single Boolean and allows an enterprise system to distinguish informational findings from deployment-blocking errors.

The healthy environment satisfies both runtime and package requirements. The invalid environment deliberately fails in two different dimensions: its Python runtime is below the required version and its `httpx` package is below the allowed minimum.

This separation is important for operational diagnostics. A single generic "dependency error" would conceal the actual cause.

## SQL Data Model

The PostgreSQL implementation models dependency management relationally.

`applications` identifies applications and their minimum Python runtime.

`packages` represents distribution packages.

`dependency_declarations` records package requirements belonging to an application. The schema uses checks to prevent malformed versions and enforces one declaration per application-package pair.

`environments` represents concrete Python environments.

`installed_packages` records the package version actually present in each environment.

`validation_runs` and `validation_findings` provide an audit trail for environment checks.

Foreign keys prevent orphaned dependency records. Unique constraints prevent duplicate application-package declarations and duplicate environment names within an application.

The indexes target common access patterns involving application dependencies, installed packages, validation environments, and validation severity.

## Database-Level Enforcement

The SQL model places structural rules in the database instead of assuming that application code will always enforce them.

Examples include:

`packages.distribution_name` must match a restricted package-name pattern.

Version fields must follow a numeric dotted-version format.

A dependency must contain at least one constraint.

An exact dependency cannot simultaneously declare minimum and maximum constraints in this model.

An installed package must refer to an existing environment and package.

These constraints protect data even when multiple applications or services write to the database.

## Compliance Queries

The `dependency_compliance` view compares declared dependency constraints with installed versions.

It evaluates minimum and maximum-exclusive ranges using PostgreSQL integer arrays derived from dotted numeric versions.

The environment-level aggregation counts declared dependencies, satisfied dependencies, and failed dependencies.

The runtime query separately evaluates the application's minimum Python version.

Keeping runtime validation separate from package validation makes the resulting operational diagnosis clearer.

## Transactions and Auditability

The SQL script creates validation records inside a transaction.

The transaction calculates environment-level dependency results and inserts a `validation_runs` record with either `PASSED` or `FAILED`.

The transaction boundary is important because a validation record should not be partially recorded. If the transaction fails, PostgreSQL can roll back the operation instead of leaving an incomplete audit state.

A production implementation would usually add more detailed version semantics, package hashes, environment markers, repository/index information, and immutable audit metadata.

## Import Names Versus Distribution Names

One of the most important distinctions in Python dependency work is that the name installed by a package manager is not necessarily the exact name used by an import statement.

The distribution metadata describes an installable package. The import system resolves a Python module or package namespace.

This means a debugging process should ask two separate questions:

**Is the distribution installed into the active environment?**

and:

**Can the active interpreter resolve the requested import?**

A positive answer to the first question does not logically guarantee a positive answer to the second.

## Common Failure Modes

### Wrong interpreter

A dependency can be installed successfully while the application still raises `ModuleNotFoundError` because installation occurred under a different Python interpreter.

The Python implementation exposes `sys.executable` specifically to make this distinction observable.

### Incorrect import name

The distribution name and import name can differ. Package-manager metadata should therefore not be treated as a direct map from installation name to Python source import.

### Environment contamination

Installing project-specific packages into a global interpreter can cause unrelated projects to share incompatible versions.

Virtual environments reduce this coupling by giving each project an isolated installation target.

### Unbounded dependencies

A declaration that accepts every future version can permit incompatible upgrades. A declaration that pins every package exactly can make maintenance and security updates difficult.

Dependency constraints should reflect tested compatibility rather than arbitrary restriction.

### Dependency conflicts

Two applications or components can impose incompatible requirements on the same package. A resolver must identify whether the constraint intersection is empty rather than selecting a version that satisfies only one side.

### Local module shadowing

A file in the current project with the same import name as an installed dependency can change what Python resolves. Module inspection and `sys.path` diagnostics help expose this class of error.

## Performance Considerations

Imports have runtime costs, although Python caches successfully loaded modules in `sys.modules`, preventing repeated execution of the same module initialization during a process's normal lifetime.

Dependency resolution has a different performance profile. It can involve searching available versions and exploring dependency relationships. A simple version-selection model can be inexpensive, while real dependency graphs may require considerably more work.

The C++ implementation uses sorted version candidates. The SQL implementation adds indexes for repeated relational lookups. The Java implementation keeps immutable policy data, making validation behavior easier to reason about.

The appropriate optimization depends on whether the bottleneck is import startup, dependency resolution, filesystem access, package metadata retrieval, or database querying.

## Security Considerations

Dependency management is part of the application's supply-chain boundary.

Important controls include:

- keeping dependency declarations under version control;
- validating dependency metadata;
- using trusted package sources;
- controlling package installation permissions;
- reviewing dependency changes;
- using hashes or lock mechanisms where the deployment model requires stronger reproducibility;
- avoiding execution of untrusted installation commands;
- separating development and production environments;
- monitoring vulnerable dependency versions through an appropriate security process.

The Python implementation intentionally avoids automatically installing dependencies. Its package-manager example is observational because an educational program should not silently modify the user's environment.

The JavaScript example validates dependency names before treating them as metadata. This is particularly relevant when dependency values could eventually flow into process execution.

## Design Relationships

The six files preserve the distinction between the major mechanisms:

| Mechanism | Specific responsibility |
|---|---|
| Module | Provides an importable Python namespace |
| Import | Resolves and loads a module or package |
| Package | Organizes related importable modules |
| Standard library | Supplies Python-distributed functionality without a separate third-party installation |
| Virtual environment | Isolates interpreter and installed dependency state |
| Dependency declaration | States which external versions an application accepts |
| Dependency resolver | Determines a compatible package set |
| Installed environment | Represents what is actually present at runtime |
| Validation | Compares actual state with declared policy |

A reliable Python project needs these mechanisms to work together, but each solves a different problem.

## Practical Operational Model

A project can be understood through four layers.

**Source layer:** Python modules and packages contain the application's importable code.

**Runtime layer:** a specific Python interpreter executes that code.

**Environment layer:** a virtual environment determines the isolated location in which third-party dependencies are installed.

**Dependency-policy layer:** project metadata declares compatible versions and the package-management workflow resolves and installs them.

When an import fails, diagnosing the problem becomes easier if these layers are checked separately rather than assuming that every failure is an import-syntax problem.

## Limitations of the Demonstrations

The version parsers in the Python, C++, Java, and JavaScript examples intentionally use simplified numeric versions. They do not implement the complete semantics of Python packaging standards.

The SQL model similarly treats versions as dotted numeric values rather than implementing the full packaging ecosystem's version specification rules.

Real dependency resolution can include transitive dependency graphs, environment markers, platform tags, optional extras, pre-release handling, package indexes, hashes, wheel compatibility, source distributions, and lock data.

The examples are therefore models of the underlying engineering concepts, not replacements for established Python packaging infrastructure.

The key technical distinction remains constant: **import resolution determines what Python can load, while dependency management determines what software the environment is expected to contain.**

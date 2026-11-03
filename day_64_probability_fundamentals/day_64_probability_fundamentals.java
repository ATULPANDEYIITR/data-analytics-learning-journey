import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Random;
import java.util.Set;

public class ProbabilityFundamentals {

    enum EventRelation {
        INDEPENDENT,
        DEPENDENT,
        DISJOINT,
        OVERLAPPING
    }

    static class ProbabilityException extends RuntimeException {
        ProbabilityException(String message) {
            super(message);
        }
    }

    record Outcome(String name, double probability) {
        Outcome {
            if (name == null || name.isBlank()) {
                throw new ProbabilityException("Outcome name cannot be blank.");
            }

            if (!Double.isFinite(probability)
                    || probability < 0.0
                    || probability > 1.0) {
                throw new ProbabilityException(
                        "Outcome probability must be between 0 and 1."
                );
            }
        }
    }

    static final class DiscreteProbabilitySpace {
        private final Map<String, Double> probabilities;

        DiscreteProbabilitySpace(List<Outcome> outcomes) {
            if (outcomes == null || outcomes.isEmpty()) {
                throw new ProbabilityException(
                        "At least one outcome is required."
                );
            }

            Map<String, Double> temporary = new LinkedHashMap<>();

            for (Outcome outcome : outcomes) {
                if (temporary.put(outcome.name(), outcome.probability()) != null) {
                    throw new ProbabilityException(
                            "Duplicate outcome: " + outcome.name()
                    );
                }
            }

            double total = temporary.values()
                    .stream()
                    .mapToDouble(Double::doubleValue)
                    .sum();

            if (Math.abs(total - 1.0) > 1e-12) {
                throw new ProbabilityException(
                        "Outcome probabilities must sum to 1."
                );
            }

            probabilities = Collections.unmodifiableMap(temporary);
        }

        private void validateEvent(Set<String> event) {
            Objects.requireNonNull(event, "Event cannot be null.");

            for (String outcome : event) {
                if (!probabilities.containsKey(outcome)) {
                    throw new ProbabilityException(
                            "Unknown outcome: " + outcome
                    );
                }
            }
        }

        double probability(Set<String> event) {
            validateEvent(event);

            return event.stream()
                    .mapToDouble(outcome -> probabilities.get(outcome))
                    .sum();
        }

        Set<String> intersection(
                Set<String> first,
                Set<String> second
        ) {
            validateEvent(first);
            validateEvent(second);

            java.util.Set<String> result =
                    new java.util.HashSet<>(first);

            result.retainAll(second);
            return Collections.unmodifiableSet(result);
        }

        Set<String> union(
                Set<String> first,
                Set<String> second
        ) {
            validateEvent(first);
            validateEvent(second);

            java.util.Set<String> result =
                    new java.util.HashSet<>(first);

            result.addAll(second);
            return Collections.unmodifiableSet(result);
        }

        Set<String> complement(Set<String> event) {
            validateEvent(event);

            java.util.Set<String> result =
                    new java.util.HashSet<>(probabilities.keySet());

            result.removeAll(event);
            return Collections.unmodifiableSet(result);
        }

        double conditionalProbability(
                Set<String> event,
                Set<String> given
        ) {
            double pGiven = probability(given);

            if (pGiven == 0.0) {
                throw new ProbabilityException(
                        "Conditional probability is undefined for P(given)=0."
                );
            }

            return probability(intersection(event, given)) / pGiven;
        }

        boolean independent(Set<String> first, Set<String> second) {
            double intersectionProbability =
                    probability(intersection(first, second));

            double product =
                    probability(first) * probability(second);

            return Math.abs(intersectionProbability - product) <= 1e-12;
        }

        EventRelation relation(
                Set<String> first,
                Set<String> second
        ) {
            Set<String> intersection =
                    intersection(first, second);

            if (intersection.isEmpty()) {
                return EventRelation.DISJOINT;
            }

            return independent(first, second)
                    ? EventRelation.INDEPENDENT
                    : EventRelation.OVERLAPPING;
        }
    }

    interface ProbabilityPolicy {
        boolean accepts(double probability);
    }

    static final class RiskPolicy implements ProbabilityPolicy {
        private final double maximumRisk;

        RiskPolicy(double maximumRisk) {
            if (maximumRisk < 0 || maximumRisk > 1) {
                throw new ProbabilityException(
                        "Risk threshold must be between 0 and 1."
                );
            }
            this.maximumRisk = maximumRisk;
        }

        @Override
        public boolean accepts(double probability) {
            return probability <= maximumRisk;
        }
    }

    static double binomialProbability(
            int n,
            int successes,
            double p
    ) {
        if (n < 0 || successes < 0 || successes > n) {
            throw new ProbabilityException("Invalid binomial parameters.");
        }

        if (p < 0 || p > 1) {
            throw new ProbabilityException(
                    "Binomial probability must be between 0 and 1."
            );
        }

        int k = Math.min(successes, n - successes);
        double coefficient = 1.0;

        for (int i = 1; i <= k; i++) {
            coefficient *= (double) (n - i + 1) / i;
        }

        return coefficient
                * Math.pow(p, successes)
                * Math.pow(1 - p, n - successes);
    }

    static Map<Integer, Integer> simulateDie(
            int trials,
            long seed
    ) {
        if (trials <= 0) {
            throw new ProbabilityException(
                    "Trial count must be positive."
            );
        }

        Random random = new Random(seed);
        Map<Integer, Integer> counts = new LinkedHashMap<>();

        for (int i = 1; i <= 6; i++) {
            counts.put(i, 0);
        }

        for (int i = 0; i < trials; i++) {
            int outcome = random.nextInt(6) + 1;
            counts.merge(outcome, 1, Integer::sum);
        }

        return Collections.unmodifiableMap(counts);
    }

    public static void main(String[] args) {
        try {
            List<Outcome> outcomes = List.of(
                    new Outcome("1", 1.0 / 6.0),
                    new Outcome("2", 1.0 / 6.0),
                    new Outcome("3", 1.0 / 6.0),
                    new Outcome("4", 1.0 / 6.0),
                    new Outcome("5", 1.0 / 6.0),
                    new Outcome("6", 1.0 / 6.0)
            );

            DiscreteProbabilitySpace space =
                    new DiscreteProbabilitySpace(outcomes);

            Set<String> even =
                    Set.of("2", "4", "6");

            Set<String> high =
                    Set.of("5", "6");

            Set<String> odd =
                    Set.of("1", "3", "5");

            System.out.println("=== Probability Fundamentals ===");

            System.out.printf(
                    "P(even) = %.4f%n",
                    space.probability(even)
            );

            System.out.printf(
                    "P(high) = %.4f%n",
                    space.probability(high)
            );

            System.out.printf(
                    "P(even union high) = %.4f%n",
                    space.probability(space.union(even, high))
            );

            System.out.printf(
                    "P(even intersection high) = %.4f%n",
                    space.probability(space.intersection(even, high))
            );

            System.out.printf(
                    "P(even | high) = %.4f%n",
                    space.conditionalProbability(even, high)
            );

            System.out.println(
                    "Even/high relation = "
                            + space.relation(even, high)
            );

            System.out.println(
                    "Even/odd relation = "
                            + space.relation(even, odd)
            );

            System.out.println("\n=== Enterprise Policy Evaluation ===");

            ProbabilityPolicy policy = new RiskPolicy(0.25);
            double probabilityOfHigh = space.probability(high);

            System.out.printf(
                    "High-event probability = %.4f%n",
                    probabilityOfHigh
            );

            System.out.println(
                    "Policy accepted = "
                            + policy.accepts(probabilityOfHigh)
            );

            System.out.println("\n=== Binomial Model ===");

            System.out.printf(
                    "P(exactly 3 of 10 successes, p=.2) = %.6f%n",
                    binomialProbability(10, 3, 0.2)
            );

            System.out.println("\n=== Simulation ===");

            Map<Integer, Integer> counts =
                    simulateDie(10000, 42L);

            counts.forEach((outcome, count) ->
                    System.out.printf(
                            "Outcome %d: count=%d, estimated P=%.4f%n",
                            outcome,
                            count,
                            count / 10000.0
                    )
            );

            System.out.println("\n=== Validation ===");

            try {
                new DiscreteProbabilitySpace(
                        List.of(
                                new Outcome("A", 0.4),
                                new Outcome("B", 0.4)
                        )
                );
            } catch (ProbabilityException exception) {
                System.out.println(
                        "Rejected invalid model: "
                                + exception.getMessage()
                );
            }

        } catch (ProbabilityException exception) {
            System.err.println(
                    "Probability error: "
                            + exception.getMessage()
            );
            System.exit(1);
        }
    }
}

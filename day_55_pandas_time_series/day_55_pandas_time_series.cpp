#include <algorithm>
#include <cassert>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

struct Timestamp {
    int year;
    int month;
    int day;
    int hour;
    int minute;

    int serialMinutes() const {
        // A deterministic calendar approximation suitable for ordering
        // this controlled dataset. Month lengths are normalized to 30 days.
        return (((year * 12 + month) * 30 + day) * 24 + hour) * 60 + minute;
    }

    bool operator<(const Timestamp& other) const {
        return serialMinutes() < other.serialMinutes();
    }

    bool operator==(const Timestamp& other) const {
        return year == other.year &&
               month == other.month &&
               day == other.day &&
               hour == other.hour &&
               minute == other.minute;
    }

    std::string toString() const {
        std::ostringstream out;
        out << year << '-'
            << std::setw(2) << std::setfill('0') << month << '-'
            << std::setw(2) << std::setfill('0') << day << ' '
            << std::setw(2) << std::setfill('0') << hour << ':'
            << std::setw(2) << std::setfill('0') << minute;
        return out.str();
    }
};

struct Observation {
    Timestamp timestamp;
    double temperature;
    double pressure;
    double energyKwh;
};

class TimeSeries {
private:
    std::vector<Observation> data;

    static double mean(const std::vector<double>& values) {
        if (values.empty()) {
            throw std::invalid_argument("Mean requires at least one value.");
        }

        return std::accumulate(values.begin(), values.end(), 0.0)
               / static_cast<double>(values.size());
    }

    static double standardDeviation(const std::vector<double>& values) {
        if (values.size() < 2) {
            return 0.0;
        }

        const double average = mean(values);

        double squared = 0.0;
        for (double value : values) {
            squared += (value - average) * (value - average);
        }

        return std::sqrt(squared / static_cast<double>(values.size() - 1));
    }

public:
    explicit TimeSeries(std::vector<Observation> observations)
        : data(std::move(observations)) {

        if (data.empty()) {
            throw std::invalid_argument("Time series cannot be empty.");
        }

        std::sort(
            data.begin(),
            data.end(),
            [](const Observation& a, const Observation& b) {
                return a.timestamp < b.timestamp;
            }
        );

        for (std::size_t i = 1; i < data.size(); ++i) {
            if (data[i].timestamp == data[i - 1].timestamp) {
                throw std::invalid_argument(
                    "Duplicate timestamps are not allowed."
                );
            }
        }
    }

    const std::vector<Observation>& observations() const {
        return data;
    }

    void printDailyResampling() const {
        struct Bucket {
            std::vector<double> temperatures;
            std::vector<double> pressures;
            double energy = 0.0;
        };

        std::map<std::tuple<int, int, int>, Bucket> buckets;

        for (const auto& observation : data) {
            auto key = std::make_tuple(
                observation.timestamp.year,
                observation.timestamp.month,
                observation.timestamp.day
            );

            auto& bucket = buckets[key];

            bucket.temperatures.push_back(observation.temperature);
            bucket.pressures.push_back(observation.pressure);
            bucket.energy += observation.energyKwh;
        }

        std::cout << "\n=== Daily Resampling ===\n";

        for (const auto& [key, bucket] : buckets) {
            const auto [year, month, day] = key;

            std::cout
                << year << '-'
                << std::setw(2) << std::setfill('0') << month << '-'
                << std::setw(2) << std::setfill('0') << day
                << " | temperature_mean="
                << mean(bucket.temperatures)
                << " | pressure_mean="
                << mean(bucket.pressures)
                << " | energy_total="
                << bucket.energy
                << '\n';
        }
    }

    void printRollingWindow(int windowDays) const {
        if (windowDays <= 0) {
            throw std::invalid_argument(
                "Rolling window must be positive."
            );
        }

        std::cout << "\n=== Time-Based Rolling Window ===\n";

        std::size_t left = 0;

        for (std::size_t right = 0; right < data.size(); ++right) {
            const int currentTime = data[right].timestamp.serialMinutes();

            while (
                left < right &&
                currentTime - data[left].timestamp.serialMinutes()
                    > windowDays * 24 * 60
            ) {
                ++left;
            }

            std::vector<double> values;

            for (std::size_t i = left; i <= right; ++i) {
                values.push_back(data[i].temperature);
            }

            std::cout
                << data[right].timestamp.toString()
                << " | value=" << data[right].temperature
                << " | rolling_mean=" << mean(values)
                << " | rolling_std=" << standardDeviation(values)
                << " | observations=" << values.size()
                << '\n';
        }
    }

    void printShiftAndDifference() const {
        std::cout << "\n=== Shift and Difference ===\n";

        for (std::size_t i = 0; i < data.size(); ++i) {
            std::cout << data[i].timestamp.toString()
                      << " | current=" << data[i].temperature;

            if (i == 0) {
                std::cout << " | previous=NULL | difference=NULL\n";
            } else {
                const double difference =
                    data[i].temperature - data[i - 1].temperature;

                std::cout
                    << " | previous=" << data[i - 1].temperature
                    << " | difference=" << difference
                    << '\n';
            }
        }
    }

    void printHourlyGrouping() const {
        struct Bucket {
            std::vector<double> temperatures;
            double energy = 0.0;
        };

        std::map<int, Bucket> groups;

        for (const auto& observation : data) {
            auto& bucket = groups[observation.timestamp.hour];

            bucket.temperatures.push_back(observation.temperature);
            bucket.energy += observation.energyKwh;
        }

        std::cout << "\n=== Hour-of-Day Grouping ===\n";

        for (const auto& [hour, bucket] : groups) {
            std::cout
                << "hour=" << hour
                << " | temperature_mean="
                << mean(bucket.temperatures)
                << " | energy_total="
                << bucket.energy
                << " | observations="
                << bucket.temperatures.size()
                << '\n';
        }
    }
};

int main() {
    try {
        TimeSeries series({
            {{2026, 1, 1, 8, 0}, 21.2, 1008, 3.1},
            {{2026, 1, 1, 12, 0}, 22.1, 1007, 2.4},
            {{2026, 1, 2, 9, 30}, 20.8, 1009, 3.7},
            {{2026, 1, 3, 10, 0}, 23.4, 1006, 4.0},
            {{2026, 1, 5, 14, 0}, 24.0, 1005, 5.1},
            {{2026, 1, 6, 11, 15}, 23.2, 1007, 4.4},
            {{2026, 1, 8, 16, 30}, 25.1, 1004, 5.8},
            {{2026, 1, 10, 9, 0}, 26.0, 1003, 6.2},
            {{2026, 1, 12, 13, 45}, 24.7, 1005, 5.0},
            {{2026, 1, 14, 15, 0}, 27.2, 1002, 6.7}
        });

        series.printDailyResampling();
        series.printRollingWindow(7);
        series.printShiftAndDifference();
        series.printHourlyGrouping();

        assert(series.observations().size() == 10);
        assert(series.observations().front().timestamp.year == 2026);
        assert(series.observations().back().temperature == 27.2);

        std::cout << "\nAll validation checks passed.\n";
    }
    catch (const std::exception& error) {
        std::cerr << "Processing failed: "
                  << error.what()
                  << '\n';
        return 1;
    }

    return 0;
}

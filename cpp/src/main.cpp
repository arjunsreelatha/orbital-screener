#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <chrono>
#include <nlohmann/json.hpp>
#include <perturb/perturb.hpp>

struct TLE {
    std::string name;
    std::string line1;
    std::string line2;
};

std::vector<TLE> load_tles(const std::string& path) {
    std::ifstream file(path);
    std::vector<TLE> tles;
    std::string name, line1, line2;
    while (std::getline(file, name)) {
        if (!std::getline(file, line1)) break;
        if (!std::getline(file, line2)) break;
        auto trim = [](std::string& s) {
            while (!s.empty() && (s.back() == '\r' || s.back() == '\n')) s.pop_back();
        };
        trim(name); trim(line1); trim(line2);
        tles.push_back({name, line1, line2});
    }
    return tles;
}

double miss_distance(const perturb::Vec3& a, const perturb::Vec3& b) {
    double dx = a[0] - b[0];
    double dy = a[1] - b[1];
    double dz = a[2] - b[2];
    return std::sqrt(dx*dx + dy*dy + dz*dz);
}

double relative_velocity(const perturb::Vec3& va, const perturb::Vec3& vb) {
    double dvx = va[0] - vb[0];
    double dvy = va[1] - vb[1];
    double dvz = va[2] - vb[2];
    return std::sqrt(dvx*dvx + dvy*dvy + dvz*dvz);
}

double jd_to_unix(double jd, double jd_frac) {
    return ((jd + jd_frac) - 2440587.5) * 86400.0;
}

int main() {
    auto tles = load_tles("../../data/tles/starlink.tle");
    std::cout << "Total objects loaded: " << tles.size() << std::endl;

    int N = tles.size();

    // parse TLEs once
    std::vector<perturb::Satellite> satellites;
    std::vector<bool> valid(N, true);
    for (int i = 0; i < N; i++) {
        satellites.push_back(perturb::Satellite::from_tle(tles[i].line1, tles[i].line2));
        if (satellites.back().last_error() != perturb::Sgp4Error::NONE) {
            valid[i] = false;
        }
    }

    // time loop settings
    // start: 2026-06-25 00:00:00 UTC
    // step:  10 minutes = 10/1440 days
    // total: 7 days = 1008 steps
    perturb::DateTime start_dt;
    start_dt.year  = 2026;
    start_dt.month = 6;
    start_dt.day   = 25;
    start_dt.hour  = 0;
    start_dt.min   = 0;
    start_dt.sec   = 0.0;

    perturb::JulianDate start_jd(start_dt);
    const double STEP_DAYS     = 10.0 / 1440.0;  // 10 minutes in days
    const int    TOTAL_STEPS   = 1008;
    const double THRESHOLD_KM  = 50.0;

    nlohmann::json results = nlohmann::json::array();
const std::string OUTPUT_FILE = "../../data/conjunctions/conjunctions.json";

    auto wall_start = std::chrono::high_resolution_clock::now();

    for (int step = 0; step < TOTAL_STEPS; step++) {
        perturb::JulianDate jd = start_jd + (step * STEP_DAYS);
        double unix_time = jd_to_unix(jd.jd, jd.jd_frac);

        // propagate all satellites to this timestamp
        std::vector<perturb::StateVector> states(N);
        std::vector<bool> step_valid = valid;

        for (int i = 0; i < N; i++) {
            if (!step_valid[i]) continue;
            auto err = satellites[i].propagate(jd, states[i]);
            if (err != perturb::Sgp4Error::NONE) {
                step_valid[i] = false;
            }
        }

        // screen all pairs
        for (int i = 0; i < N; i++) {
            if (!step_valid[i]) continue;
            for (int j = i + 1; j < N; j++) {
                if (!step_valid[j]) continue;

                double dist = miss_distance(states[i].position, states[j].position);
                if (dist < THRESHOLD_KM) {
                    double rel_vel = relative_velocity(states[i].velocity, states[j].velocity);

                    nlohmann::json event;
                    event["object1_name"]           = tles[i].name;
                    event["object2_name"]           = tles[j].name;
                    event["miss_distance_km"]       = dist;
                    event["relative_velocity_km_s"] = rel_vel;
                    event["tca_unix"]               = unix_time;
                    event["pos1_teme"]              = {states[i].position[0], states[i].position[1], states[i].position[2]};
                    event["pos2_teme"]              = {states[j].position[0], states[j].position[1], states[j].position[2]};

                    results.push_back(event);
                }
            }
        }

        // progress every 50 steps
        if (step % 50 == 0) {
    auto now = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(now - wall_start).count();
    std::cout << "Step " << step << "/" << TOTAL_STEPS
              << " | candidates so far: " << results.size()
              << " | elapsed: " << elapsed << "s" << std::endl;

    // write incrementally so Ctrl+C doesn't lose data
    std::ofstream out(OUTPUT_FILE);
    out << results.dump(2);
    out.close();
}
    }

    std::ofstream out(OUTPUT_FILE);
    out << results.dump(2);
    out.close();

    auto wall_end = std::chrono::high_resolution_clock::now();
    double total = std::chrono::duration<double>(wall_end - wall_start).count();
    std::cout << "Done. Total candidates: " << results.size() << std::endl;
    std::cout << "Total time: " << total << " seconds" << std::endl;
    std::cout << "Written to data/conjunctions/conjunctions.json" << std::endl;
    return 0;
}
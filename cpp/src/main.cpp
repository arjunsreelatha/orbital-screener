#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
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

int main() {
    auto tles = load_tles("../../data/tles/starlink.tle");
    std::cout << "Total objects loaded: " << tles.size() << std::endl;

    int N = tles.size();
    std::cout << "Screening " << N << " objects..." << std::endl;

    perturb::DateTime dt;
    dt.year  = 2026;
    dt.month = 6;
    dt.day   = 25;
    dt.hour  = 19;
    dt.min   = 19;
    dt.sec   = 35.0;
    perturb::JulianDate jd(dt);

    std::vector<perturb::StateVector> states(N);
    std::vector<bool> valid(N, true);

    for (int i = 0; i < N; i++) {
        auto sat = perturb::Satellite::from_tle(tles[i].line1, tles[i].line2);
        if (sat.last_error() != perturb::Sgp4Error::NONE) {
            valid[i] = false;
            continue;
        }
        auto err = sat.propagate(jd, states[i]);
        if (err != perturb::Sgp4Error::NONE) {
            valid[i] = false;
        }
    }

    const double THRESHOLD_KM = 5.0;
    nlohmann::json results = nlohmann::json::array();

    for (int i = 0; i < N; i++) {
        if (!valid[i]) continue;
        for (int j = i + 1; j < N; j++) {
            if (!valid[j]) continue;

            double dist = miss_distance(states[i].position, states[j].position);
            if (dist < THRESHOLD_KM) {
                double rel_vel = relative_velocity(states[i].velocity, states[j].velocity);

                nlohmann::json event;
                event["object1_name"]          = tles[i].name;
                event["object2_name"]          = tles[j].name;
                event["miss_distance_km"]      = dist;
                event["relative_velocity_km_s"] = rel_vel;
                event["pos1_teme"]             = {states[i].position[0], states[i].position[1], states[i].position[2]};
                event["pos2_teme"]             = {states[j].position[0], states[j].position[1], states[j].position[2]};

                results.push_back(event);
                std::cout << "CANDIDATE: " << tles[i].name
                          << " vs " << tles[j].name
                          << " | dist = " << dist << " km"
                          << std::endl;
            }
        }
    }

    // write to file
    std::ofstream out("../../data/conjunctions/conjunctions.json");
    out << results.dump(2);
    out.close();

    std::cout << "Screening done. Candidates found: " << results.size() << std::endl;
    std::cout << "Written to data/conjunctions/conjunctions.json" << std::endl;
    return 0;
}
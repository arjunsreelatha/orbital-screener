#include <iostream>
#include <fstream>
#include <vector>
#include <string>
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

int main() {
    auto tles = load_tles("../../data/tles/starlink.tle");
    std::cout << "Total objects: " << tles.size() << std::endl;

    // propagate first satellite - STARLINK-1008
    auto& t = tles[0];
    std::cout << "Propagating: " << t.name << std::endl;

    // from_tle takes mutable strings
    auto sat = perturb::Satellite::from_tle(t.line1, t.line2);

    if (sat.last_error() != perturb::Sgp4Error::NONE) {
        std::cerr << "TLE parse error!" << std::endl;
        return 1;
    }

    // same timestamp as Python test: 2026-06-23 19:19:35 UTC
    perturb::DateTime dt;
    dt.year  = 2026;
    dt.month = 6;
    dt.day   = 23;
    dt.hour  = 19;
    dt.min   = 19;
    dt.sec   = 35.0;

    perturb::JulianDate jd(dt);
    perturb::StateVector sv;

    auto err = sat.propagate(jd, sv);
    if (err != perturb::Sgp4Error::NONE) {
        std::cerr << "Propagation error!" << std::endl;
        return 1;
    }

    std::cout << "Position (TEME, km):" << std::endl;
    std::cout << "  x = " << sv.position[0] << std::endl;
    std::cout << "  y = " << sv.position[1] << std::endl;
    std::cout << "  z = " << sv.position[2] << std::endl;

    return 0;
}
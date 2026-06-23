cmake_minimum_required(VERSION 3.15)
project(orbital_screener)

set(CMAKE_CXX_STANDARD 17)

include(FetchContent)

FetchContent_Declare(
  perturb
  GIT_REPOSITORY https://github.com/gunvirranu/perturb.git
  GIT_TAG        5723e50a54d438876b7a02e02a326e30b51ead4c
)

FetchContent_Declare(
  nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG        v3.11.3
)

FetchContent_MakeAvailable(perturb nlohmann_json)

add_executable(orbital_screener src/main.cpp)

target_link_libraries(orbital_screener PRIVATE perturb nlohmann_json::nlohmann_json)
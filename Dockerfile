FROM python:3.11-slim

# Install C++ and CMake
RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY python/requirments.txt /app/python/requirments.txt

RUN pip install --no-cache-dir -r /app/python/requirments.txt

# Copy project
COPY cpp /app/cpp
COPY data /app/data
COPY python /app/python

# Build C++ executable
RUN cmake -S /app/cpp -B /app/cpp/build \
    -DCMAKE_BUILD_TYPE=Release

RUN cmake --build /app/cpp/build --config Release

# Port used by FastAPI
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "python.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
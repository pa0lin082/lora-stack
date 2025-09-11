ARG PYTHON_VERSION="3.13"
FROM python:${PYTHON_VERSION}-slim AS base
ENV PIPENV_VENV_IN_PROJECT=1

# Multi-stage build per ottimizzare dimensioni dell'immagine
##########################################################################
##########################################################################
##########################################################################
FROM base AS builder
##########################################################################
# Install pipenv
RUN pip install pipenv

# Set working directory
WORKDIR /app


# Copy dependency files
COPY Pipfile* ./

# Install dependencies
RUN pipenv install --deploy 


# Copy application code
COPY . .
RUN sh scripts/generate_proto.sh

# Run the application
CMD ["pipenv", "run", "python", "meshtasticMqttToInfluxDb"]


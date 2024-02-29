FROM python:3.10
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR="/opt/.cache" \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 -
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
ENV PATH="${POETRY_HOME}/bin:${PATH}" 
RUN poetry install
COPY . /app/
EXPOSE 5000

# Development
# CMD ["poetry", "run", "flask", "--app", "yocto", "run", "--host", "0.0.0.0", "--port", "5000", "--debug"]

# Production
RUN pip install gunicorn
CMD ["gunicorn", "-w", "12", "-b", "0.0.0.0:5000", "yocto:create_app('ProductionConfig')"]
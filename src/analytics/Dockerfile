FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn

# Copy only requirements if you had any (optional for future)
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# Copy the file only if you want a fallback image build
# Leave this out if you plan to mount the file instead (or leave in, overriden)
COPY *.py .
COPY templates/ templates/

EXPOSE 7275

# Entrypoint overridden by docker-compose for live reload
CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "7275"]

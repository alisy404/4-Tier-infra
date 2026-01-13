# 1️⃣ Use a small official Python image
FROM python:3.11-slim

# 2️⃣ Set working directory inside container
WORKDIR /app

# 3️⃣ Install dependencies first (cache-friendly)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable for application environment
ENV APP_ENV=local

# 4️⃣ Copy application code
COPY app.py config.py ./

# 5️⃣ Expose app port
EXPOSE 80

# 6️⃣ Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]

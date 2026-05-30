# Pull the lightweight base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

#Expose the port the app runs on
EXPOSE 8080

# Set execution command
# CMD ["python", "manage.py","runserver","0.0.0.0:8080"]
ENTRYPOINT ["sh","-c","python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]
# Estefadeh az Python 3.11 sabok
FROM python:3.11-slim

# Sakhtane poosheh kari tuye Docker
WORKDIR /app

# Copy kardane niazmandiha va nasb e anha
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy kardane kolle code haye barname
COPY . .

# Baz kardane port 8000
EXPOSE 8000

# Dastoor e roshan kardane barname tuye Docker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
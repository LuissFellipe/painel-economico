FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# O dbt_utils é baixado na construção da imagem, e não a cada execução.
RUN dbt deps --profiles-dir dbt_bcb --project-dir dbt_bcb
CMD ["python", "-u", "agendador.py"]

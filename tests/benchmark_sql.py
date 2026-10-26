import psycopg2
from pgbenchmark import Benchmark

conn = psycopg2.connect(
    dbname = "appdb",
    user = "appuser",
    password = "apppassword",
    host = "localhost",
    port = "5432"
)

benchmark = Benchmark(db_connection=conn, number_of_runs=1000)
benchmark.set_sql("SELECT * FROM students LIMIT 20;")

for _ in benchmark:
    pass

print(benchmark.get_execution_results())
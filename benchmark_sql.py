import psycopg2
from pgbenchmark import Benchmark

conn = psycopg2.connect(
    dbname = "appdb",
    user = "appuser",
    password = "apppassword",
    host = 
)
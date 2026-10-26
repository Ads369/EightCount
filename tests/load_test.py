
# import concurrent.futures
# import json
# import time
# import urllib.request

# URL = "http://127.0.0.1:8000/check-in"
# TOTAL = 10500
# WORKERS = 100

# def one_request(owner: str):
#     data = json.dumps({"owner": owner}).encode()
#     req = urllib.request.Request(URL, data=data, headers={"Content-Type": "application/json"})
#     try:
#         with urllib.request.urlopen(req) as resp:
#             return resp.status
#     except urllib.error.HTTPError as e:
#         return e.code

# def main():
#     start = time.time()
#     with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
#         results = list(pool.map(lambda _: one_request("Алексей"), range(TOTAL)))
#     elapsed = time.time() - start
#     ok = sum(1 for s in results if s == 200)
#     print(f"Запросов: {TOTAL}, успешных: {ok}, время: {elapsed:.2f} сек")

# if __name__ == "__main__":
#     main()

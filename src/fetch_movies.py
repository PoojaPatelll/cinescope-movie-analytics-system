import requests
import time
import mysql.connector

# 🔐 PUT YOUR REAL API KEY HERE
import os
API_KEY = os.getenv("TMDB_API_KEY")

url = f"https://api.themoviedb.org/3/trending/movie/day?api_key={API_KEY}"

headers = {
    "User-Agent": "Mozilla/5.0"
}

# 🌐 Fetch data with retry
for attempt in range(3):
    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            break
        else:
            print("API Error:", response.status_code)

    except Exception as e:
        print("Connection error:", e)
        print("Retrying...")
        time.sleep(3)
else:
    print("Failed after retries")
    exit()

# 🗄️ Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="your_password",   # your MySQL password
    database="cinescope_db"
)

cursor = conn.cursor(buffered=True)

# 📥 Insert movies
for movie in data["results"]:
    if "title" not in movie:
        continue

    title = movie["title"]

    # Check if movie already exists
    check_query = "SELECT * FROM movies WHERE title = %s"
    cursor.execute(check_query, (title,))
    result = cursor.fetchone()

    # Insert only if not exists
    if result is None:
        insert_query = "INSERT INTO movies (title) VALUES (%s)"
        cursor.execute(insert_query, (title,))
        print(f"Inserted: {title}")
    else:
        print(f"Already exists: {title}")

# 💾 Save changes
conn.commit()

print("Movies inserted successfully!")

# 🔒 Close connection
cursor.close()
conn.close()

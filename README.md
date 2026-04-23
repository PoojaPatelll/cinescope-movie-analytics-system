# CineScope – Real-Time Movie Analytics & Data Pipeline System

## 📌 Overview
CineScope is a live movie and series analytics system that fetches real-time data from the TMDB API, stores it in a MySQL database, and updates automatically on a daily basis. The system is designed to handle duplicates, maintain clean data, and support relational queries.


## 🚀 Features
- 🔄 Fetches real-time trending movies using TMDB API  
- ⏰ Automated daily database updates using Task Scheduler  
- 🗄️ MySQL database integration  
- 🔗 Relational database design with foreign key constraints  
- 📋 Watchlist feature to track movies and series  
- 🧠 SQL queries for data analysis (joins, aggregations, trends)  
- ⚠️ Error handling and retry mechanism for API failures

## 📸 Project Screenshots

### 🎬 Movies Table
![Movies](movies.png)

### 📋 Watchlist Table
![Watchlist](watchlist.png)

### 🔗 Watchlist with Movie IDs (Join)
![Join](join.png)

### 📊 Data Analysis
![Analytics](analytics.png)


## 🛠️ Tech Stack
- Python  
- MySQL  
- TMDB API  
- SQL  
- Windows Task Scheduler  


## 🗂️ Project Structure

```
cinescope/
│── fetch_movies.py
│── requirements.txt
│── schema.sql
│── README.md
```


## ⚙️ Setup Instructions
1. Clone the repository  
2. Install dependencies:  pip install -r requirements.txt
3. Set your TMDB API key in `fetch_movies.py`
4. Run the script:  python fetch_movies.py


## 📊 Database Design
- Movies table stores movie details  
- Watchlist table stores user-tracked content  
- Foreign key relationship ensures data consistency  


## 🔥 Key Highlights
- Built a real-time data pipeline integrating API + database  
- Implemented duplicate handling for clean data storage  
- Designed relational schema with meaningful queries  
- Automated system to simulate real-world data updates  


## 📌 Future Improvements
- Add web interface for user interaction  
- Visual dashboard for analytics  
- Store more detailed movie metadata

  ## ⚡ Challenges Faced
- Handling API connection errors and retries  
- Preventing duplicate entries in database  
- Mapping inconsistent movie titles between datasets  

## 🧠 Learnings
- Implemented real-time API data fetching using Python  
- Designed relational database with foreign key constraints  
- Performed SQL joins and aggregation queries  
- Built automated data pipeline using Task Scheduler  
- Handled API failures and ensured data consistency


## 👩‍💻 Author
Pooja Patel

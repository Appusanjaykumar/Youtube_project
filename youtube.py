import streamlit as st
import sqlite3
import pymongo
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set up MongoDB connection
mongo_client = pymongo.MongoClient("mongodb+srv://sanjaykumar:sanjay6336@cluster0.kqvktku.mongodb.net/?retryWrites=true&w=majority")
mongo_db = mongo_client["youtube_data"]
mongo_collection = mongo_db["channel_data"]

# Set up SQLite connection
sql_connection = sqlite3.connect("youtube_data.db")
sql_cursor = sql_connection.cursor()

# Define your YouTube API key (replace with your actual API key)
API_KEY = "AIzaSyB0pJaF8hCq4TngMkiIIjY_M0DEcq-QgyI"  # Replace with your YouTube API key

# Initialize the YouTube API client
youtube = build("youtube", "v3", developerKey=API_KEY)

# Streamlit app
def main():
    st.title("YouTube Data Analysis")

    # Input field for a single channel ID
    channel_id = st.text_input("Enter a YouTube Channel ID:")

    if st.button("Retrieve Channel Data"):
        if channel_id:
            channel_data = retrieve_channel_data(channel_id)
            if channel_data:
                display_channel_data(channel_data)
            else:
                st.error(f"No channel data found for channel ID {channel_id}")
        else:
            st.error("Channel ID is empty or not provided.")

    # Button to display questions and answers
    if st.button("Questions"):
        display_questions_and_answers()  # Remove the channel_id argument

    # Button to display a graph chart
    if st.button("Graph Chart"):
        display_graph_chart()

    # Display channel details and questions/answers based on provided channel ID
    if channel_id:
        display_channel_data(retrieve_channel_data(channel_id))

def retrieve_channel_data(channel_id):
    try:
        # Call the YouTube API to retrieve channel details
        channel_response = youtube.channels().list(
            part='snippet,statistics,contentDetails',
            id=channel_id
        ).execute()

        # Check if any items were returned in the response
        if 'items' in channel_response:
            # Extract channel information from the first item in the response
            channel_item = channel_response['items'][0]

            # Extract relevant information from the channel item
            channel_name = channel_item['snippet']['title']
            subscribers = channel_item['statistics']['subscriberCount']
            total_videos = channel_item['statistics']['videoCount']
            playlist_id = channel_item['contentDetails']['relatedPlaylists']['uploads']

            # Create a dictionary to store the channel data
            channel_data = {
                '_id': channel_id,  # Using '_id' as the channel_id
                'Channel_name': channel_name,
                'Subscribers': subscribers,
                'Total_Videos': total_videos,
                'Playlist_id': playlist_id,
                'Videos': [],  # Initialize an empty list for videos
            }

            # Fetch video data for the channel
            channel_data['Videos'] = get_video_data(channel_id, playlist_id)

            return channel_data
        else:
            # If no data was found, return an empty dictionary
            return {}

    except HttpError as e:
        # Handle API errors here if needed
        print(f"Error retrieving data for channel ID {channel_id}: {str(e)}")
        return {}

def get_video_data(channel_id, playlist_id):
    try:
        # Call the YouTube API to retrieve video data for the playlist
        playlist_response = youtube.playlistItems().list(
            part='contentDetails',
            playlistId=playlist_id,
            maxResults=20  # You can increase this to get more videos
        ).execute()

        videos = playlist_response.get('items', [])
        video_data = []

        for video in videos:
            video_id = video['contentDetails']['videoId']
            video_info = youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            ).execute()

            video_details = {
                'Video_ID': video_id,
                'Title': video_info['items'][0]['snippet']['title'],
                'Likes': video_info['items'][0]['statistics'].get('likeCount', 0),  # Handle missing keys
                'Dislikes': video_info['items'][0]['statistics'].get('dislikeCount', 0),  # Handle missing keys
                'Views': video_info['items'][0]['statistics'].get('viewCount', 0),  # Handle missing keys
                'Comments': get_comments(channel_id, video_id),
            }

            video_data.append(video_details)

        return video_data

    except HttpError as e:
        # Handle API errors here if needed
        print(f"Error retrieving video data for channel ID {channel_id}: {str(e)}")
        return []

def get_comments(channel_id, video_id):
    try:
        # Call the YouTube API to retrieve comments for a video
        comments_response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=5  # You can change this to get more comments per video
        ).execute()

        comments = comments_response.get('items', [])
        comment_texts = []

        for comment in comments:
            comment_text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
            comment_texts.append(comment_text)

        return comment_texts

    except HttpError as e:
        # Handle API errors here if needed
        print(f"Error retrieving comments for channel ID {channel_id}, video ID {video_id}: {str(e)}")
        return []

def display_graph_chart():
    # Sample data for the chart (you can replace this with your data)
    data = {
        'Category': ['Category A', 'Category B', 'Category C', 'Category D'],
        'Value': [10, 25, 15, 30]
    }

    # Create a DataFrame from the sample data
    df = pd.DataFrame(data)

    # Create a bar chart using Seaborn
    st.subheader("Sample Bar Chart")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.barplot(data=df, x='Category', y='Value', ax=ax)
    ax.set_xlabel("Categories")
    ax.set_ylabel("Values")
    ax.set_title("Sample Bar Chart")

    # Display the figure using st.pyplot()
    st.pyplot(fig)

def execute_query(question):
    try:
        if question == "1. What are the names of all the videos and their corresponding channels?":
            query = "SELECT Title, Channel_ID FROM youtube_videos"

        elif question == "2. Which channels have the most number of videos, and how many videos do they have?":
            query = """
            SELECT Channel_ID, COUNT(*) AS VideoCount
            FROM youtube_videos
            GROUP BY Channel_ID
            ORDER BY VideoCount DESC
            LIMIT 1
            """

        elif question == "3. What are the top 10 most viewed videos and their respective channels?":
            query = """
            SELECT Title, Channel_ID, Views
            FROM youtube_videos
            ORDER BY Views DESC
            LIMIT 10
            """

        elif question == "4. How many comments were made on each video, and what are their corresponding video names?":
            query = "SELECT Title, Comments FROM youtube_videos"

        elif question == "5. Which videos have the highest number of likes, and what are their corresponding channel names?":
            query = """
            SELECT Title, Likes, Channel_ID
            FROM youtube_videos
            ORDER BY Likes DESC
            LIMIT 10
            """

        elif question == "6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?":
            query = "SELECT Title, Likes, Dislikes FROM youtube_videos"

        elif question == "7. What is the total number of views for each channel, and what are their corresponding channel names?":
            query = """
            SELECT Channel_ID, SUM(Views) AS TotalViews
            FROM youtube_videos
            GROUP BY Channel_ID
            """

        elif question == "8. What are the names of all the channels that have published videos in the year 2022?":
            query = """
            SELECT DISTINCT c.Channel_Name
            FROM youtube_videos v
            INNER JOIN youtube_channels c ON v.Channel_ID = c.Channel_ID
            WHERE SUBSTR(v.Publish_Date, 1, 4) = '2022'
            """

        elif question == "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?":
            query = """
            SELECT Channel_ID, AVG(Duration) AS AvgDuration
            FROM youtube_videos
            GROUP BY Channel_ID
            """

        elif question == "10. Which videos have the highest number of comments, and what are their corresponding channel names?":
            query = """
            SELECT Title, Comments, Channel_ID
            FROM youtube_videos
            ORDER BY LENGTH(Comments) DESC
            LIMIT 10
            """

        sql_cursor.execute(query)

        # Fetch all the rows returned by the query
        rows = sql_cursor.fetchall()

        return rows

    except Exception as e:
        st.error(f"Error executing SQL query: {str(e)}")
        return []

def display_questions_and_answers():
    st.header("Questions and Answers")

    # Question 1
    st.subheader("1. What are the names of all the videos and their corresponding channels?")
    answer1 = execute_query("1. What are the names of all the videos and their corresponding channels?")
    display_table(answer1)

    # Question 2
    st.subheader("2. Which channels have the most number of videos, and how many videos do they have?")
    answer2 = execute_query("2. Which channels have the most number of videos, and how many videos do they have?")
    display_table(answer2)

    # Question 3
    st.subheader("3. What are the top 10 most viewed videos and their respective channels?")
    answer3 = execute_query("3. What are the top 10 most viewed videos and their respective channels?")
    display_table(answer3)

    # Question 4
    st.subheader("4. How many comments were made on each video, and what are their corresponding video names?")
    answer4 = execute_query("4. How many comments were made on each video, and what are their corresponding video names?")
    display_table(answer4)

    # Question 5
    st.subheader("5. Which videos have the highest number of likes, and what are their corresponding channel names?")
    answer5 = execute_query("5. Which videos have the highest number of likes, and what are their corresponding channel names?")
    display_table(answer5)

    # Question 6
    st.subheader("6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?")
    answer6 = execute_query("6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?")
    display_table(answer6)

    # Question 7
    st.subheader("7. What is the total number of views for each channel, and what are their corresponding channel names?")
    answer7 = execute_query("7. What is the total number of views for each channel, and what are their corresponding channel names?")
    display_table(answer7)

    # Question 8
    st.subheader("8. What are the names of all the channels that have published videos in the year 2022?")
    answer8 = execute_query("8. What are the names of all the channels that have published videos in the year 2022?")
    display_table(answer8)

    # Question 9
    st.subheader("9. What is the average duration of all videos in each channel, and what are their corresponding channel names?")
    answer9 = execute_query("9. What is the average duration of all videos in each channel, and what are their corresponding channel names?")
    display_table(answer9)

    # Question 10
    st.subheader("10. Which videos have the highest number of comments, and what are their corresponding channel names?")
    answer10 = execute_query("10. Which videos have the highest number of comments, and what are their corresponding channel names?")
    display_table(answer10)

def display_table(data):
    if data:
        st.table(data)
    else:
        st.info("No results found for the query.")

def store_in_mongodb(data):
    try:
        # Update or insert the data into the MongoDB collection
        result = mongo_collection.update_one(
            {'_id': data['_id']},
            {'$set': data},
            upsert=True
        )
        return result.acknowledged  # Return True if the operation was acknowledged
    except Exception as e:
        st.error(f"Error updating/inserting data in MongoDB: {str(e)}")
        return False

def migrate_to_sql(data):
    try:
        # Create a table if it doesn't exist (you can customize the schema)
        sql_cursor.execute('''
            CREATE TABLE IF NOT EXISTS youtube_videos (
                Video_ID TEXT PRIMARY KEY,
                Title TEXT,
                Likes INTEGER,
                Dislikes INTEGER,
                Views INTEGER,
                Channel_ID TEXT,
                Comments TEXT,
                Duration TEXT  -- Add a Duration column
            )
        ''')

        # Insert video data into the SQL table
        for video in data['Videos']:
            sql_cursor.execute('''
                INSERT OR REPLACE INTO youtube_videos 
                (Video_ID, Title, Likes, Dislikes, Views, Channel_ID, Comments, Duration) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video['Video_ID'],
                video['Title'],
                video['Likes'],
                video['Dislikes'],
                video['Views'],
                data['_id'],
                '\n'.join(video['Comments']),
                video.get('Duration', '')  # Insert Duration if available, otherwise insert an empty string
            ))

        # Commit the changes to the database
        sql_connection.commit()

        print("Data migrated to SQL database successfully.")

    except Exception as e:
        print(f"Error migrating data to SQL database: {str(e)}")

def execute_sql_query(query):
    try:
        # Execute the SQL query
        sql_cursor.execute(query)

        # Fetch all the rows returned by the query
        rows = sql_cursor.fetchall()

        if rows:
            # Display the query result in a table-like structure
            st.subheader("SQL Query Result")

            # Get the column names (titles)
            column_names = [description[0] for description in sql_cursor.description]

            # Prepare the output
            output = [column_names] + rows

            # Display data in a table
            st.table(output)

        else:
            st.info("No results found for the query.")

    except Exception as e:
        st.error(f"Error executing SQL query: {str(e)}")

def display_channel_data(data):
    st.subheader("Channel Data")

    # Display channel information
    st.write(f"Channel ID: {data['_id']}")
    st.write(f"Channel Name: {data['Channel_name']}")
    st.write(f"Subscribers: {data['Subscribers']}")
    st.write(f"Total Videos: {data['Total_Videos']}")
    st.write(f"Playlist ID: {data['Playlist_id']}")

    # You can add more fields as needed

    # Display video data
    st.subheader("Video Data")

    for video in data['Videos']:
        st.write(f"Video ID: {video['Video_ID']}")
        st.write(f"Title: {video['Title']}")
        st.write(f"Likes: {video['Likes']}")
        st.write(f"Dislikes: {video['Dislikes']}")
        st.write(f"Views: {video['Views']}")
        st.write(f"Duration: {video.get('Duration', 'N/A')}")
        st.subheader("Comments")
        for i, comment in enumerate(video['Comments'], start=1):
            st.write(f"Comment {i}: {comment}")
        st.write("---")

if __name__ == "__main__":
    main()

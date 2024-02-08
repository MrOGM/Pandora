from flask import Flask, jsonify, request, send_file
from pytube import YouTube
from pytube import Playlist
from moviepy.editor import VideoFileClip
from flask_cors import CORS
import requests
import firebase_admin
from firebase_admin import credentials, storage
from firebase_admin import db
import os


app = Flask(__name__)

# Path to your Firebase service account key file
firebase_cred_path = "./pandora-qs325r-firebase-adminsdk-uulau-ead47b9736.json"


@app.route("/download", methods=["GET"])
def download():
    # Check if the 'url' parameter is provided in the query string
    youtube_url = request.args.get("url")
    if not youtube_url:

        # Return an error response if 'url' parameter is missing
        return jsonify({"error": "Missing 'url' parameter"}), 400

    # Return a success response with the provided 'url'
    else:
        YtDownloader(youtube_url)
        return jsonify({"success": youtube_url}), 200


# @app.route("/download", methods=["POST"])
# def Download1():
#     try:
#         data = request.get_json()
#         youtube_url = data.get("url")
#         # Check if the request data is in form-data or urlencoded format

#         if youtube_url:
#             return jsonify({"succes": youtube_url})
#         else:
#             return jsonify({"error": "Failed to download or extract MP3."}), 500

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


def upload_file_to_firebase(file_path, file_name):
    try:
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(
            cred, {"storageBucket": "pandora-qs325r.appspot.com"}
        )
        # Create a storage client
        bucket = storage.bucket()

        # Upload the file to Firebase Storage
        blob = bucket.blob(file_name)
        blob.upload_from_filename(file_path)

        print(f"File {file_name} uploaded to Firebase Storage")

        # Get the download URL of the uploaded file
        download_url = blob.generate_signed_url(
            expiration=3600
        )  # URL expiration time in seconds
        print("Download URL:", download_url)

        return download_url

    except Exception as e:
        print(f"Error uploading file to Firebase Storage: {e}")


# Deletes the MP4 video downloaded for extracting MP3
def delete_file(file_path, result):
    try:
        if result:
            os.remove(file_path)
            print(f"File deleted: {file_path}")
    except OSError as e:
        print(f"Error deleting file: {e}")


# Formats the title of youtube video to audio file name (takes out symbols and spaces)
def make_filename_safe(title):
    # Replace spaces with underscores
    title = title.replace(" ", "_")

    # Remove characters that might cause issues in filenames
    safe_chars = "".join(
        c if c.isalnum() or c in ("_", "-", ".") else "_" for c in title
    )
    # Replace additional characters that might cause issues
    safe_chars = (
        safe_chars.replace("|", "")
        .replace("/", "")
        .replace("\\", "")
        .replace(":", "")
        .replace("*", "")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
    )

    return safe_chars


# Creates an mp3 file from a mp4 file path
def extract_audio_from_mp4(input_file, output_file="output_audio.mp3"):
    try:
        # Load the video clip
        video_clip = VideoFileClip(input_file)

        # Extract the audio
        audio_clip = video_clip.audio

        output_file = make_filename_safe(output_file)
        # Save the audio as an MP3 file
        audio_clip.write_audiofile("downloadsAudio/" + output_file)

        print(f"Audio extraction complete. Saved as: {output_file}")

        video_clip.close()
        audio_clip.close()

        return True, output_file

    except Exception as e:
        print(f"Error: {e}")
        return False, output_file


# Creates an mp4 file from a youtube URL
def download_video(youtube_url, output_path="downloads"):
    try:
        # Create a YouTube object
        yt = YouTube(youtube_url)

        # Get the highest resolution stream
        video_stream = yt.streams.get_highest_resolution()

        # Print video details
        print(f"Downloading: {yt.title}")
        print(f"Resolution: {video_stream.resolution}")
        print(f"File size: {video_stream.filesize / (1024 * 1024):.2f} MB")

        # Set the output path and download the video
        downloaded_file_path = video_stream.download(output_path)

        print("Download complete!")
        return downloaded_file_path, yt.title

    except Exception as e:
        print(f"Error: {e}")


# # Creates an mp3 file from a youtube URL
# def YtDownloader(url):
#     downloaded_file_path, title = download_video(url)
#     result = extract_audio_from_mp4(downloaded_file_path, title + ".mp3")
#     delete_file(downloaded_file_path, result)


def YtDownloader(url):
    downloaded_file_path, title = download_video(url)
    result, safeName = extract_audio_from_mp4(downloaded_file_path, title + ".mp3")
    delete_file(downloaded_file_path, result)

    if result:
        mp3_file_path = f"downloadsAudio/{safeName}"
        print(mp3_file_path)
        mp3_file_name = f"{safeName}"
        print(mp3_file_name)
        download_url = upload_file_to_firebase(mp3_file_path, mp3_file_name)
        return download_url
    else:
        print("Failed to download or extract MP3")
        return None


# Creates an array of URLs from a youtube playlist URL
def get_playlist_info(youtube_url):
    try:
        playlist = Playlist(youtube_url)
        videosURL = []
        # Print information about the playlist
        print(f"Playlist Title: {playlist.title}")
        print(f"Number of videos in playlist: {len(playlist.video_urls)}")

        # Print details for each video in the playlist
        for index, video_url in enumerate(playlist.video_urls, start=1):
            videosURL.append(video_url)
            print(f"{index}. {video_url}")

        return videosURL
    except Exception as e:
        print(f"Error: {e}")


# Creates multiple mp3 files from a youtube playlist URL
def PlaylistDownloader(Playlist_url):
    urls = get_playlist_info(Playlist_url)
    for url in urls:
        YtDownloader(url)


# 2c0SFB7G0lXx036mNAIRaW6Vixr_7ErDRhZvm8PzXxwoLzkuv
if __name__ == "__main__":
    app.run(debug=True, port=5000)


# # Example usage
# youtube_url = "https://www.youtube.com/watch?v=gK5IKEgt7e4"

# ted = "https://www.youtube.com/watch?v=KVNh0JRm8Qw"
# bver = "https://www.youtube.com/watch?v=zUkR6chwtOo"


# YtDownloader(bver)
# YtDownloader(ted)
# # PlaylistDownloader(youtube_url)

import os
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx

# Define the output directory
OUTPUT_DIR = "processed_videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Add a logo to the center top of the video
def add_logo(video_clip, logo_path):
    logo = (
        VideoFileClip(logo_path)
        .resize(height=100)  # Resize logo to height of 100 pixels
        .set_position(("center", "top"))  # Place logo at center-top
        .set_duration(video_clip.duration)
    )
    return CompositeVideoClip([video_clip, logo])

# Slightly increase the brightness of the video
def adjust_brightness(video_clip):
    return video_clip.fx(vfx.colorx, 1.1)  # Slight increase in brightness

# Add audio distortion for copyright-free sound
def distort_audio(audio_clip, volume_factor=1.2):
    return audio_clip.volumex(volume_factor)

# Process a single video
def process_video(input_path, output_path, logo_path=None):
    # Load the video
    video = VideoFileClip(input_path)

    # Adjust brightness
    video = adjust_brightness(video)

    # Add logo if a logo path is provided
    if logo_path:
        video = add_logo(video, logo_path)

    # Add audio distortion
    if video.audio:
        distorted_audio = distort_audio(video.audio)
        video = video.set_audio(distorted_audio)

    # Write the processed video to the output
    video.write_videofile(output_path, codec="libx264", audio_codec="aac")

# Batch process videos in a folder
def process_videos(input_folder, logo_path=None):
    for filename in os.listdir(input_folder):
        if filename.endswith((".mp4", ".mov", ".avi")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(OUTPUT_DIR, f"processed_{filename}")
            process_video(input_path, output_path, logo_path)
            print(f"Processed: {filename}")

# Update the input folder and logo path as needed
INPUT_FOLDER = "downloaded_videos"
LOGO_PATH = "logo.png"  # Path to your logo file (center top)

if __name__ == "__main__":
    process_videos(INPUT_FOLDER, LOGO_PATH)

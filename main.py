import tkinter as tk
from tkinter import ttk, filedialog
from threading import Thread
import os
import yt_dlp
import subprocess

def get_short_links(channel_url, progress_var, progress_label_var):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlist_end': 100,
    }


    if '/@' in channel_url:

        channel_username = channel_url.split('/@')[1].split('/')[0]
        
        channel_url = f'https://www.youtube.com/@{channel_username}/shorts'
    else:

        channel_url = channel_url.split('/about')[0]  
        channel_url = channel_url.split('/community')[0]  
        channel_url = channel_url.split('/playlist')[0]  
        channel_url = channel_url.split('/playlists')[0]  
        channel_url = channel_url.split('/streams')[0]  
        channel_url = channel_url.split('/featured')[0]  
        channel_url = channel_url.split('/videos')[0]  

        channel_url += '/shorts'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        if 'entries' in result:
            video_ids = [entry['id'] for entry in result['entries']]
            short_links = [f'https://www.youtube.com/shorts/{video_id}' for video_id in video_ids]
            return short_links
        else:
            print("No videos found on the channel.")
            return []

def download_videos_from_links(links, output_path, progress_var, progress_label_var):
    total_links = len(links)
    for index, link in enumerate(links, start=1):
        link = link.strip()
        try:
            subprocess.run(['yt-dlp', '--quiet', '--output', os.path.join(output_path, '%(title)s.%(ext)s'), link], check=True)
            progress_label_var.set(f"Downloading video {index}/{total_links}: {link} - Downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading {link}: {e}")
            progress_label_var.set(f"Downloading video {index}/{total_links}: {link} - Failed to download: {e}")
        finally:
            progress_var.set(int((index / total_links) * 100))

def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_var.set(folder_selected)

def on_start_button_click(folder_var, channel_entry, progress_var, progress_label_var):
    output_directory = folder_var.get()
    os.makedirs(output_directory, exist_ok=True)

    channel_url = channel_entry.get()
    channel_name = channel_url.split('/')[-2]

    short_links = get_short_links(channel_url, progress_var, progress_label_var)
    if not short_links:
        return

    Thread(target=download_videos_from_links, args=(short_links, output_directory, progress_var, progress_label_var)).start()


root = tk.Tk()
root.title(" Shorts Bulk DL By Sewer")

style = ttk.Style()
style.theme_use("clam")
style.configure("TLabel", background="#2E2E2E", foreground="#FFFFFF")
style.configure("TButton", background="#555555", foreground="#FFFFFF")
style.configure("TEntry", fieldbackground="#555555", foreground="#FFFFFF")
style.configure("Horizontal.TProgressbar", troughcolor="#555555", bordercolor="#555555", background="#009688")
style.configure("TFrame", background="#2E2E2E")

main_frame = ttk.Frame(root, padding="10")
main_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

folder_label = ttk.Label(main_frame, text="Select the folder to save videos:")
folder_label.grid(column=0, row=0, sticky=tk.W, pady=10)

browse_button = ttk.Button(main_frame, text="Browse", command=browse_folder)
browse_button.grid(column=1, row=0, sticky=tk.W, pady=10)

folder_var = tk.StringVar()
folder_entry = ttk.Entry(main_frame, textvariable=folder_var, state="readonly", width=50)
folder_entry.grid(column=2, row=0, sticky=(tk.W, tk.E), pady=10)

channel_label = ttk.Label(main_frame, text="Enter the YouTube channel URL:")
channel_label.grid(column=0, row=1, sticky=tk.W, pady=10)

channel_entry = ttk.Entry(main_frame, width=50)
channel_entry.grid(column=1, row=1, columnspan=2, sticky=(tk.W, tk.E), pady=10)

start_button = ttk.Button(main_frame, text="Start Download", command=lambda: on_start_button_click(folder_var, channel_entry, progress_var, progress_label_var))
start_button.grid(column=0, row=2, columnspan=3, pady=10)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(main_frame, orient="horizontal", mode="determinate", variable=progress_var, style="Horizontal.TProgressbar")
progress_bar.grid(column=0, row=3, columnspan=3, pady=10, sticky=(tk.W, tk.E))

progress_label_var = tk.StringVar()
progress_label = ttk.Label(main_frame, textvariable=progress_label_var)
progress_label.grid(column=0, row=4, columnspan=3, pady=5, sticky=(tk.W, tk.E))

root.mainloop()

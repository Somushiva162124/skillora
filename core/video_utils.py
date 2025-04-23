import logging
from moviepy.editor import VideoFileClip

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

def process_video(input_path, output_path="output.mp4"):
    try:
        # Load video
        clip = VideoFileClip(input_path)
        
        # Preview video (optional, remove if not needed)
        # clip.preview(fps=24, preview=False)
        
        # Save processed video
        clip.write_videofile(output_path, threads=False)
        
        logging.info(f"Video processed successfully: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Error processing video: {e}")
        return None

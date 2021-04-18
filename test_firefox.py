from streamstock.uploader import YoutubeSeleniumUploader
from pathlib import Path


# video_path = '/tmp/tmpsn2j4k7p/compilation.mp4'
# metadata_path = '/home/oem/Streams/streamstock/metadata.json'

# current_working_dir = str(Path.cwd())

# uploader = YouTubeUploader(video_path, metadata_path, browser)
# was_video_uploaded, video_id = uploader.upload()
# print(was_video_uploaded)

video_path = '/tmp/tmpsn2j4k7p/compilation.mp4'
cookie_path = '/home/oem/Streams/streamstock'
extension_path = '/home/oem/Streams/streamstock'
# extension_path = '/tmp'

uploader = YoutubeSeleniumUploader(cookie_path, extension_path)
uploader.upload(video_path, title='Test test')




from moviepy.video import VideoClip
import tempfile
import logging


logger = logging.getLogger(__name__)


def build(clip: VideoClip, name='compilation.mp4'):
    tmp_dir = tempfile.mkdtemp()
    filename = name
    output = '{}/{}'.format(tmp_dir, filename)

    logger.debug('Begin processing of compilation')
    try:
        clip.write_videofile(output)
    except IndexError:
        clip = clip.subclip(t_end=(clip.duration - 1.0 / clip.fps))
        clip.write_videofile(output)

    logger.debug('Processing ended. Output file {}'.format(output))

    return output


    # try:
    #     final_clip.write_videofile(save_path,  threads=6, logger=None)
    #     logger.info("Saved .mp4 without Exception at {}".format(save_path))
    # except IndexError:
    #     # Short by one frame, so get rid on the last frame:
    #     final_clip = final_clip.subclip(t_end=(clip.duration - 1.0/final_clip.fps))
    #     final_clip.write_videofile(save_path, threads=6, logger=None)
    #     logger.info("Saved .mp4 after Exception at {}".format(save_path))
    # except Exception as e:
    #     logger.warning("Exception {} was raised!!".format(e))
from streamstock_common.api_models import const as api_consts
from streamstock_common.api_models import Model, Compilation, Project, PipelineSettings
from streamstock_common.mq import MQConsumer
from streamstock.helpers.files import create_file, create_folder
from streamstock.pipeline import PipelineBuilder
from streamstock.configs import config
from streamstock import const
from streamstock_common import const as mq_const
import json
import pickle
import vosk
import logging
import sys


def main_process(body):
    compilation_id = body[api_consts.ID]
    compilation = Compilation.get_by_id(compilation_id)

    if compilation[api_consts.COMPILATION_STATUS] == api_consts.COMPILATION_STATUS_PAUSE:
        return

    project = Project.get_by_id(compilation[api_consts.PROJECT])

    pipeline_settings = PipelineSettings({})
    compilation_pipeline_settings = PipelineSettings.get_by_id(compilation[api_consts.PIPELINE_SETTINGS])
    project_pipeline_settings = PipelineSettings.get_by_id(project[api_consts.PIPELINE_SETTINGS])

    pipeline_settings.update(project_pipeline_settings)
    pipeline_settings.update(compilation_pipeline_settings)
    pipeline_settings[api_consts.COMPILATION] = compilation

    pipeline_settings[api_consts.COMPILATION_SOURCE_LOCATION] = compilation[api_consts.COMPILATION_SOURCE_LOCATION]

    if pipeline_settings.get(api_consts.YOUTUBE_UPLOADER_CLIENT_SECRETS):
        client_secrets = create_file(pipeline_settings[api_consts.YOUTUBE_UPLOADER_CLIENT_SECRETS])
        pipeline_settings[api_consts.YOUTUBE_UPLOADER_CLIENT_SECRETS] = client_secrets

    if pipeline_settings.get(api_consts.YOUTUBE_UPLOADER_CREDENTIALS):
        credentials = create_file(pipeline_settings[api_consts.YOUTUBE_UPLOADER_CREDENTIALS])
        pipeline_settings[api_consts.YOUTUBE_UPLOADER_CREDENTIALS] = credentials

    if pipeline_settings[api_consts.UPLOADER_TYPE] == api_consts.UPLOADER_TYPE_YOUTUBE_SELENIUM:
        tmp_folder = create_folder()
        cookie_text = pipeline_settings[api_consts.YOUTUBE_SELENIUM_UPLOADER_COOKIE]
        json_data = json.loads(cookie_text)
        data = pickle.dumps(json_data)
        create_file(data, name=const.YOUTUBE_COOKIE_FILE, dir=tmp_folder)

        pipeline_settings[api_consts.YOUTUBE_SELENIUM_UPLOADER_COOKIES_FOLDER] = tmp_folder
        pipeline_settings[api_consts.YOUTUBE_SELENIUM_UPLOADER_EXTENSIONS_FOLDER] = tmp_folder

    pipeline_builder = PipelineBuilder()
    pipeline = pipeline_builder.build(pipeline_settings)

    compilation[api_consts.COMPILATION_STATUS] = api_consts.COMPILATION_STATUS_PROGRESS
    compilation.save()

    pipeline.produce()

    compilation[api_consts.COMPILATION_STATUS] = api_consts.COMPILATION_STATUS_READY
    compilation.save()


def init():
    logging.basicConfig(level=logging.WARNING,
                        format='[%(asctime)s] %(levelname)s %(name)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.DEBUG)
    vosk.SetLogLevel(-1)
    sys.setrecursionlimit(sys.getrecursionlimit() * 20)
    logger.debug('Python recursion limit {}'.format(sys.getrecursionlimit()))

    Model.DB_URL = config.STREAMSTOCK_API

    consumer = MQConsumer(config.MQ_HOST, config.MQ_PORT, const.MQ_TASK_CONSUMER)
    consumer.add_callback(main_process, mq_const.COMPILATION_QUEUE)
    consumer.start_infinity_consuming()

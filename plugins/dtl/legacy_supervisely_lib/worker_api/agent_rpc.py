# coding: utf-8

import cv2
import numpy as np

from .chunking import load_to_memory_chunked_image, load_to_memory_chunked
from ..worker_proto import worker_api_pb2 as api_proto
from ..utils.general_utils import batched


class SimpleCache:
    def __init__(self, item_cnt_limit):
        self.dct = {}
        self.item_cnt_limit = item_cnt_limit

    def get(self, key):
        return self.dct.get(key)

    def add(self, key, value):
        if len(self.dct) >= self.item_cnt_limit:
            self.dct = {}  # specially developed method for smart caching
        self.dct[key] = value


def download_image_from_remote(agent_api, image_hash, src_node_token, logger):
    resp = agent_api.get_stream_with_data(
        'DownloadImages',
        api_proto.ChunkImage,
        api_proto.ImagesHashes(images_hashes=[image_hash], src_node_token=src_node_token)
    )
    b_data = load_to_memory_chunked_image(resp)
    logger.trace('Image downloaded',
                 extra={'image_hash': image_hash, 'src_node_token': src_node_token, 'len': len(b_data)})
    return b_data


def download_data_from_remote(agent_api, req_id, logger):
    resp = agent_api.get_stream_with_data('GetGeneralEventData', api_proto.Chunk, api_proto.Empty(),
                                          addit_headers={'x-request-id': req_id})
    b_data = load_to_memory_chunked(resp)
    logger.trace('Data downloaded', extra={'request_id': req_id, 'len': len(b_data)})
    return b_data


def send_from_memory_generator(out_bytes, chunk_size):
    for bytes_chunk in batched(out_bytes, chunk_size):
        yield api_proto.Chunk(buffer=bytes_chunk, total_size=len(out_bytes))


def decode_image(img_data_packed):
    img_data_packed = np.frombuffer(img_data_packed, dtype=np.uint8)
    img_np = cv2.imdecode(img_data_packed, cv2.IMREAD_UNCHANGED).astype(np.uint8)
    if not img_np.size:
        raise RuntimeError('Unable to decode input image.')
    img_data = img_np[:, :, ::-1]  # BGR 2 RGB
    return img_data

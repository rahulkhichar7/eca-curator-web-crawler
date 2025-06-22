import os
from warcio.warcwriter import WARCWriter
from warcio.statusandheaders import StatusAndHeaders
from io import BytesIO
from config import WARC_DIR, FILES_DIR, WARC_SIZE_LIMIT

def visited_writer(visited_queue):
    file_path = os.path.join(FILES_DIR, 'visited.txt')
    with open(file_path, 'w') as f:
        while True:
            url = visited_queue.get()
            if url is None:
                break
            f.write(url + '\n')
            f.flush()

def timeouts_writer(timeouts_queue):
    file_path = os.path.join(FILES_DIR, 'timeouts.txt')
    with open(file_path, 'w') as f:
        while True:
            url = timeouts_queue.get()
            if url is None:
                break
            f.write(url + '\n')
            f.flush()

def warc_writer_process(warc_queue):
    warc_index = 0
    current_size = 0
    file_path = os.path.join(WARC_DIR, f"global_{warc_index}.warc.gz")
    f = open(file_path, 'wb')
    writer = WARCWriter(f, gzip=True)
    while True:
        record = warc_queue.get()
        if record is None:
            break
        url, content, headers, status = record
        if current_size >= WARC_SIZE_LIMIT:
            f.close()
            warc_index += 1
            file_path = os.path.join(WARC_DIR, f"global_{warc_index}.warc.gz")
            f = open(file_path, 'wb')
            writer = WARCWriter(f, gzip=True)
            current_size = 0
        http_headers = StatusAndHeaders(
            f"{status} OK" if status == 200 else str(status),
            list(headers.items()),
            protocol='HTTP/1.1'
        )
        warc_headers = {
            "WARC-Identified-Payload-Type": headers.get('content-type', '').split(';')[0]
        }
        warc_record = writer.create_warc_record(
            uri=url,
            record_type='response',
            payload=BytesIO(content),
            http_headers=http_headers,
            warc_headers_dict=warc_headers
        )
        writer.write_record(warc_record)
        current_size += len(content)
    f.close()

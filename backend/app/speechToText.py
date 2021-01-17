from vosk import Model, KaldiRecognizer, SetLogLevel
import numpy as np
import os
import websockets
import asyncio
from flask_sse import sse
import math

transcription = []

def process_chunk(raw_data, length):
    data = eval(raw_data)
    results = data.get('result')
    if results:
        transcription.extend(results)
        last = results[-1]
        time = last['end']
        sse.publish({
            "seconds": time,
            "fraction": round((math.ceil(time) / length), 4) 
            },
            type='processing'
        )
        print(f'Processed {time} seconds')


async def transcribe(data, fs):
    length = math.ceil(len(data) / fs);
    CHUNK_SIZE = 4000

    print("Processing audio...")
    async with websockets.connect(os.environ.get('STT_URL')) as websocket:
        for chunk_idx in range(0, len(data), CHUNK_SIZE):
            chunk = data[chunk_idx:chunk_idx+CHUNK_SIZE]
            await websocket.send(chunk.tobytes())
            process_chunk(await websocket.recv(), length)

        await websocket.send('{"eof" : 1}')
        process_chunk(await websocket.recv(), length)
        print("Finished")


def get_transcription(data, fs):
    asyncio.run(
        transcribe(data, fs),
    )

    print('Transcription is ready')

    return transcription
import os
import torch
import sounddevice as sd
import time

print('Initializing TTS Model...')
device = torch.device('cpu')
local_file = 'torch_model/model.pt'

model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
model.to(device)

sample_rate = 48000
speaker = 'en_10'  # 40
put_accent = True
put_yo = True


def va_speak(what: str):
    audio = model.apply_tts(text=what + "..",
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)

    sd.play(audio, sample_rate * 1.05)
    time.sleep((len(audio) / sample_rate) + 0.5)
    sd.stop()


print('TTS Model Initialized')

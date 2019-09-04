#!/bin/python3

import argparse
import soundfile
from scipy.signal import spectrogram
import numpy as np
import matplotlib.pyplot as plt

PARSER = argparse.ArgumentParser(description='Script that generates a png spectrogram from an audio wav file')
PARSER.add_argument('audio_file', help='Filepath of the input audio wav file')
PARSER.add_argument('--tile-levels', '-tl', type=int, default=1, help='Number of wanted tile levels (default 1)')
PARSER.add_argument('output', nargs='?', help='Desired ouput filepath')

def gen_spectro(data, sample_rate, output_file):
    nfft = 512
    winSize = 512
    overlapInPercent = 0.9
    cmap_color = 'Greys'

    # Calculating Spectrogram
    fPSD, _, vPSD = spectrogram(
        x=data,
        fs=sample_rate,
        window='hann',
        nperseg=winSize,
        noverlap=winSize * overlapInPercent,
        nfft=nfft,
        detrend=False,
        return_onesided=True,
        axis=-1,
        mode='psd',
        scaling='density'
    )

    # Resizing
    yStep = sample_rate / (2 * 256); yEnd = sample_rate / 2 + 1 / 256
    x, y = np.mgrid[slice(0, vPSD.shape[1] / 60 , 1 / 60), slice(0, yEnd, yStep)]
    z = 10 * np.log10(np.array(vPSD.T))

    my_dpi = 100
    factX = 1.3
    factY = 1.3

    fig = plt.figure(figsize=(factX * 1800/my_dpi, factY * 512/my_dpi), dpi=my_dpi)
    plt.pcolormesh(x, y, z, cmap=cmap_color)
    plt.axis('off')
    fig.axes[0].get_xaxis().set_visible(False)
    fig.axes[0].get_yaxis().set_visible(False)

    # Savefig
    plt.savefig(output_file, bbox_inches='tight', pad_inches = 0, dpi=my_dpi)
    plt.close()

def gen_tiles(tile_levels, data, sample_rate, output):
    duration = len(data) / int(sample_rate)
    for level in range(0, tile_levels):
        tile_duration = duration / 2**level
        for tile in range(0, 2**level):
            start = tile * tile_duration
            end = start + tile_duration
            output_file = f"{output[:-4]}_{start}_{end}.png"
            sample_data = data[int(start * sample_rate):int(end * sample_rate)]
            gen_spectro(sample_data, sample_rate, output_file)

if __name__ == '__main__':

    args = PARSER.parse_args()
    
    if args.audio_file[-4:].lower() != '.wav':
        raise ValueError('Input audio file should have .wav extension')
    
    if args.output is None:
        args.output = args.audio_file[:-4] + '.png'

    data, sample_rate = soundfile.read(args.audio_file)

    if args.tile_levels == 1:
        gen_spectro(data, sample_rate, args.output)
    else:
        gen_tiles(args.tile_levels, data, sample_rate, args.output)

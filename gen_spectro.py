#!/bin/python3

import argparse
import soundfile
from scipy.signal import spectrogram
import numpy as np
import matplotlib.pyplot as plt

PARSER = argparse.ArgumentParser(description='Script that generates a png spectrogram from an audio wav file')
PARSER.add_argument('audio_file', help='Filepath of the input audio wav file')
PARSER.add_argument('output', nargs='?', help='Desired ouput filepath')

def gen_spectro(input_file, output_file):
    nfft = 512
    winSize = 512
    overlapInPercent = 0.9
    cmap_color = 'jet'

    sig, fs = soundfile.read(input_file)

    fPSD, _, vPSD = spectrogram(
        x=sig,
        fs=fs,
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

    yStep = fs / (2 * 256); yEnd = fs / 2 + 1 / 256
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
    plt.savefig(output_file, bbox_inches='tight', pad_inches = 0, dpi=my_dpi)
    plt.close()

if __name__ == '__main__':

    args = PARSER.parse_args()
    
    if args.audio_file[-4:] != '.wav':
        raise ValueError('Input audio file should have .wav extension')
    
    if args.output is None:
        args.output = args.audio_file[:-4] + '.png'

    gen_spectro(args.audio_file, args.output)

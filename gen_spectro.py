#!/bin/python3

import argparse
import soundfile
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


PARSER = argparse.ArgumentParser(description='Script that generates a png spectrogram from an audio wav file')
PARSER.add_argument('audio_file', help='Filepath of the input audio wav file')
PARSER.add_argument('--nfft', '-n', type=int, default=4096, help='NFFT parameter for spectrogram')
PARSER.add_argument('--win_size', '-w', type=int, default=4096, help='Window size parameter for spectrogram')
PARSER.add_argument('--overlap', '-o', type=float, default=0, help='Overlap parameter (in percent) for spectrogram')
PARSER.add_argument('--min_freq', '-minf', type=float, default=None, help='Maximum frequency for spectrogram')
PARSER.add_argument('--max_freq', '-maxf', type=float, default=None, help='Minimum frequency for spectrogram')
PARSER.add_argument('--cmap_color', '-c', type=str, default='plasma', help='CMAP color parameter for spectrogram (cf matplotlib)')
PARSER.add_argument('--tile-levels', '-tl', type=int, default=1, help='Number of wanted tile levels (default 1)')
PARSER.add_argument('output', nargs='?', help='Desired ouput filepath')


class SpectroGenerator:
    def __init__(self, nfft, win_size, pct_overlap, cmap_color, min_freq=None, max_freq=None):
        self.nfft = nfft
        self.win_size = win_size
        self.pct_overlap = pct_overlap
        self.cmap_color = cmap_color
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.max_w = 1

    def gen_spectro(self, data, sample_rate, output_file, main_ref=False, window_type='hamming'):
        noverlap = int(self.win_size * self.pct_overlap/100)
        nperseg = self.win_size
        nstep = nperseg - noverlap

        win = signal.get_window(window_type, nperseg)

        x = np.asarray(data)
        shape = x.shape[:-1] + ((x.shape[-1] - noverlap) // nstep, nperseg)
        strides = x.strides[:-1] + (nstep * x.strides[-1], x.strides[-1])
        xinprewin = np.lib.stride_tricks.as_strided(x, shape=shape, strides=strides)
        xinwin = win * xinprewin

        result = xinwin.real
        func = np.fft.rfft
        fftraw = func(result, n=self.nfft)

        scale_psd = 1.0 / (sample_rate * (win * win).sum())
        vPSD_noBB = np.conjugate(fftraw) * fftraw
        vPSD_noBB *= scale_psd

        if self.nfft % 2:
            vPSD_noBB[..., 1:] *= 2
        else:
            vPSD_noBB[..., 1:-1] *= 2

        spectro = vPSD_noBB.real
        segment_times = np.arange(nperseg / 2, x.shape[-1] - nperseg / 2 + 1, nperseg - noverlap) / float(sample_rate)
        frequencies = np.fft.rfftfreq(self.nfft, 1 / sample_rate)
        spectro = spectro.transpose()

        # Setting self.max_w and normalising spectro as needed
        if main_ref:
            self.max_w = np.amax(spectro)
        spectro = spectro / self.max_w


        # Restricting spectro frenquencies
        freqs_to_keep = (frequencies == frequencies)
        if self.min_freq:
            freqs_to_keep *= self.min_freq <= frequencies
        if self.max_freq:
            freqs_to_keep *= frequencies <= self.max_freq
        frequencies = frequencies[freqs_to_keep]
        spectro = spectro[freqs_to_keep, :]

        # Switching to log spectrogram
        log_spectro = 10 * np.log10(np.array(spectro))

        # Ploting spectrogram
        my_dpi = 100
        fact_x = 1.3
        fact_y = 1.3
        fig = plt.figure(figsize=(fact_x * 1800 / my_dpi, fact_y * 512 / my_dpi), dpi=my_dpi)
        plt.pcolormesh(segment_times, frequencies, log_spectro, cmap=self.cmap_color)
        plt.clim([-35,0])
        plt.axis('off')
        fig.axes[0].get_xaxis().set_visible(False)
        fig.axes[0].get_yaxis().set_visible(False)

        # Saving spectrogram plot to file
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=my_dpi)
        plt.close()

def gen_tiles(spectro_generator, tile_levels, data, sample_rate, output):
    """Generates multiple spectrograms for zoom tiling"""
    duration = len(data) / int(sample_rate)
    for level in range(0, tile_levels):
        zoom_level = 2**level
        tile_duration = duration / zoom_level
        for tile in range(0, zoom_level):
            start = tile * tile_duration
            end = start + tile_duration
            output_file = f"{output[:-4]}_{zoom_level}_{tile}.png"
            sample_data = data[int(start * sample_rate):int(end * sample_rate)]
            spectro_generator.gen_spectro(sample_data, sample_rate, output_file, level == 0)

def main():
    """Main script function"""
    args = PARSER.parse_args()

    if args.audio_file[-4:].lower() != '.wav':
        raise ValueError('Input audio file should have .wav extension')

    if args.output is None:
        args.output = args.audio_file[:-4] + '.png'

    data, sample_rate = soundfile.read(args.audio_file)

    spectro_generator = SpectroGenerator(
        args.nfft,
        args.win_size,
        args.overlap,
        args.cmap_color,
        args.min_freq,
        args.max_freq
    )

    if args.tile_levels == 1:
        spectro_generator.gen_spectro(data, sample_rate, args.output,args.tile_levels)
    else:
        gen_tiles(spectro_generator, args.tile_levels, data, sample_rate, args.output)

if __name__ == '__main__':
    main()

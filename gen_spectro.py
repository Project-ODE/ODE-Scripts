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
PARSER.add_argument('--freq_plot_range', '-fpr', type=str, default=None, help='Frequency range (min:max) for spectrogram plot')
PARSER.add_argument('--freq_dyn_range', '-fdr', type=str, default=None, help='Frequency range (min:max) for spectrogram dynamic range')
PARSER.add_argument('--color_val_range', '-cvr', type=str, default=None, help='Set the color norm limit range (min:max) for image scaling')
PARSER.add_argument('--cmap_color', '-c', type=str, default='Greys', help='CMAP color parameter for spectrogram (cf matplotlib)')
PARSER.add_argument('--tile-levels', '-tl', type=int, default=1, help='Number of wanted tile levels (default 1)')
PARSER.add_argument('--butter-order', '-b', type=int, default=5, help='Order level for Butterworth highpass digital filter')
PARSER.add_argument('--max-bgw', '-mw', type=float, default=None, help='Fix value for spectro background highlighting')
PARSER.add_argument('output', nargs='?', help='Desired ouput filepath')


class Range:
    def __init__(self, string=None, min=None, max=None):
        self.min = None
        self.max = None
        if string != None:
            format_prompt = 'Range input should have MIN:MAX, or MIN: or :MAX format'
            if type(string) == str and string != '':
                if string.startswith(':'):
                    self.max = float(string[1:])
                elif string.endswith(':'):
                    self.min = float(string[:-1])
                else:
                    string_split = string.split(':')
                    if len(string_split) != 2:
                        raise ValueError(format_prompt)
                    self.min = float(string_split[0])
                    self.max = float(string_split[1])
            else:
                raise ValueError(format_prompt)
        else:
            if min:
                self.min = min
            if max:
                self.max = max
        if self.min != None and self.max != None:
            if self.min > self.max:
                raise ValueError('Max value should be bigger than min value')

    def __repr__(self):
        return f"Range({self.min}:{self.max})"

class SpectroGenerator:
    def __init__(self, nfft, win_size, pct_overlap, cmap_color, freq_plot_range=None, freq_dyn_range=None, color_val_range=None):
        self.nfft = nfft
        self.win_size = win_size
        self.pct_overlap = pct_overlap
        self.cmap_color = cmap_color
        self.min_freq_plot = freq_plot_range.min if freq_plot_range else None
        self.max_freq_plot = freq_plot_range.max if freq_plot_range else None
        self.min_freq_dyn = freq_dyn_range.min if freq_dyn_range else None
        self.max_freq_dyn = freq_dyn_range.max if freq_dyn_range else None
        self.min_color_val = color_val_range.min if color_val_range else None
        self.max_color_val = color_val_range.max if color_val_range else None
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

        # Restricting spectro frenquencies
        freqs_to_keep = (frequencies == frequencies)
        if self.min_freq_plot:
            freqs_to_keep *= self.min_freq_plot <= frequencies
        if self.max_freq_plot:
            freqs_to_keep *= frequencies <= self.max_freq_plot
        frequencies = frequencies[freqs_to_keep]
        spectro = spectro[freqs_to_keep, :]

        # Setting self.max_w and normalising spectro as needed
        if main_ref:
            # Restricting spectro frenquencies for dynamic range
            freqs_to_keep = (frequencies == frequencies)
            if self.min_freq_dyn:
                freqs_to_keep *= self.min_freq_dyn <= frequencies
            if self.max_freq_dyn:
                freqs_to_keep *= frequencies <= self.max_freq_dyn
            self.max_w = np.amax(spectro[freqs_to_keep, :])
        spectro = spectro / self.max_w

        # Switching to log spectrogram
        log_spectro = 10 * np.log10(np.array(spectro))

        # Ploting spectrogram
        my_dpi = 100
        fact_x = 1.3
        fact_y = 1.3
        fig = plt.figure(figsize=(fact_x * 1800 / my_dpi, fact_y * 512 / my_dpi), dpi=my_dpi)
        plt.pcolormesh(segment_times, frequencies, log_spectro, cmap=self.cmap_color)
        plt.clim(vmin=self.min_color_val, vmax=self.max_color_val)
        plt.axis('off')
        fig.axes[0].get_xaxis().set_visible(False)
        fig.axes[0].get_yaxis().set_visible(False)

        # Saving spectrogram plot to file
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0, dpi=my_dpi)
        plt.close()

    def gen_tiles(self, tile_levels, data, sample_rate, output, equalize_spectro=True):
        """Generates multiple spectrograms for zoom tiling"""
        duration = len(data) / int(sample_rate)
        for level in range(0, tile_levels):
            zoom_level = 2**level
            tile_duration = duration / zoom_level
            main_ref = equalize_spectro and (level == 0)
            for tile in range(0, zoom_level):
                start = tile * tile_duration
                end = start + tile_duration
                output_file = f"{output[:-4]}_{zoom_level}_{tile}.png"
                sample_data = data[int(start * sample_rate):int(end * sample_rate)]
                self.gen_spectro(sample_data, sample_rate, output_file, main_ref=main_ref)

def butter_highpass_filter(data, cutoff, sample_rate, order):
    """Applies highpass (above cutoff) Butterworth digital filter of given order on data"""
    normal_cutoff = cutoff / (0.5 * sample_rate)
    numerator, denominator = signal.butter(order, normal_cutoff, btype='high', analog=False)
    return signal.filtfilt(numerator, denominator, data)

def main():
    """Main script function"""
    args = PARSER.parse_args()

    if args.audio_file[-4:].lower() != '.wav':
        raise ValueError('Input audio file should have .wav extension')

    if args.output is None:
        args.output = args.audio_file[:-4] + '.png'

    data, sample_rate = soundfile.read(args.audio_file)

    freq_plot_range = Range(args.freq_plot_range) if args.freq_plot_range else None
    freq_dyn_range = Range(args.freq_dyn_range) if args.freq_dyn_range else None
    color_val_range = Range(args.color_val_range) if args.color_val_range else None

    # Applying highpass Butterworth digital filter
    butter_cutoff = 0
    if freq_dyn_range and freq_dyn_range.min:
        butter_cutoff = freq_dyn_range.min
    elif freq_plot_range and freq_plot_range.min:
        butter_cutoff = freq_plot_range.min
    data = butter_highpass_filter(data, butter_cutoff, sample_rate, args.butter_order)

    spectro_generator = SpectroGenerator(
        args.nfft,
        args.win_size,
        args.overlap,
        args.cmap_color,
        freq_plot_range,
        freq_dyn_range,
        color_val_range
    )

    equalize_spectro = False
    if args.max_bgw:
        spectro_generator.max_w = args.max_bgw
        equalize_spectro = True

    if args.tile_levels == 1:
        spectro_generator.gen_spectro(data, sample_rate, args.output)
    else:
        spectro_generator.gen_tiles(args.tile_levels, data, sample_rate, args.output, equalize_spectro)

if __name__ == '__main__':
    main()

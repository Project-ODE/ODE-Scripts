require "date"

header = "dataset_name, filename, audio_start, audio_end, audio_sample_rate_khz\n"
dataset_name = "Glider SPAms 2019"

files = `ls *.wav`.split

seconds = 1.0/24/60/60
tformat = "%Y-%m-%d %H:%M:%S"

res = header + files.map do |file|
  start_dt = DateTime.strptime(file.split("_")[2..3].join, "%d%m%y%H%M%S")
  duration = `soxi -D #{file}`.to_i
  end_dt = start_dt + duration * seconds
  asr = `soxi -r  #{file}`.to_i/1000.0
  [dataset_name, file, start_dt.strftime(tformat), end_dt.strftime(tformat), asr].join(", ")
end.join("\n")

File.write("dataset_files.csv", res)

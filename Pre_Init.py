import pandas as pd

import re

import subprocess

import os

from pathlib import Path

from DataMethods import makeOutDir

########################################################################################################################

def video_duration(path_to_recordings, framerate=120):
    """
    obtains the duration of each recording within the recordings directory
    :param path_to_recordings: str, path to the recordings directory
    :param framerate: int, frames per second that the recording was shot at
    :returns num_frames_lst: list, num_frames of each recording in sorted order
    :returns h_readable_lst: list, human-readable time length of recording in sorted order
    """
    num_frames_lst = []
    h_readable_lst = []
    for file in sorted(Path(path_to_recordings).iterdir()):
        if file.suffix == '.mp4':
            # for each file in the directory, extract its length in seconds through ffprobe and then through regex
            secs = subprocess.check_output(
                f'ffprobe -v error -select_streams v:0 -show_entries stream=duration '
                f'-of default=noprint_wrappers=1:nokey=1 "{str(file)}"',
                shell=True).decode()
            time_search_str = "\d+.\d+"
            secs = float(re.search(time_search_str, secs)[0])

            # convert to human-readable format
            hours = secs // 3600
            min_left = (secs - hours * 3600) // 60
            secs_left = (secs - hours * 3600 - min_left * 60)
            h_read_time = "%i h %i min %i sec" % (hours, min_left, secs_left)
            h_readable_lst.append(h_read_time)

            #
            frames_in_chunk = secs * framerate + 2
            num_frames_lst.append(int(frames_in_chunk))
    return num_frames_lst, h_readable_lst


def get_vid_paths(path_to_recordings):
    """
    list of sorted mp4 files from inputted stack directory

    :param path_to_recordings: str, directory of mp4 video recordings
    :return: sorted list of recording file paths
    """
    path_to_recordings = Path(path_to_recordings)
    files = [file for file in sorted(path_to_recordings.iterdir()) if file.suffix == '.mp4']

    return files


def get_init_stack(path_to_recordings, HomeDir, selected_rec_num, minutes, seconds, framerate=120):
    """
    convert chosen length of chosen video to images and save out initialization stack
    :param path_to_recordings: str, directory of mp4 video recordings
    :param HomeDir: str, path to home directory  (typically name of jelly)
    :param selected_rec_num: int, recording number to pull the initialization stack from
    :param seconds: tuple, (start second, end second) to pull initialization stack from
    :param framerate: int, frames per second that the recording was shot at
    :return None: creates the initialization stack
    """
    # make initialization out directory
    pathOfInitializationStack = makeOutDir(Path(HomeDir), "Initialization_Stack")

    # choose the video to obtain the initialization stack from
    selected_vid_path = str(get_vid_paths(path_to_recordings)[selected_rec_num - 1])

    print("The video path chosen is %s"%selected_vid_path)

    # run FFMPEG to obtain the initialization stack in the chosen time frame
    os.system("ffmpeg -i %s -r %i -q 0 -ss 00:%s:%s -t 00:%s:%s  %s/%%06d.jpg" % (selected_vid_path, framerate,
                                                                                  minutes[0], seconds[0],
                                                                                       minutes[1], seconds[1],
                                                                                       pathOfInitializationStack)
              )

def frame(time_1, time_2, initial_frame, observed_total_frame):
    d = {'time': [time_1, time_2]}
    df = pd.DataFrame(data=d)
    specified_format = '%Y%m%d_%H%M'
    df['time'] = pd.to_datetime(df['time'], format=specified_format)
    time_diff = df['time'][1]-df['time'][0]
    time_diff = time_diff.total_seconds()
    time_diff = int(time_diff)
    expected_total_frame = time_diff*120
    frame_diff = expected_total_frame - observed_total_frame
    actual_frame = initial_frame + frame_diff
    return actual_frame

def make_preinit_DF(HomeDir, path_to_recordings, framerate=120, savio_additional_subdir=None,
                    savio_root_path='global/scratch/users/zhiqinchen'):
    """
    make pre-initialization Pandas dataframe and save out as csv file
    :param HomeDir: str, path to home directory  (typically name of jelly)
    :param path_to_recordings: str, directory of mp4 video recordings
    :param framerate: int, frames per second that the recording was shot at
    :param savio_additional_subdir: str, additional subdirectory that files will be located in on Savio
    :param savio_root_path: str, path of scratch directory files will be located in on Savio
    :returns None: makes pre-init dataframe and saves out as csv
    """
    # get number of recordings in folder
    HomeDir_Path = Path(HomeDir)

    # get lists for the pre-initialization dataframe
    recording_name_lst = ['%s' % (HomeDir_Path.stem) for file in sorted(Path(path_to_recordings).iterdir()) if
                          file.suffix == '.mp4']
    recording_dir_path_lst = ['/%s/%s' % (savio_root_path, HomeDir_Path.stem) for file in
                              sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']
    chunk_name_lst = [file.stem for file in sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']
    num_frames_in_chunk_lst, h_readable_time_lst = video_duration(path_to_recordings, framerate)
    frame_rate_lst = [framerate for file in sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']
    savio_chunk_path_lst = ['/tmp/Image_Stacks/%s' % (file.stem)
                            for file in sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']

    # in the case that there are additional subdirectories on savio
    if savio_additional_subdir is not None:
        chunk_name_lst = [file.stem for file in sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']

        recording_dir_path_lst = ['/%s/%s/%s' % (savio_root_path, savio_additional_subdir, HomeDir_Path.stem) for file in
                                  sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']
        savio_chunk_path_lst = ['/tmp/Image_Stacks/%s' % (file.stem)
                                for file in sorted(Path(path_to_recordings).iterdir()) if file.suffix == '.mp4']

    # make the actual pre-initialization df
    pre_init_DF = pd.DataFrame({'RecordingName': recording_name_lst,
                                'RecordingDirPath': recording_dir_path_lst,
                                'ChunkName': chunk_name_lst,
                                'SavioChunkPath': savio_chunk_path_lst,
                                'NumFramesInChunk': num_frames_in_chunk_lst,
                                'RecordingDuration': h_readable_time_lst,
                                'FrameRate': frame_rate_lst})

    NumFramesInChunk_initial = pre_init_DF['NumFramesInChunk']
    date = [re.search('\d+\_\d+', i).group(0) for i in pre_init_DF['ChunkName']]
    pre_init_DF['date'] = date
    for i in range(len(pre_init_DF)-1):
        date = pre_init_DF['date'][i]
        next_date = pre_init_DF['date'][i+1]
        if date != next_date:
            observed_total_frame = sum(pre_init_DF.loc[(pre_init_DF['date'])==date]['NumFramesInChunk'])
            actual_frame = frame(date, next_date, pre_init_DF['NumFramesInChunk'][i], observed_total_frame)
            pre_init_DF = pre_init_DF.replace(pre_init_DF['NumFramesInChunk'][i], actual_frame)
    pre_init_DF['NumFramesInChunk_initial'] = NumFramesInChunk_initial
    pre_init_DF = pre_init_DF.drop(columns=['date'])

    # make initialization dataframe outdirectory and save pre-initialization dataframe
    init_Df_Dir = makeOutDir(HomeDir_Path, 'Initialization_DF')

    pre_init_DF.to_csv(init_Df_Dir / '{}_PreInitializationDF.csv'.format(HomeDir_Path.stem))

########################################################################################################################
# NOTES
# INCLUDE CROPPING SECTION

########################################################################################################################
########################################3#### For Running Code #########################################################
########################################################################################################################

rec_path = "F:\RNAseq2_SD_Jellies\\20210901_LZ\\StaceyDash\\Rebound" # recording directory path (typically in HD F)
HomeDir = "I:\Ganglia_Tracker_Data\RNASeq2\\20210901\\StaceyDash\\Rebound" # home directory path (where you want to put init stack and df)

os.makedirs(Path(HomeDir), exist_ok=True)


# params are recording path, home directory path, video number (starts from 1), first time point (minute, second), second time point (minute, second)
get_init_stack(rec_path, HomeDir, 1,('00', '00'), ('00', '30'))

make_preinit_DF(HomeDir, rec_path, savio_additional_subdir='RNASeq2/20210901/StaceyDash/Rebound')

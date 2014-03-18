from path_helpers import path


def plot_frames(in_file, start_point=0, end_point=-1):
    in_path = path(in_file)
    target_fps, frame_lengths, times, sleep_times, record_times = in_file.pickle_load()

    plt.plot(len(frame_lengths[start_point:end_point]) * [1. / target_fps], label='%.4f fps' % target_fps)
    plt.plot(frame_lengths[start_point:end_point], label='frame_lengths')
    plt.plot(record_times[start_point:end_point], label='record_times')
    plt.plot(sleep_times[start_point:end_point], label='sleep_times')
    plt.legend()


if __name__ == '__main__':
    from sys import argv

    if not len(argv) == 2:
        print 'usage: %s <RecorderLog input file>' % argv[0]
        raise SystemExit
    in_file = path(argv[1])
    plot_frames(in_file)

import time


# print process bar
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█'):
    """
    创建进度条
    :param iteration: 当前进度（int）
    :param total: 总进度（int）
    :param prefix: 进度条前的文字（str）
    :param suffix: 进度条后的文字（str）
    :param decimals: 显示的小数点位数（int）
    :param length: 进度条的总长度（int）
    :param fill: 进度条的填充字符（str）
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    # 当进度达到总量时换行
    if iteration == total: 
        print()
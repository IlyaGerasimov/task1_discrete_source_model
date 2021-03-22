import argparse
import json
from random import uniform
import config
import multiprocessing
import sys


def parse_init():
    parser = argparse.ArgumentParser(description='Discrete source model.')
    parser.add_argument(
        '-f', '--file',
        type=argparse.FileType('r', encoding='UTF-8'),
        nargs='?',
        help='Name of the discrete source description file. If it is specified, program will work in Mode 1.'
    )
    parser.add_argument(
        '-n', '--num',
        type=int,
        nargs='?',
        default=None,
        help='Mode 1: Symbols amount. Optional argument.\nMode 2: Number of samples.'
    )
    parser.add_argument(
        '-s', '--sequence',
        nargs='*',
        help='Discrete probabilistic ensemble sequence. If file name is specified, it will be calculated by file model.\n Else by saved model which is previously used model.'
    )
    args = parser.parse_args()
    print(args)
    if not args.file and not args.sequence:
        exit("Error: Script cannot establish any mode. Please check your input.")
    if args.file:
        if args.file.name.split('.')[-1]!='json':
            print("Warning: your file doesn't have 'json' extension. Continue?[yes/no]")
            input_flag = True
            while input_flag:
                answer = input().lower()
                if answer in ['n', 'no', 'нет', 'н']:
                    args.file.close()
                    exit(0)
                elif answer in ['y', 'yes', 'да', 'д']:
                    input_flag = False
                else:
                    print("Please type [yes/no]")
        return args, True
    else:
        return args, False


# https://github.com/joeyespo/py-getch/blob/master/getch/getch.py
try:
    from msvcrt import getch
except ImportError:
    def getch():
        """
        Gets a single character from STDIO.
        """
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
# end


def check_distribution(data):
    for key, value in data.items():
        prob = 0
        for probability in data[key].values():
            prob += probability
            if probability > 1.0 or probability < 0.0:
                return False
        if prob != 1.0:
            return False
    return True


def check_names_dict(names, data):
    for values in data.values():
        for namekey in values.keys():
            if namekey not in names:
                return False
    return True


def check_names_list(names, list):
    for elem in list:
        if elem not in names:
            return False
    return True


def string_float(s):
    if '/' in s:
        return string_float(s.split('/')[0])/string_float(s.split('/')[1])
    else:
        return float(s)


def get_json(file):
    data = json.load(file)
    file.close()
    keys = data.keys()
    if 'models' not in keys or\
        'switches' not in keys or\
        'source' not in keys:
        exit("Error: json file requires 'models', 'switches' and 'source' keys")
    models = data['models']
    switches = data['switches']
    for key in models.keys():
        for key_m, value_m in models[key].items():
            models[key][key_m] = string_float(value_m)
    for key in switches.keys():
        for key_m, value_m in switches[key].items():
            switches[key][key_m] = string_float(value_m)
    if not check_distribution(data['models']) or not check_distribution(data['switches']):
        exit("Error: wrong source distribution function.")
    if not check_names_dict(models.keys(), data['switches']) or not check_names_list(switches.keys(), data['source']):
        exit("Error: unknown name is used.")
    return data


def get_source(data, i):
    switch_result = uniform(0.0, 1.0)
    model_result = uniform(0.0, 1.0)
    switch = data['source'][i % len(data['switches'])]
    switch_part = float(0)
    for key, value in data['switches'][switch].items():
        switch_part += value
        if switch_result < switch_part:
            model_part = float(0)
            for key_m, value_m in data['models'][key].items():
                model_part += value_m
                if model_result < model_part:
                    return key_m


def first_mode(data):
    i = 0
    while True:
        print(get_source(data, i))
        i = i + 1


def set_process(data, num):
    if num:
        for i in range(num):
            print(get_source(data, i))
    else:
        print(data)
        p = multiprocessing.Process(target=first_mode, args=(data,))
        p.start()
        button = getch()
        while button != b'q':
            print(button)
            button = getch()
        p.terminate()
    return 0


def second_mode(data, num, seq):
    if num is None or num == 0:
        exit("Error: Cannot establish second mode.")
    l = len(seq)
    total_cases = num - l + 1
    good_cases = 0
    shift = list()
    for i in range(l):
        res = get_source(data, i)
        shift.append(res)
    for i in range(num):
        if shift == seq:
            good_cases += 1
        res = get_source(data, i)
        shift.pop(0)
        shift.append(res)
    return good_cases/total_cases


def main():
    args, is_file = parse_init()
    print(args)
    if not args.sequence and is_file:
        print("Executing first mode.")
        print("Processing file...")
        data = get_json(args.file)
        print("Done.")
        print("Executing the source:")
        set_process(data, args.num)
    else:
        print("Executing second mode.")
        if is_file:
            print("Processing file...")
            data = get_json(args.file)
        else:
            print("No source file. Taking default file.")
            f = open(config.DEF_FILE, 'r')
            data = get_json(f)
        print("Done.")
        print("Executing the source:")
        print("The probability is:", second_mode(data, args.num, args.sequence))
    return 0


if __name__ == "__main__":
    main()

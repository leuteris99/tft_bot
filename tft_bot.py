import argparse
import signal
# ! Try to change to the pydirectinput library.
# import pydirectinput
import pydirectinput
import PIL
import time
import yaml
import cv2
from enum import Enum


IS_EXITING = False


class StartPos(Enum):
    NONE = 1
    FIND = 2
    ACCEPT = 3
    EXIT = 4
    PLAY_AGAIN = 5


class Log(Enum):
    MSG = 1
    ACTION = 2
    ERROR = 3
    DEBUG = 4
    INFO = 5


def log(msg: str, log_type: Log):
    out = ''
    if log_type is Log.MSG:
        out += '[MESSAGE] '
    elif log_type is Log.ACTION:
        out += '[ACTION] '
    elif log_type is Log.ERROR:
        out += '[ERROR] '
    elif log_type is Log.DEBUG:
        out += '[DEBUG] '
    elif log_type is Log.INFO:
        out += '[INFO] '
    print(out, msg)


def on_exit(signum, frame):
    global IS_EXITING
    if not IS_EXITING:
        res = input("Do you want to exit? [Y/n]\n")
    else:
        res = input("Do you want to exit instantly? [Y/n]")
    if res == 'y' or res == 'Y' or res == 'yes' or res == 'Yes' or res == 'YES' or res == "":
        if not IS_EXITING:
            res = input("Do you want to exit instantly? [y/N]")
            if res == "n" or res == "no" or res == "No" or res == "N" or res == "NO" or res == "":
                IS_EXITING = True
                return
        save_on_exit()
        exit(1)


def save_on_exit():
    data = dict(
        CALIBRATION=dict(
            X=x,
            Y=y,
        ),
        INFO=dict(
            TOKENS_COLLECTED=(tokens_count + tokens_collected),
        ),
    )
    write_yaml('settings.yaml', data)
    print('Total tokens collected during this session: ', tokens_collected)
    print('Total tokens collected for this pass: ', tokens_count + tokens_collected)


def read_yaml(file_path):
    with open(file_path, "r") as f:
        return yaml.safe_load(f)


def write_yaml(file_path, data):
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def fixed_move_cursor():
    pydirectinput.moveTo(100, 100, duration=1)


def press_button(button_img, timer):
    in_screen = False
    count = 0
    minutes_passed = 0
    while not in_screen:
        if pydirectinput.locateOnScreen(button_img) is None:
            count += 1
            if count >= 10:
                minutes_passed += ((count * timer) / 60)
                log('Searching for ' + button_img + '. Minutes Passed Searching: '
                    + str(minutes_passed), Log.ACTION)  # log
                count = 0
            time.sleep(timer)
        else:
            log(button_img + ' clicked.', Log.ACTION)  # log
            in_screen = True
    pydirectinput.click(button_img)


# 'X': 1276, 'Y': 894
def click_on_coordinates(xc, yc, timer, break_point):
    in_screen = False
    count = 0
    while not in_screen:
        pydirectinput.click(xc, yc)
        count += 1
        time.sleep(timer)
        if count >= break_point:
            break

# Point In( X = 1283, Y = 853) Point Bench ( X = 1810, Y = 1000)
def click_in_game(xc, yc, delay=0):
    pydirectinput.moveTo(xc, yc, delay)
    # try:
    #     pydirectinput.mouseDown(button="left")
    # except:
    pydirectinput.mouseDown(button="left")
    time.sleep(0.05)
    # try:
    #     pydirectinput.mouseUp(button="left")
    # except:
    pydirectinput.mouseUp(button='left')

def bench_unbench():
    click_in_game(1283, 853, 0.5)
    time.sleep(0.1)
    click_in_game(1810, 1000, 0.8)
    time.sleep(0.5)
    click_in_game(1283, 853, 0.8)

def accept_afk_check(button_img, timer):
    press_button(button_img, timer)
    fixed_move_cursor()
    count = 0
    while count <= 100:
        count += 1
        time.sleep(1)
        if pydirectinput.locateOnScreen(button_img) is not None:
            press_button(button_img, timer)
            time.sleep(0.5)
            fixed_move_cursor()
            count = 0


def find_tokens_earned(tok_col):
    if pydirectinput.locateOnScreen('./place/first_place.png') is not None \
            or pydirectinput.locateOnScreen('./place/second_place.png') is not None:
        tok_col += 8
        log('finished 1st - 2nd.', Log.DEBUG)
    elif pydirectinput.locateOnScreen('./place/third_place.png') is not None \
            or pydirectinput.locateOnScreen('./place/fourth_place.png') is not None:
        tok_col += 6
        log('finished 3rd - 4th.', Log.DEBUG)
    elif pydirectinput.locateOnScreen('./place/fifth_place.png') is not None \
            or pydirectinput.locateOnScreen('./place/sixth_place.png'):
        tok_col += 4
        log('finished 5th - 6th.', Log.DEBUG)
    elif pydirectinput.locateOnScreen('./place/seventh_place.png') is not None \
            or pydirectinput.locateOnScreen('./place/eighth_place.png'):
        tok_col += 2
        log('finished 7th - 8th.', Log.DEBUG)
    else:
        log('UNKNOWN FINISH PLACEMENT.', Log.ERROR)
    return tok_col


if __name__ == '__main__':
    signal.signal(signal.SIGINT, on_exit)

    parser = argparse.ArgumentParser(description='Settings')
    parser.add_argument('-c', '--calibrate', dest='calibrate', action='store_true',
                        help='[LEGACY] calibrate the cursor for the AFK check.')
    parser.add_argument('-sc', '--screenshot', dest='screenshot', action='store_true',
                        help='take a screenshot of the screen.')
    parser.add_argument('-s', '--start', type=str, dest='starting_argument',
                        help='Start from a specific step.'
                            '\n\t"start" or "find" or "find game" = start from the game lobby.'
                            '\n\t"accept" = start from the afk check.'
                            '\n\t"exit" or "exit game" = start by exiting the current game.'
                            '\n\t"restart" or "play again" = start from the finishing game lobby.')
    parser.add_argument('-t', '--tokens', dest='tokens', action='store_true',
                        help='Shows the tokens that had been earned by using the bot.')
    parser.add_argument('-q', dest='cloc', action='store_true',
                        help='Test clicking.')
    args = parser.parse_args()
    if args.cloc:
        time.sleep(5)
        # print(pydirectinput.position()[0])
        # print(pydirectinput.position()[1])
        # pydirectinput.alert(str(pydirectinput.position()))
        
        # for i in range(1,10):
            # time.sleep(2)
            # loc = pydirectinput.locateCenterOnScreen("find_match_button.png", confidence=0.8)
            # pydirectinput.moveTo(x=loc[0], y=loc[1])
            # pydirectinput.mouseDown(button="left")
            # time.sleep(0.05)
            # pydirectinput.mouseUp(button="left")
            # exit(0)
        exit(0)
    start_arg = StartPos.NONE
    if args.calibrate:
        log('Preparing to calibrate...', Log.ACTION)
        rev_clock = 3
        while rev_clock > 0:
            log(str(rev_clock), Log.INFO)  # log
            rev_clock -= 1
            time.sleep(1)
        pos = pydirectinput.position()
        d = dict(
            CALIBRATION=dict(
                X=pos.x,
                Y=pos.y,
            )
        )
        log(str(d), Log.INFO)  # log
        write_yaml('settings.yaml', d)
        exit(0)
    elif args.screenshot:
        log('Preparing to take a screenshot...', Log.ACTION)
        rev_clock = 3
        while rev_clock > 0:
            log(str(rev_clock), Log.INFO)  # log
            rev_clock -= 1
            time.sleep(1)
        img = pydirectinput.screenshot('screenshot.png')
        exit(0)
    elif args.starting_argument:
        if args.starting_argument == 'find'\
                or args.starting_argument == 'find game' or args.starting_argument == 'start':
            start_arg = StartPos.FIND
        elif args.starting_argument == 'accept':
            start_arg = StartPos.ACCEPT
        elif args.starting_argument == 'exit' or args.starting_argument == 'exit game':
            start_arg = StartPos.EXIT
        elif args.starting_argument == 'play again' or args.starting_argument == 'restart':
            start_arg = StartPos.PLAY_AGAIN
        else:
            log(args.starting_argument +
                " not found. run the program with -h to see the available parameters.", Log.ERROR)  # log
            exit(2)
    elif args.tokens:
        settings = read_yaml('settings.yaml')
        tokens_count = settings['INFO']['TOKENS_COLLECTED']
        log(str(tokens_count) + ' tokens has been collected.', Log.INFO)  # log
        exit(0)

    settings = read_yaml('settings.yaml')
    x = settings['CALIBRATION']['X']
    y = settings['CALIBRATION']['Y']
    tokens_count = settings['INFO']['TOKENS_COLLECTED']
    tokens_collected = 0
    log('Starting the bot...', Log.ACTION)  # log
    screen_num = 0
    while True:
        start_time = int(time.time())
        if start_arg is StartPos.NONE or start_arg is StartPos.FIND:
            press_button('find_match_button.png', 3)
            start_arg = StartPos.NONE
        if start_arg is StartPos.NONE or start_arg is StartPos.ACCEPT:
            accept_afk_check('accept.png', 2)
            start_arg = StartPos.NONE
            time.sleep(1 * 60)

        # 'X': 1100, 'Y': 735

        is_exit_found = False
        tc = 0
        if start_arg is StartPos.NONE or start_arg is StartPos.EXIT:
            start_arg = StartPos.NONE
            while not is_exit_found:
                time.sleep(5)
                bench_unbench()
                img_exit = pydirectinput.locateOnScreen('exit.png')
                img_win = pydirectinput.locateOnScreen('play_again.png')
                img_mission_ok = pydirectinput.locateCenterOnScreen('mission_ok.png', confidence=0.8)
                if img_exit is not None:
                    end_time = int(time.time())
                    pydirectinput.hotkey('alt', 'f4')
                    pydirectinput.hotkey('alt', 'f4')
                    minutes = int((end_time - start_time) / 60)
                    seconds = int((end_time - start_time) % 60)
                    log('Time elapsed: ' + str(minutes) + ' Minutes and ' + str(seconds) + ' Seconds.', Log.INFO)  # log
                    is_exit_found = True
                elif img_win is not None:
                    log('YOU WON A ROUND!!!', Log.INFO)  # log
                    is_exit_found = True
                elif img_mission_ok is not None:
                    log('Mission Complete.', Log.INFO)
                    pydirectinput.moveTo(img_mission_ok[0], img_mission_ok[1])
                    pydirectinput.click()
                    is_exit_found = True

            # print('Tokens collected that far: ', tokens_collected)
        if start_arg is StartPos.NONE or start_arg is StartPos.PLAY_AGAIN:
            # For testing purposes.
            while pydirectinput.locateOnScreen('play_again.png') is None and pydirectinput.locateOnScreen('mission_ok.png', confidence=0.8) is None:
                time.sleep(1)
            # tokens_collected = find_tokens_earned(tokens_collected)           # ! change the images for the new set.
            img_mission_ok = pydirectinput.locateCenterOnScreen('mission_ok.png', confidence=0.8)
            if(img_mission_ok is not None):
                pydirectinput.moveTo(img_mission_ok[0], img_mission_ok[1])
                pydirectinput.click()
                time.sleep(2)    
            time.sleep(2)
            pydirectinput.screenshot('./screenshots/screenshot_' + str(screen_num) + '.png')
            log("Screenshot taken.",Log.DEBUG)
            screen_num += 1
            
            press_button('play_again.png', 10)
            start_arg = StartPos.NONE
            fixed_move_cursor()
        if IS_EXITING:
            save_on_exit()
            break

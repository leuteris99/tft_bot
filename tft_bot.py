import argparse
import schedule
import signal
import pyautogui
import pydirectinput
import pyscreeze as psc
import pytesseract
from pytesseract import Output
import PIL
from time import sleep, time
from os import remove as remove_file
import yaml
import cv2
from enum import Enum
from config_manager import ConfigManager, Pref

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
        set_config_to_user()
        save_on_exit()
        exit(1)

def set_config_to_user() -> None:
    manager = ConfigManager()
    manager.change_config(Pref.USER)
    manager.save()
    log("Config set to user's preferences.",Log.INFO)


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
        if pyautogui.locateOnScreen(button_img) is None:
            count += 1
            if count >= 10:
                minutes_passed += ((count * timer) / 60)
                log('Searching for ' + button_img + '. Minutes Passed Searching: '
                    + str(minutes_passed), Log.ACTION)  # log
                count = 0
            sleep(timer)
        else:
            log(button_img + ' clicked.', Log.ACTION)  # log
            in_screen = True
    coord = pyautogui.locateCenterOnScreen(button_img)
    pydirectinput.click(coord.x,coord.y)


# 'X': 1276, 'Y': 894
def click_on_coordinates(xc, yc, timer, break_point):
    in_screen = False
    count = 0
    while not in_screen:
        pydirectinput.click(xc, yc)
        count += 1
        sleep(timer)
        if count >= break_point:
            break

# Point In( X = 1283, Y = 853) Point Bench ( X = 1810, Y = 1000)
def click_in_game(xc, yc, delay=0):
    pyautogui.moveTo(xc, yc, delay)
    # try:
    #     pydirectinput.mouseDown(button="left")
    # except:
    pydirectinput.mouseDown(button="left")
    sleep(0.05)
    # try:
    #     pydirectinput.mouseUp(button="left")
    # except:
    pydirectinput.mouseUp(button='left')

def bench_unbench():
    click_in_game(1283, 853, 0.5)
    sleep(0.1)
    click_in_game(1810, 1000, 0.8)
    sleep(0.5)
    click_in_game(1283, 853, 0.8)

def accept_afk_check(button_img, timer):
    press_button(button_img, timer)
    fixed_move_cursor()
    count = 0
    while count <= 100:
        count += 1
        sleep(1)
        if pyautogui.locateOnScreen(button_img) is not None:
            press_button(button_img, timer)
            sleep(0.5)
            fixed_move_cursor()
            count = 0


def find_tokens_earned(tok_col):
    if pyautogui.locateOnScreen('./place/first_place.png') is not None \
            or pyautogui.locateOnScreen('./place/second_place.png') is not None:
        tok_col += 8
        log('finished 1st - 2nd.', Log.DEBUG)
    elif pyautogui.locateOnScreen('./place/third_place.png') is not None \
            or pyautogui.locateOnScreen('./place/fourth_place.png') is not None:
        tok_col += 6
        log('finished 3rd - 4th.', Log.DEBUG)
    elif pyautogui.locateOnScreen('./place/fifth_place.png') is not None \
            or pyautogui.locateOnScreen('./place/sixth_place.png'):
        tok_col += 4
        log('finished 5th - 6th.', Log.DEBUG)
    elif pyautogui.locateOnScreen('./place/seventh_place.png') is not None \
            or pyautogui.locateOnScreen('./place/eighth_place.png'):
        tok_col += 2
        log('finished 7th - 8th.', Log.DEBUG)
    else:
        log('UNKNOWN FINISH PLACEMENT.', Log.ERROR)
    return tok_col

def isClientStuck():
    pass

def exit_when_lose() -> bool:
    filename = 'tmp.png'
    psc.screenshot(filename)
    image = cv2.imread(filename)
    remove_file(filename)
    results = pytesseract.image_to_data(image=image,output_type=Output.DICT)
    for i in range(0,len(results['text'])):
        exiters = [
            'exit',
            'watching',
            'finished'
        ]
        for exiter in exiters:
            if exiter in results['text'][i].lower():
                end_time = int(time())
                pyautogui.hotkey('alt', 'f4')
                pyautogui.hotkey('alt', 'f4')
                minutes = int((end_time - start_time) / 60)
                seconds = int((end_time - start_time) % 60)
                log('Time elapsed: ' + str(minutes) + ' Minutes and ' + str(seconds) + ' Seconds.', Log.INFO)  # log
                return True
    return False


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
    parser.add_argument('-cm', '--config', '--config-manager', type=str, dest='config',
                        help='Set the in-game settings manually.'
                            "\n\t'user' to change the settings to the user's prefered."
                            "\n\t'bot' to change the settings to the bot's prefered.")
    args = parser.parse_args()

    start_arg = StartPos.NONE
    if args.config:
        log(f'Setting the game configuration manually to {args.config} profile.',Log.INFO)
        manager = ConfigManager()
        pref = Pref.set_pref(args.config)
        if pref is None:
            raise ValueError(f'Incompatable Configuration profile {args.config}')
        manager.change_config(pref)
        manager.save()
        log(f"Active config file: {manager.active().name}",Log.INFO)
        exit(0)
    if args.calibrate:
        log('Preparing to calibrate...', Log.ACTION)
        rev_clock = 3
        while rev_clock > 0:
            log(str(rev_clock), Log.INFO)  # log
            rev_clock -= 1
            sleep(1)
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
            sleep(1)
        try:
            img = psc.screenshot('screenshot.png')
        except:
            log('error taking screenshot.',Log.ERROR)
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
    manager = ConfigManager()
    manager.change_config(Pref.BOT)
    log('Change the in-game settings according to the Bot\'s preference.',Log.ACTION)
    manager.save()

    schedule.every(1).minutes.do(isClientStuck)

    screen_num = 0
    while True:
        start_time = int(time())
        if start_arg is StartPos.NONE or start_arg is StartPos.FIND:
            press_button('find_match_button.png', 3)
            start_arg = StartPos.NONE
        if start_arg is StartPos.NONE or start_arg is StartPos.ACCEPT:
            accept_afk_check('accept.png', 2)
            start_arg = StartPos.NONE
            sleep(1 * 60)

        # 'X': 1100, 'Y': 735

        is_exit_found = False
        tc = 0
        if start_arg is StartPos.NONE or start_arg is StartPos.EXIT:
            start_arg = StartPos.NONE
            while not is_exit_found:
                sleep(5)
                bench_unbench()

                is_exit_found = exit_when_lose()

                img_exit = pyautogui.locateOnScreen('exit.png')
                img_win = pyautogui.locateOnScreen('play_again.png')
                img_mission_ok = pyautogui.locateCenterOnScreen('mission_ok.png', confidence=0.8)
                if img_exit is not None:
                    end_time = int(time())
                    pyautogui.hotkey('alt', 'f4')
                    pyautogui.hotkey('alt', 'f4')
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
                schedule.run_pending()

            # print('Tokens collected that far: ', tokens_collected)
        if start_arg is StartPos.NONE or start_arg is StartPos.PLAY_AGAIN:
            # For testing purposes.
            while pyautogui.locateOnScreen('play_again.png') is None and pyautogui.locateOnScreen('mission_ok.png', confidence=0.8) is None:
                sleep(1)
            # tokens_collected = find_tokens_earned(tokens_collected)           # ! change the images for the new set.
            img_mission_ok = pyautogui.locateCenterOnScreen('mission_ok.png', confidence=0.8)
            if(img_mission_ok is not None):
                pydirectinput.moveTo(img_mission_ok[0], img_mission_ok[1])
                pydirectinput.click()
                sleep(2)    
            sleep(2)
            try:
                psc.screenshot('./screenshots/tmp_place/screenshot_' + str(screen_num) + '.png')
            except:
                log('error on screenshot.',Log.ERROR)
            log("Screenshot taken.",Log.DEBUG)
            screen_num += 1
            
            press_button('play_again.png', 10)
            start_arg = StartPos.NONE
            fixed_move_cursor()
        if IS_EXITING:
            set_config_to_user()
            save_on_exit()
            break

# -*- coding: utf-8 -*-
"""
Created on Wed Aug 26 12:33:30 2020

@author: Amit G
"""

import pygame
import pygame.locals
from sys import exit
import string
from spellchecker import SpellChecker
from threading import Thread
from time import sleep, time
from random import randint, seed
from collections import OrderedDict
import SysUtility as su
# import GameUtility as gu
import pyperclip as cb
import os
import pickle
from collections import Counter

FPSCLOCK = None


class SpellerThread(Thread):

    def __init__(self, spell):
        Thread.__init__(self)
        self._spell = spell
        self.text = ''
        self._stop = False
        self._error = 1
        self._misspelled = ''
        self.fresh_data = False

    def clearCache(self):
        self._misspelled = ''
        self._error = 1

    def _updatedStatus(self, ignore_spell_list=[]):
        # print(f' 1--> {self._misspelled}')
        return (1 - self._error, self._misspelled)

    def _updateText(self, textList, buffer):
        # if len(textList) == 0 and len(buffer) < 10:
        #     return
        self.text = ''
        for item in textList:
            self.text += item
        self.text += ''.join(buffer)
        self.fresh_data = True

    def getWords(self):
        return self.text.split(' ')

    def _stopThread(self):
        self._stop = True

    def stripSpecial(self):
        " strip all characters that hampers dictionary check"
        _specialChars = tuple('.,;:-_=-{}[]()')
        _working_text = self.text
        for _char in _specialChars:
            while _working_text.find(_char) > 0:
                _working_text = _working_text.replace(_char, '')

        return _working_text

    def run(self):
        while self._stop is False:
            if not self.fresh_data or len(self.text) == 0:
                sleep(.5)
                continue

            _cleaned_text = self.stripSpecial()
            _cleaned_text = [txt.strip() for txt in _cleaned_text.split(' ')
                             if txt not in ['a', '']
                             ]
            self._misspelled = self._spell.unknown(_cleaned_text)
            self._error = len(self._misspelled) / len(self.text.split(' '))
            self.fresh_data = False
        print("Exiting thread...")


def _type_effice(txt_list, strokes):

    if strokes == 0 or txt_list is None:
        return 0

    total_chars = 0

    for txt in txt_list:
        total_chars += sum(len(word) for word in txt.split(' ')) + \
            len(txt.split(' ')) - 1

    # print(f'total chars found ...{total_chars}, {strokes}')
    return total_chars / strokes


def showTextBox(screen, box, font, _live_text):

    _text = _live_text.replace('\n', '').strip()
    if len(_text) == 0:
        return

    step = 4
    _x, _y = box.topleft
    _y += header_width

    while(len(_text) > 0):
        i = 10
        while (font.size(_text[:i])[0] < _TEXT_AREA):
            i += step
            try:
                _text[i]
            except IndexError:
                # print('Broken out!!!')
                break

        screen.blit(
            font.render(_text[:i-1], True, (255, 255, 255)),
            (_x + 5, _y)
        )
        # print(_text[:i])
        _text = _text[i-1:]
        _y += line_size
        if font.size(_text)[0] < _TEXT_AREA:
            break

    screen.blit(font.render(_text, True, (255, 255, 255)), (_x + 5, _y))


def _draw_mesh(screen_dim: set):
    mesh = pygame.Surface(screen_dim, 0, 32)
    net_mesh = pygame.Surface((100, 100))
    color = (90, 90, 90)
    for xy in range(4, 105, 4):
        pygame.draw.line(net_mesh, color, (0, xy), (xy, 0))
        pygame.draw.line(net_mesh, color, (xy, 100), (100, xy))
        pygame.draw.line(net_mesh, color, (0, 100 - xy), (xy, 100))
        pygame.draw.line(net_mesh, color, (100 - xy, 0), (100, xy))

    net_mesh_rect = net_mesh.get_rect()
    for col in range(screen_dim[0]//100 + 1):
        for row in range(screen_dim[1]//100 + 1):
            net_mesh_rect.topleft = (col * 100, row * 100)
            mesh.blit(net_mesh, net_mesh_rect.topleft)

    return mesh


def _draw_label_box(screen, color, disp_label, head_text, metrics=False):

    _x, _y = disp_label.topleft
    _disp_width = disp_label.size[0] + 1
    label_box = pygame.Rect((_x, _y), (_disp_width, header_width))
    # disp_label.topleft = (_x, _y + header_width)

    screen.fill((6, 34, 7.4), disp_label)
    pygame.draw.rect(screen, color, disp_label, 2)
    pygame.draw.rect(screen, (16.5, 61.6, 19.3), label_box)

    screen.blit(
            font.render(head_text[0], True, (255, 255, 255)),
            (_x + 5, _y)
            )

    if metrics:
        _x = disp_label.midleft[0]
        _x += disp_label.width // 2
        symbol = '' if head_text[0] == 'TPM' else ' %'
        head_info = f'{int(head_text[1])}{symbol}'
        _y = disp_label.midleft[1] + header_width // 2
        _disp = header_font.render(head_info, True, (255, 255, 255))
        _disp_rect = _disp.get_rect()
        _disp_rect.center = (_x, _y)
        screen.blit(_disp, _disp_rect)
        label_box = _disp_rect

    # return the x, y co-ordinates for further drawwing purposes
    return label_box


def getTextBlocks(filepath):

    try:
        with open(filepath, 'rb') as file:
            textLines = pickle.load(file)

        for text in textLines:
            if len(textLines[text]) == 1:
                textLines[text].append([])
    except Exception:
        textLines = {0: []}
        txt = (r'''Please enter the text in the text input box at
               a comfortable speed. This application will help
               you to analyze your typing efficiency and give
               real time feed back of your typing performance.
               You can take the feedback to understand
               areas of teimprovement.Thank you for
               listening''').replace("\n", "")
        textLines[0].append(txt)
        textLines[0].append([])

    return textLines


def inProcessLogo(screen, logoname):

    assert len(logoname) > 0

    speaking_img = pygame.image.load(logoname + '.png')
    speak_rect = speaking_img.get_rect()
    speak_rect.center = screen.get_rect().center
    screen.blit(speaking_img, speak_rect.topleft)
    _rect = pygame.rect.Rect(speak_rect)
    pygame.draw.rect(screen, (206, 64, 18), _rect, 4)
    pygame.display.update()
    FPSCLOCK.tick()


def speakAbout(screen, speaker):
    inProcessLogo(screen, 'speaking')
    print('speaking...')
    speaker.speak(r'''Please enter the text in the text input box at a
                  comfortable speed. This application will help you to analyze
                  your typing efficiency and give real time feed back of
                  your typing performance. You can take the feedback to
                  understand areas of improvement. Thank you for listening''')


def _systemExit():
    pygame.quit()
    exit()


def _saveTextBlock(textLines, fileName):
    try:
        with open(fileName, 'wb') as _file:
            pickle.dump(textLines, _file)
    except FileNotFoundError:
        pass


def _showSpellWords(screen, font, afterThis,
                    showWords, spell_white_list, gap_between_box=8):

    if len(showWords) == 0:
        return {}
    # create position to put the misspelled words below the read box
    _initPos = (afterThis.bottomleft[0],
                afterThis.bottomleft[1] + gap_between_box)
    _textPos = _initPos[::]
    _txt_width = _textPos[0]
    WHITE = (10, 87, 21)
    BLACK = (0, 0, 0)
    WHITE_LIST = (127, 158, 214)

    _spell_boxes = {}
    _spells_list = list(showWords)[::-1]
    for _word in _spells_list:
        if _word in spell_white_list:
            _box_text = font.render(f'X {_word}', True, BLACK, WHITE_LIST)
        else:
            _box_text = font.render(f'X {_word}', True, BLACK, WHITE)

        # Rect((0, 0), font.size(_word))
        _box = _box_text.get_rect()
        # print(_textPos, _txt_width, screen.get_width(), _word)

        if _txt_width + _box.width + gap_between_box < screen.get_width():
            _textPos = (_txt_width, _textPos[1])
            _box.topleft = _textPos
        else:
            _textPos = (_initPos[0],
                        _textPos[1] + gap_between_box + _box.height)
            _txt_width = _initPos[0]
            _box.topleft = _textPos

        _txt_width += _box.width + gap_between_box
        _spell_boxes[_word] = _box
        # print(_word, _box.topleft)
        screen.blit(_box_text, _box.topleft)
    # print('-------------------')
    return _spell_boxes


def __show_text_stats(text_stat, boxref):
    # create a new surface and print the mistyped letters stats
    if not text_stat:
        return

    assert boxref[0] > 0

    _box_width = 90

    _font = pygame.font.SysFont('arial', 18)
    _header = _font.render('Mistypes', True, (255, 255, 255))
    text_height = _header.get_rect()[3]
    boxHeight = boxref[0] - text_height
    str_rect = _header.get_rect()
    str_rect.center = (_box_width // 2, text_height // 2)
    boxHeight -= text_height
    _surface = pygame.Surface((100, boxHeight)).convert()
    _surface.fill((100, 100, 0))
    _surface.blit(_header, str_rect.topleft)
    pygame.draw.rect(_surface, (100, 255, 0),
                     pygame.Rect(0, 0, 100, text_height), 1)

    _num_items = boxHeight / text_height
    _xPos, _yPos = 0, text_height + 5
    __item_count = 0

    for stat in text_stat:

        # print the character
        _str = _font.render(stat[0].ljust(5), True, (255, 255, 255))
        _surface.blit(_str, (_xPos + 2, _yPos))

        _str = _font.render(f'{stat[1][0]} %', True, (255, 255, 255))
        str_rect = _str.get_rect()
        str_rect.center = (_box_width // 2, _yPos + text_height // 2)
        _surface.blit(_str, str_rect.topleft)
        _yPos += text_height + 2
        __item_count += 1
        if __item_count > min(9, _num_items):
            break
    return _surface


def _text_counter(disp_text: str, typed_text: str):
    assert len(disp_text) > 0

    if len(typed_text) < len(disp_text) * 0.4:
        return {}

    # compare only upto the length of the typed text
    type_count = Counter(typed_text.replace(' ', '').lower())
    type_weight = sum(type_count.values())
    for key in type_count:
        type_count[key] = [type_count[key]]
        type_count[key].append(round(type_count[key][0]/type_weight, 2))

    typed_length = len(typed_text)
    disp_count = Counter(disp_text.replace(' ', '').lower()[:typed_length])

    diff_count = dict()
    for key in disp_count:
        if key in type_count:
            if disp_count[key] != type_count[key][0]:
                _diff = (disp_count[key] - type_count[key][0])

                diff_count[key] = [int(_diff / disp_count[key] * 100),
                                   type_count[key][1]]

    mismatch = sorted(diff_count.items(),
                      key=lambda k: k[1][1], reverse=True)
    print(mismatch)
    return mismatch


def _find_dndx(texts, idx):
    try:
        return tuple(texts.keys())[idx]
    except IndexError:
        return 0,


MTERICS_BOX = (100, 60)


def main():
    global screen, font, header_font, header_width, line_size, _TEXT_AREA

    os.environ['SDL_VIDEO_CENTERED'] = '1'

    seed()
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    SCREEN_SIZE = (800, 600)
    checkSpell = SpellerThread(SpellChecker())
    checkSpell.start()

    SPEAKER = su.TextSpeak()
    SPEAKER.start()

    assert checkSpell.is_alive() is True

    display_icon = pygame.image.load('keyboard.png')

    # --------process welcome screen ----------------
    screen = pygame.display.set_mode((400, 300), pygame.NOFRAME, 32)
    pygame.display.set_caption('Typing Accuracy Test')

    program_logo = pygame.image.load('keyboard_logo.png')
    logo_rect = program_logo.get_rect()
    logo_rect.center = (screen.get_rect().center)
    screen.blit(program_logo, logo_rect.topleft)
    pygame.display.update()
    # --------display welcome screen ------------

    sleep(1.0)

    font = pygame.font.SysFont('arial', 20)
    header_font = pygame.font.SysFont('arial', 30)
    header_width = 20
    # pygame.event.set_blocked(pygame.MOUSEMOTION)

    line_size = font.get_linesize()
    gap_between_box = 10

    BOX_SIZE = (SCREEN_SIZE[0] - MTERICS_BOX[0] - gap_between_box * 2, 200)

    startX, startY = SCREEN_SIZE[0] - BOX_SIZE[0], header_width
    startX -= gap_between_box
    CURSOR_POS = (startX, startY)

    # structure the display are of the screen
    display_box = pygame.Rect((startX, 5), BOX_SIZE)
    read_yPos = display_box.topleft[1] + BOX_SIZE[1] + gap_between_box
    read_box = pygame.Rect((startX, read_yPos), BOX_SIZE)
    # print(f'read box bottom pos {read_box.bottomleft}')

    icon_names = ['speak', 'next', 'previous', 'delete', 'info', 'plus']

    _ICONS = {}

    for icon in icon_names:
        _ICONS[icon] = [pygame.image.load(f'{icon}.png').convert_alpha()]
        _ICONS[icon].append(_ICONS[icon][0].get_rect())

    _prev_rect = read_box.topright
    for _icon in _ICONS.values():
        _icon[1].topleft = (_prev_rect[0] -
                            _icon[0].get_width() - gap_between_box,
                            _prev_rect[1])
        _prev_rect = _icon[1].topleft
        # print(_prev_rect)

    _metrics_box = OrderedDict()
    accuracy_box = pygame.Rect((2, 5), MTERICS_BOX)
    _metrics_box['accuracy_box'] = (accuracy_box, 'Accuracy')
    spell_accuracy_box = pygame.Rect((2, 5), MTERICS_BOX)
    _metrics_box['spell_accuracy_box'] = (spell_accuracy_box, 'Spelling')
    word_matching_box = pygame.Rect((2, 5), MTERICS_BOX)
    _metrics_box['word_matching_box'] = (word_matching_box, 'Word Match')
    type_rpm_box = pygame.Rect((2, 5), MTERICS_BOX)
    _metrics_box['type_rpm_box'] = (type_rpm_box, 'TPM')

    _first_box = True
    _prev_bottomleft = None
    for m_box in _metrics_box:
        if _first_box:
            _first_box = False
            _prev_bottomleft = _metrics_box[m_box][0].bottomleft
            continue

        _metrics_box[m_box][0].topleft = (_prev_bottomleft[0],
                                          _prev_bottomleft[1] +
                                          gap_between_box)
        _prev_bottomleft = _metrics_box[m_box][0].bottomleft

    status_box = pygame.Rect((0, 0), (SCREEN_SIZE[0], 20))
    status_box.bottomleft = (0, SCREEN_SIZE[1])

    _TEXT_AREA = (display_box.width - 25)
    # print(f'text area {_TEXT_AREA}')

    filePath = 'textBlocks.ob'
    textLines = getTextBlocks(filePath)
    _spell_boxes = {}

    letters = list([])
    _keyboard_hits = 0

    _history = {}
    _disp_text = list([])
    # event_text = []

    # randomize the text display
    txtIndex = randint(0, len(textLines)-1)
    _live_text = textLines[_find_dndx(textLines, txtIndex)]
    _total_chars = len(_live_text[0])

    start_time = 0
    _typed_chars = 0
    typed_per_min = 0
    del program_logo

    timer_disp = font.render("Elapsed Time: 0 Secs",
                             True,
                             (200, 0, 0)
                             )
    time_disp_rect = timer_disp.get_rect()
    time_disp_rect.topleft = (display_box.topright[0] - timer_disp.get_width(),
                              display_box.topleft[1]
                              )

    _SKIP_SP_KEYS = set([pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP,
                         pygame.K_DOWN, pygame.K_LSHIFT, pygame.K_RSHIFT,
                         pygame.K_LCTRL, pygame.K_RCTRL])

    os.environ['SDL_VIDEO_CENTERED'] = '1'

    _status_text = 'Welcome to Keyboard Master!'
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    pygame.display.set_icon(display_icon)

    screen_background = _draw_mesh(SCREEN_SIZE)
    __STOP = False

    while not __STOP:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # _saveTextBlock(textLines, filePath)
                __STOP = True
                break
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    __STOP = True
                    break
                elif event.key == pygame.K_BACKSPACE:
                    print('backspace...')
                    print(''.join(letters))
                    if len(letters) > 0:
                        # letters = letters[:-1]
                        tx = letters.pop()
                        print(f'popped {tx}')
                    elif len(_disp_text) > 0:
                        last_line = _disp_text.pop()
                        letters.extend(last_line)
                        # letters = letters[:-1]
                        tx = letters.pop()
                        print(f'popped {tx}')
            elif event.type == pygame.KEYDOWN:
                # print(event)
                if event.unicode in string.printable:
                    if event.key not in _SKIP_SP_KEYS:
                        _keyboard_hits += 1
                        letters.append(event.unicode)
                    # save the start time of typing
                    if len(_disp_text) == 0 and len(letters) == 1:
                        start_time = time()
                    else:
                        # calculate the typed chars per minute
                        typed_per_min = 60 * _typed_chars / \
                            (time() - start_time)
                        _text = f"Time: {int(time()-start_time)} Seconds"
                        timer_disp = font.render(_text,
                                                 True,
                                                 (200, 100, 0)
                                                 )
                        time_disp_rect = timer_disp.get_rect()
                        time_disp_rect.topleft = (display_box.topright[0] -
                                                  timer_disp.get_width(),
                                                  display_box.topleft[1]
                                                  )
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if _ICONS['next'][1].collidepoint(pygame.mouse.get_pos()):
                    _history[txtIndex] = _disp_text
                    txtIndex += 1
                    if txtIndex >= len(textLines):
                        txtIndex = 0
                    _disp_text.clear()

                    if txtIndex in _history.keys():
                        _disp_text = _history[txtIndex]

                    letters.clear()
                    _keyboard_hits = 0
                    _live_text = textLines[_find_dndx(textLines, txtIndex)]
                    _total_chars = len(_live_text[0])
                    checkSpell.clearCache()
                elif _ICONS['info'][1].collidepoint(pygame.mouse.get_pos()):
                    speakAbout(screen, SPEAKER)
                elif _ICONS['speak'][1].collidepoint(pygame.mouse.get_pos()):
                    # print(f'Speak Text {speak_icon_rect}')
                    SPEAKER.speak(_live_text[0])
                elif _ICONS['previous'][1].collidepoint(
                        pygame.mouse.get_pos()):

                    _history[txtIndex] = _disp_text
                    txtIndex -= 1
                    if txtIndex < 0:
                        txtIndex = len(textLines) - 1
                    _disp_text.clear()
                    letters.clear()
                    _keyboard_hits = 0

                    if txtIndex in _history.keys():
                        _disp_text = _history[txtIndex]

                    _live_text = textLines[_find_dndx(textLines, txtIndex)]
                    _total_chars = len(_live_text[0])
                    checkSpell.clearCache()
                elif _ICONS['delete'][1].collidepoint(pygame.mouse.get_pos()):
                    if len(textLines) == 0:
                        _status_text = "Nothing to delete!!"
                        continue

                    del textLines[_find_dndx(textLines, txtIndex)]
                    txtIndex -= 1
                    if txtIndex < 0:
                        txtIndex = len(textLines) - 1
                    _saveTextBlock(textLines, filePath)
                    _status_text = "Changes saved..."
                    checkSpell.clearCache()
                elif _ICONS['plus'][1].collidepoint(
                        pygame.mouse.get_pos()):
                    if len(cb.paste()) > 0:
                        _pasted_text = cb.paste().replace('\n', '')
                        if len(_pasted_text) < 100:
                            _status_text = 'Please Paste text > 100 chars'
                            continue

                        next_index = max(textLines.keys()) + 1
                        textLines[next_index] = []
                        textLines[next_index].append(_pasted_text[:500])
                        textLines[next_index].append([])
                        _status_text = 'Copied text (Max 500 chars)'
                        cb.copy('')
                        txtIndex = len(textLines) - 1
                        _disp_text.clear()
                        letters.clear()
                        _keyboard_hits = 0
                        _live_text = textLines[_find_dndx(textLines, txtIndex)]
                        _total_chars = len(_live_text[0])
                        _saveTextBlock(textLines, filePath)
                        checkSpell.clearCache()
                        _status_text = "New addition saved..."
                    else:
                        _status_text = "Clipboard is empty!!"
                else:
                    spell_hits = [box.collidepoint(pygame.mouse.get_pos())
                                  for box in _spell_boxes.values()]
                    if any(spell_hits):
                        idx = 0
                        while spell_hits[idx] == 0:
                            idx += 1
                        key_clicked = tuple(_spell_boxes.keys())[idx]
                        # remove the word from white list
                        if key_clicked in _live_text[1]:
                            idx = _live_text[1].index(key_clicked)
                            del _live_text[1][idx]
                            # print(_live_text[1])
                            _status_text = f'{key_clicked} Removed'
                        else:
                            _status_text = f'{key_clicked} Excluded'
                            # idx = _find_dndx(textLines, txtIndex)
                            _live_text[1].append(key_clicked)
                            # del _spell_boxes[key_clicked]

            screen.blit(screen_background, (0, 0))
            # screen.fill((0,0,0))

            _draw_label_box(screen, (80.8, 25, 7), display_box, ['Input Text'])
            _draw_label_box(screen,
                            (80.8, 25, 7),
                            read_box,
                            [f"Read Text >>{txtIndex+1} of {len(textLines)}"]
                            )

            for _icon in _ICONS.values():
                screen.blit(_icon[0], _icon[1].topleft)

            _draw_label_box(screen,
                            (204, 39, 18),
                            _metrics_box['accuracy_box'][0],
                            [_metrics_box['accuracy_box'][1],
                             _type_effice(
                                 letters + _disp_text,
                                 _keyboard_hits) * 100],
                            True
                            )
            # print(f"{letters}, {_disp_text}, {_keyboard_hits}")

            _x, _y = startX + 3, startY + 3

            # print(letters)
            if font.size(''.join(letters))[0] > _TEXT_AREA:
                _disp_text.append(''.join(letters))
                # _history.extend(letters)
                letters.clear()

            checkSpell._updateText(_disp_text, letters)
            _status = checkSpell._updatedStatus()
            # print(f'Thread status--->{_status[1]}')

            _spell_boxes = _showSpellWords(screen, font, read_box,
                                           _status[1], _live_text[1])
            # spelling accuracy display
            _draw_label_box(screen,
                            (0, 200, 0),
                            _metrics_box['spell_accuracy_box'][0],
                            [_metrics_box['spell_accuracy_box'][1],
                             _status[0] * 100],
                            True
                            )

            # Remaining characters count
            _typed_chars = sum([len(x) for x in _disp_text]) + \
                len(''.join(letters).replace(' ', ''))

            # if the chars remaining reachers zero , discard the last entry
            if _total_chars - _typed_chars < 0:
                if len(letters) > 0:
                    letters.pop()
                    _typed_chars -= 1

            max_val = max(_total_chars - _typed_chars, 0)
            _ch_count = header_font.render(f"{max_val}", True, (0, 200, 100))
            _by = display_box.bottomleft[1] - _ch_count.get_rect()[3]
            _bx = display_box.bottomright[0] - _ch_count.get_rect()[2]

            screen.blit(_ch_count, (_bx, _by))

            # find matches from the words being typed and display
            # the unfound words percentage among the typed text
            _words = checkSpell.getWords()

            _words_found_map = [word in _live_text[0].split(' ')
                                for word in _words]
            _match_words_sum = sum(_words_found_map)
            _words_not_found = []
            for idx, flag in enumerate(_words_found_map):
                if not flag:
                    _words_not_found.append(_words[idx])

            _missed = _match_words_sum / len(_live_text[0].split(' '))

            _draw_label_box(screen,
                            (0, 200, 0),
                            _metrics_box['word_matching_box'][0],
                            [_metrics_box['word_matching_box'][1],
                             _missed * 100],
                            True
                            )

            _last_box_pos = _draw_label_box(screen, (0, 200, 0),
                                            _metrics_box['type_rpm_box'][0],
                                            [_metrics_box['type_rpm_box'][1],
                                             typed_per_min],
                                            True
                                            )

            if len(_disp_text) > 0:
                for i in range(len(_disp_text)):
                    screen.blit(
                        font.render(_disp_text[i], True, (255, 255, 255)),
                        (_x, _y)
                        )
                    _y += line_size

            # display the last line from transient buffer
            screen.blit(
                    font.render(''.join(letters), True, (255, 255, 255)),
                    (_x, _y)
                    )

            text_stat = _text_counter(_live_text[0],
                                      ''.join(_disp_text) + ''.join(letters)
                                      )
            # process the display only if the stat is generated
            if text_stat:
                # print('Last Box', _last_box_pos)
                _bottom_left = _last_box_pos.bottomleft
                stat_surf = __show_text_stats(text_stat, (SCREEN_SIZE[1] -
                                              _bottom_left[1],
                                              _last_box_pos.size[0])
                                              )

                screen.blit(stat_surf, (5, _last_box_pos[1] +
                                        _last_box_pos[3] + 6))

            CURSOR_POS = (_x + font.size(''.join(letters))[0], _y)

            # ischeck_spelling(_disp_text, spell)
            # print(f'{_text_length(letters + _disp_text)/_keyboard_hits}')
            showTextBox(screen, read_box, font, _live_text[0])

            screen.blit(timer_disp, time_disp_rect.topleft)
            pygame.draw.rect(screen, (6, 34, 7.4), status_box, 0)

            screen.blit(font.render(_status_text, True, (255, 255, 255)),
                        status_box.topleft)

        # get the cursor blinking
        if time() % 1 > .5:
            screen.blit(
                font.render(' # ', True, (255, 255, 255)), CURSOR_POS)

        pygame.display.update()
        FPSCLOCK.tick(20)

    print("Saving text....")
    _saveTextBlock(textLines, filePath)
    checkSpell._stopThread()
    checkSpell = None

    pygame.quit()
    exit(0)
    print("Exiting....")


if __name__ == '__main__':
    main()

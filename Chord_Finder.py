# Chord Generator
# This code is licensed under CC0.
# http://creativecommons.org/publicdomain/zero/1.0/deed.ja

import numpy as np

# 目標：コード名を入力として、弾けるフレットポジションを自動生成する。

Chord_name = "B7"

Key_List = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
Key_List_fixed_width = ["C ", "C#", "D ", "D#", "E ", "F ", "F#", "G ", "G#", "A ", "A#", "B "]

# Represents Chord Modification Parts such as "dim", "m", "7aug" etc.
# Structure: tuple of ["Chord modification string", [added notes], [deleted notes], No more modification]
Mod_List = [
    ["", [0, 4, 7], [], False],
    ["5", [], [4, ], True],
    ["m", [3, ], [4, ], False],
    ["7", [10, ], [], False],
    ["M7", [11, ], [], False],
    ["9", [10, 14, ], [], False],
    ["add9", [14, ], [], False],
    ["b5", [6, ], [7, ], False],
    ["dim", [3, 6, ], [4, 7, ], False],
    ["aug", [8, ], [7, ], False],
    ["sus4", [5, ], [4, ], False],
    ["sus2", [2, ], [4, ], False]
]

# Represents Synonym in Chord (Left would be replaced to Right)
Synonym = [
    ["♭", "b"],
    ["-5", "b5"],
    ["maj7", "M7"],
    ["Db", "C#"],
    ["Eb", "D#"],
    ["Gb", "F#"],
    ["Ab", "G#"],
    ["Bb", "A#"]
]

# Fret Base Note  (Tuning) note: C == 0, C# == 1, ...
# Regular Tuning is [4, 9, 14, 19, 23, 28] (E, A, D, G, B, E)
# Lower should be former
Tuning = [4, 9, 14, 19, 23, 28]

# ***** Setting *****
Fret_Limit = 10  # note: up to (limit - 1) fret could be used.
Finger_Limit = 3  # note: up to (lowest press position) + (limit) allowed.


def Find_Notes(_cn):
    # Replace Synonym
    for pair_synonym in Synonym:
        _cn = _cn.replace(pair_synonym[0], pair_synonym[1])

    # Get Key
    Key = -1
    for i in range(12):
        if _cn.startswith(Key_List[i]):
            if i == 11 or not _cn.startswith(Key_List[i + 1]):
                Key = i
                _cn = _cn[len(Key_List[i]):]
    if Key == -1:
        raise Exception("ER01: Key does not exist")

    Relative_Notes = []
    # Get modification
    for i in range(len(Mod_List)):
        Mod_String = Mod_List[i][0]
        if _cn.startswith(Mod_String):
            # list adding and deleting notes up
            Adding_Notes = Mod_List[i][1]
            Deleting_Notes = Mod_List[i][2]
            Continue_Check = Mod_List[i][3]

            _cn = _cn[len(Mod_String):]
            for Deleting_Note in Deleting_Notes:
                Relative_Notes.remove(Deleting_Note)
            Relative_Notes.extend(Adding_Notes)
            if Continue_Check or _cn == "":
                break

    Relative_Notes.sort()

    return (Key, Relative_Notes)


def Get_NoteStr(i):
    return Key_List[i % 12]


def Get_NoteStr_Fixed(i):
    return Key_List_fixed_width[i % 12]


def is_valid(apc, _notes):
    # Finger_Limitの範囲内か
    base_string = 0
    maxp = 0
    minp = 0
    for string in range(len(Tuning)):
        if apc[string] != -1:
            base_string = string
            maxp = apc[string]
            minp = apc[string]
            break

    for string in range(base_string, len(Tuning)):
        if apc[string] != 0 and apc[string] != -1:
            maxp = max(maxp, apc[string])
            minp = min(minp, apc[string])
    if not (maxp - minp <= Finger_Limit):
        return False

    # 全構成音を含んでいるか
    apcnotes = []
    for string in range(len(Tuning)):
        apcnotes.append((Tuning[string] + apc[string]) % 12)
    Definite_Notes = [((_notes[0] + _notes[1][i]) % 12) for i in range(len(_notes[1]))]
    Definite_Notes.sort()
    for note in Definite_Notes:
        if not (note in apcnotes):
            return False

    return True


def Generate_Fret(_notes):
    # generate Available Fretboard Positions Matrix
    # get Key and Notes in Definite(C = 0) Position
    Key = _notes[0]
    Definite_Notes = [((_notes[0] + _notes[1][i]) % 12) for i in range(len(_notes[1]))]
    Definite_Notes.sort()

    # let's list up available presses
    available_chords = []

    # 1st thing: list up which fret can be pressed;
    # in type of pressable[string_number] = [1, 4,...](list of pressable frets)
    pressable = []
    for i in range(len(Tuning)):
        pressable_for_this_string = []
        for n in range(Fret_Limit):
            if ((Tuning[i] + n) % 12) in Definite_Notes:
                pressable_for_this_string.append(n)
        pressable.append(pressable_for_this_string)

    # 2nd thing: set key and generate chords according to key within +- Finger_Limit
    for base_string in range(len(Tuning) - 1):
        for base_press in range(Fret_Limit):
            if ((Tuning[base_string] + base_press) % 12) == _notes[0]:
                # got base note!!!!
                # then make another frets coordinate
                available_frets = [[-1, ]] * 6
                # mute lower
                for i in range(base_string):
                    available_frets[i] = [-1, ]
                # press base
                available_frets[base_string] = [base_press, ]
                # press higher
                for string in range(base_string + 1, len(Tuning)):
                    avfr = [-1, ]
                    for avst in pressable[string]:
                        if avst == 0 or ((base_press - Finger_Limit) <= avst <= (base_press + Finger_Limit)):
                            avfr.append(avst)
                    if len(avfr) > 1:
                        avfr.remove(-1)
                    available_frets[string] = avfr
                # available frets to available chords
                available_frets = np.array(available_frets)
                appendings = np.meshgrid(available_frets[0], available_frets[1], available_frets[2], available_frets[3],
                                         available_frets[4], available_frets[5])
                appendings = np.c_[
                    appendings[0].flatten(), appendings[1].flatten(), appendings[2].flatten(), appendings[3].flatten(),
                    appendings[4].flatten(), appendings[5].flatten()]
                appendings = appendings.tolist()
                for i in range(len(appendings)):
                    if is_valid(appendings[i], _notes):
                        available_chords.append(appendings[i])
                # for c0 in available_frets[0]:
                #     for c1 in available_frets[1]:
                #         for c2 in available_frets[2]:
                #             for c3 in available_frets[3]:
                #                 for c4 in available_frets[4]:
                #                     for c5 in available_frets[5]:
                #                         appending = [c0, c1, c2, c3, c4, c5]
                #                         if is_valid(appending, _notes):
                #                             available_chords.append(appending)

    # 3rd thing: print all
    ppdict = {}
    for press in available_chords:
        cp = ChordPress(press, _notes)
        ps, pt = cp.printChord()
        ppdict[ps] = pt
    ppdict = sorted(ppdict.items(), key=lambda x: x[1], reverse=True)
    for i in range(len(ppdict)):
        if ppdict[i][1]< -100:
            break
        print(ordinal(i + 1), "Position: ", ppdict[i][1], "pt")
        print(ppdict[i][0])


# this function is copied from https://qiita.com/boonrew/items/1d056c71978f27dca81c THANKS!
def ordinal(i):
    return str(i) + ({1: "st", 2: "nd", 3: "rd"}.get(i if 14 > i > 10 else i % 10) or "th")


# .press has info about which frets to press
class ChordPress:
    Prints = {"On-Fret": "●|",
              "Off-Fret": "  |",
              "Barre-Fret": "■|",
              "On-Start": "〇||",
              "Mute-Start": "×||",
              "Openable-Start": "△||",
              "Norm-Start": "  ||",
              "Partition": "---"}

    def __init__(self, press, notes):
        self.press = press
        self.notes = notes

    def evaluate(self):
        point = 0

        return point

    def printChord(self):
        printing_str = ""

        max_fret = 5
        for i in range(len(self.press)):
            max_fret = max(max_fret, self.press[i])

        # barre check
        # if lowest pos of chord (>0) is same and is not blocked by higher string then you can barre
        barre = False
        need_barre = False
        barre_from_string = -1
        barre_pos = -1
        for string in range(len(Tuning)):
            pos = self.press[string]
            if barre == False:
                if pos > 0:
                    barre = True
                    barre_from_string = string
                    barre_pos = pos
            else:
                if pos < barre_pos:
                    barre = False
                if pos == barre_pos:
                    need_barre = True
        if barre == False:
            need_barre = False

        # print and collect point
        finger_count = 0  # 少ないほどいい
        mute_count = 0  # 少ないほどいい
        pressing_sum = 0  # avgが2に近いほどいい
        pressing_count = 0
        barre_length = 0  # 長いほどいい
        lowest_press = 10000  # バレーを下回ると大減点
        highest_press = -10000  # high-lowが大きいと減点あり
        if need_barre:
            finger_count = 1
        for i in reversed(range(len(self.press))):
            if self.press[i] == -1:
                # must mute or open-able
                mute_count += 1
                if (Tuning[i] % 12) in self.notes[1]:
                    printing_str += "   "
                    printing_str += self.Prints["Openable-Start"]
                else:
                    printing_str += "   "
                    printing_str += self.Prints["Mute-Start"]
            else:
                printing_str += Get_NoteStr_Fixed(Tuning[i] + self.press[i]) + " "
                if self.press[i] == 0:
                    printing_str += self.Prints["On-Start"]
                else:
                    printing_str += self.Prints["Norm-Start"]
            for n in range(1, max_fret + 1):
                if n == self.press[i]:
                    pressing_sum += n
                    pressing_count += 1
                    if need_barre and n == barre_pos and i >= barre_from_string:
                        printing_str += self.Prints["Barre-Fret"]
                    else:
                        finger_count += 1
                        lowest_press = min(lowest_press, n)
                        highest_press = max(highest_press, n)
                        printing_str += self.Prints["On-Fret"]
                else:
                    if need_barre and n == barre_pos and i >= barre_from_string:
                        pressing_sum += n
                        pressing_count += 1
                        printing_str += self.Prints["Barre-Fret"]
                    else:
                        printing_str += self.Prints["Off-Fret"]
            printing_str += "\n"

        point = 200  # 基本点
        finger_points = [50, 48, 45, 35, 10, -100, -1000]
        point += finger_points[finger_count]  # 指数による減点
        point -= mute_count ** 4  # ミュート数への減点
        point -= int((float(pressing_sum) / float(pressing_count) - 2) * 30)  # 遠いポジションへの減点
        point -= (highest_press - lowest_press) ** 4
        if need_barre:
            point += (len(Tuning) - barre_from_string) * 2
            if barre_pos == lowest_press:
                point -= 100
            if barre_pos > lowest_press:
                point -= 500

        return (printing_str, point)


def main():
    Notes = Find_Notes(Chord_name)

    # print notes
    if True:
        print("Chord:\t{}".format(Chord_name))
        print("key:\t{}\t({}th)".format(Get_NoteStr(Notes[0]), Notes[0]))
        notes_string = [Get_NoteStr(Notes[0] + Notes[1][i]) for i in range(len(Notes[1]))]
        notes_string_int = "Key"
        for i in range(1, len(Notes[1])):
            notes_string_int += ", +" + str(Notes[1][i])
        print("notes:\t{}\t[{}]".format(notes_string, notes_string_int))

        # print("tuning_base: {}".format([Get_NoteStr(Tuning[i]) for i in range(len(Tuning))]))

    # Get "valid" Position in Fretboard
    Generate_Fret(Notes)


while True:
    Chord_name = input("Enter 'exit' to exit.\nEnter Chord:")
    if Chord_name == "exit":
        break
    main()

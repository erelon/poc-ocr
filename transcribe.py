from typing import List

import PIL
from kraken import transcribe as tr
from kraken.pageseg import segment


def do_overlap(box1: list, box2: list):
    l1x, l1y, r1x, r1y = box1
    l2x, l2y, r2x, r2y = box2
    # If one rectangle is on left side of other
    if (l1x > r2x or l2x > r1x):
        return False

    # If one rectangle is above other
    if (l1y > r2y or l2y > r1y):
        return False

    return True


def fix_overlapping_boxes(boxes: List[list]) -> List[list]:
    i = 0
    while i < len(boxes) - 1:
        for j in range(i + 1, i + 6):
            if (j >= len(boxes)):
                break
            if do_overlap(boxes[i], boxes[j]):
                boxes[i] = [min(boxes[i][0], boxes[j][0]), boxes[i][1], max(boxes[i][2], boxes[j][2]),
                            boxes[j][3]]
                boxes.remove(boxes[j])
                break
        i += 1
    return boxes


def transcribe(book_pages_png: list, book_path: str = "book", name_of_transcribed_file="html_transcribe"):
    """
    A warper for transcribing book pages

    :param book_pages_png: List with all of the pages that need to be transcribed
    :param book_path: The path of the pages
    :return: None
    """
    t_interface = tr.TranscriptionInterface()
    t_interface.text_direction = "rl"
    for page in book_pages_png:
        im = PIL.Image.open(f"{book_path}/{page}").convert(mode='1')
        # Create segments with the basic segmentor
        segments = segment(im, 'horizontal-rl')
        # Manualy fix some errors in the segmentation
        boxes = fix_overlapping_boxes(segments['boxes'])
        segments['boxes'] = boxes
        t_interface.add_page(im, segments)
    f = open(f"{name_of_transcribed_file}.html", "wb+")
    t_interface.write(f)
    f.close()


def filler(pages_paths: List[str], untranscribed_html_path: str):
    ready_text = dict()
    for i in range(len(pages_paths)):
        ready_text[f"page_{i + 1}"] = open(pages_paths[i])

    untranscribed = open(untranscribed_html_path)
    untranscribed_list = untranscribed.readlines()
    pages_to_lines = dict()
    for line in untranscribed_list:
        if "page container" in line:
            curr_page = line[line.rfind("page"):-3]
            pages_to_lines[curr_page] = list()
        if "line_" in line and "<li" in line:
            begin = line[line.find("line"):]
            refine = begin[:begin.find('"')]
            pages_to_lines[curr_page].append(refine)

    for page in pages_to_lines.keys():
        txt_page = ready_text[page]
        txt_lines = txt_page.readlines()
        j = 0
        i = 0
        while i < len(pages_to_lines[page]) and j < len(txt_lines):
            print(f"Replace {pages_to_lines[page][i]} to: {txt_lines[j]}? [y,n,s,a,e,h,b]")
            ans = input()
            if ans == 'y':
                pages_to_lines[page][i] = txt_lines[j]
            elif ans == 'n':
                print("Write the correct input:")
                cur_in = input()
                pages_to_lines[page][i] = cur_in
                j -= 1
            elif ans == "s":
                print(f"Skipping: {txt_lines[j]}")
                i -= 1
            elif ans == "e":
                # Leave empty or clean
                pages_to_lines[page][i] = ""
                j -= 1
            elif ans == "b":
                # Go back:
                i -= 2
                j -= 2
            elif ans == 'a':
                # Abort
                break
            else:
                try:
                    nans = int(ans)
                    for k in range(nans):
                        pages_to_lines[page][i] = txt_lines[j]
                        i += 1
                        j += 1
                    i -= 1
                    j -= 1
                except:
                    print("try again:")
                    print("y - Yes, n - No, s- Skip line in txt, e - skip line on image, a - stop here, b - back")
                    i -= 1
                    j -= 1
            j += 1
            i += 1

    all_lines = list()
    [all_lines.extend(v) for v in pages_to_lines.values()]
    i, j = 0, 0
    while i < len(untranscribed_list):
        if "line_" in untranscribed_list[i] and "<li" in untranscribed_list[i]:
            if "line" not in all_lines[j]:
                untranscribed_list.insert(i + 1, all_lines[j])
            j += 1
            i += 1
        i += 1

    f = open(f"full_{untranscribed_html_path}", "w+")
    f.writelines(untranscribed_list)
    for fd in ready_text.values():
        fd.close()

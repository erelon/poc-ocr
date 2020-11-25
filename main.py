import os
import random

import PIL
import kraken.ketos

from typing import List

from kraken import ketos
from kraken.lib.train import KrakenTrainer
from lxml import etree
from pdf2image.pdf2image import convert_from_path

from transcribe import transcribe, filler

from bs4 import BeautifulSoup
import re


def flip_by_line(string: str) -> str:
    fix_txt = ""
    for line in string.splitlines():
        l = line.split()
        l.reverse()
        for word in l:
            fix_txt += word + " "
        fix_txt += "\n"
    return fix_txt


def raw_to_preclean(raw_path: str = "raw_txt", preclean_path: str = "preclean_txt") -> None:
    for file in os.listdir(raw_path):
        f = open(raw_path + "/" + file)
        txt = f.read()
        f.close()

        fixed_txt = flip_by_line(txt)

        f = open(preclean_path + "/" + file, "w")
        f.write(fixed_txt)
        f.close()


def show_boxes_on_img(img: PIL.Image, boxes: List[list]) -> PIL.Image:
    from PIL import ImageDraw
    drawing_obj = ImageDraw.Draw(img)
    for box in boxes:
        drawing_obj.rectangle(box, fill=None, outline='black')
    return img


def learn(transcribe_path, validation_size=0.3, batch_size: int = 1, lag: int = 5, min_delta: float = 0,
          learning_rate: float = 0.001, threads: int = 1, augment: bool = False) -> None:
    """
    Creates models out of learning from the transcribe file

    :param transcribe_path: The path of the data to learn from
    :param validation_size: The size of validation set
    :param batch_size: Batch size to learn in every epoch
    :param lag: Number of iterations without any improvement that are allowed
    :param min_delta: The goal min value of accuracy
    :param learning_rate: Learning rate
    :param threads: Number of threads to run on
    :param augment: Augment the data
    :return: None
    """
    if (0 == os.fork()):
        exec(ketos.extract(["--output", "output_directory", transcribe_path]))
    os.wait()

    pngs = sorted(["output_directory/" + f for f in os.listdir("output_directory") if "png" in f])
    random.shuffle(pngs)

    trian = pngs[:int(len(pngs) * (1 - validation_size))]
    test = pngs[int(len(pngs) * (1 - validation_size)):]

    def _update_progress():
        print('.', end='')

    def _print_eval(epoch, accuracy, **kwargs):
        print(
            f"epoch: {epoch}, accuracy: {accuracy}, right: {kwargs['chars'] - kwargs['error']}, errors: {kwargs['error']}")

    hp = kraken.lib.default_specs.RECOGNITION_HYPER_PARAMS
    hp["batch_size"] = batch_size
    hp["lag"] = lag
    hp["min_delta"] = min_delta
    hp["lrate"] = learning_rate

    kt = KrakenTrainer.recognition_train_gen(hyper_params=hp, training_data=trian, evaluation_data=test,
                                             format_type='path', threads=threads, augment=augment)
    kt.run(_print_eval, _update_progress)


if __name__ == '__main__':
    # # Create png from pdf
    # convert_from_path("raw_book/az_nidberu_part_a.pdf", dpi=600, use_pdftocairo=True, output_folder="book",
    #                   thread_count=3, output_file="az_nidberu_part_a")

    vv = [f"clean_txt/page{i}.txt" for i in range(16, 25)]
    filler(vv, "az nidberu 16 to 24.html")

    # # Transcribe
    # vv = [f"az_nidberu_part_a0001-0{i}.png" for i in range(16, 25)]
    # transcribe(vv, name_of_transcribed_file="az nidberu 16 to 24")

    # learn("az nidberu 3 pages full.html", batch_size=4, lag=50, min_delta=0.1, learning_rate=0.1, threads=4,
    #       augment=False)

import plac

from .command_line import run_ginza, run_ginzame


def main_ginzame():
    plac.call(run_ginzame)


def main_ginza():
    plac.call(run_ginza)


if __name__ == "__main__":
    plac.call(run_ginza)

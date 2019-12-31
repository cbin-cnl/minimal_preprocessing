from subprocess import Popen, PIPE
import shlex
import time
import logging


def set_logging(loglevel=logging.INFO):
    logging.basicConfig(
        filename="app.log", filemode="w", format="%(message)s", level=logging.DEBUG
    )

    console = logging.StreamHandler()
    console.setLevel(loglevel)

    logging.getLogger("").addHandler(console)


def print_cmd(cmd_str):
    logging.info(cmd_str.replace(" -", "\n -"))


def run_cmd(env, refit_cmd):
    start_time = time.time()
    print_cmd(refit_cmd)
    p = Popen(shlex.split(refit_cmd), stdout=PIPE, stderr=PIPE, env=env)
    stdout, stderr = p.communicate()
    logging.debug(stdout.decode("UTF-8"))
    logging.debug(stderr.decode("UTF-8"))
    logging.debug("Elapsed time: {:.2f}s".format(time.time() - start_time))

import get_pip
import logging
import subprocess
import sys
import os
import time
from client import Network

# Basic logging configuration

logFile = os.path.join('log', 'game.log')

stdout_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(logFile)
handlers = [stdout_handler, file_handler]

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s:%(name)s: %(levelname)s : %(message)s',
                    handlers=handlers
                    )

log = logging.getLogger(__name__)


# Installs pygame library and pip
#   dependencies included in requirements.txt
#       Skipped when dependencies are already met

def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])


try:
    log.warning("Trying to import pygame")
    import pygame
    log.info("Success..")
    log.info("Running game..")
except Exception:
    log.info("Pygame not installed")

    try:
        resp = input("Do you want to install pygame via pip? [Y/N]")
        while resp is not "Y" or "N":
            resp2 = input("Select again..[Y/N]")
            if resp2 == "Y":
                log.info("Trying to install pygame via pip")
                import pip
                install("pygame")
                log.info("Pygame has been installed")
                break

            elif resp2 == "N":
                log.info("Pygame library required to play game. Exiting...")
                sys.exit(0)

    except Exception:
        log.info("Pip not installed on system")
        log.info("Trying to install Pip..")
        get_pip.main()
        log.info("Pip has been installed")
        time.sleep(3)
        try:
            log.info("Proceeding to install pygame")
            import pip
            install("pygame")
            log.info("Pygame has been installed")
        except Exception:
            log.info("Pygame could not be installed")
            sys.exit(0)

import pygame

pygame.font.init()

board = pygame.transform.scale(pygame.image.load(os.path.join(
        "img", "board_alt.png")),
        (750, 750)
        )
chessbg = pygame.image.load(os.path.join("img", "chessbg.png"))
rect = (113, 113, 525, 525)

turn = "w"


# Rendering is defined by RGB color picker
#   i.e: White (255,255,255)

def menu_screen(win, name, config):
    global bo, chessbg
    run = True
    offline = False

    while run:
        win.blit(chessbg, (0, 0))
        small_font = pygame.font.SysFont("comicsans", 50)

        if offline:
            off = small_font.render(
                "Server Offline, Try Again Later...", 1, (255, 0, 0)
                )
            win.blit(off, (width / 2 - off.get_width() / 2, 500))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                run = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                offline = False
                try:
                    bo = connect(config)
                    run = False
                    main()
                    break
                except Exception:
                    log.error("Could not connect: Server Offline")
                    offline = True


'''
Pygame UI Rendering configuration
    In full accordance with pygame code conventions
'''

# Create configuration for connection


def createConnectionConfig():
    connectionConfig = {}
    hostAddr = input("Enter server IP to connect to: ")
    connectionConfig['hostIp'] = hostAddr
    if not hostAddr:
        log.info("No IP specified. Defaulting to localhost...")
    portNo = input("Port number: ")
    if not portNo:
        log.info("No port specified. Default port: 5555")
    else:
        connectionConfig['port'] = int(portNo) if portNo else None

    return connectionConfig


def redraw_gameWindow(win, bo, p1, p2, color, ready):
    win.blit(board, (0, 0))
    bo.draw(win, color)

    formatTime1 = str(int(p1//60)) + ":" + str(int(p1 % 60))
    formatTime2 = str(int(p2 // 60)) + ":" + str(int(p2 % 60))
    if int(p1 % 60) < 10:
        formatTime1 = formatTime1[:-1] + "0" + formatTime1[-1]
    if int(p2 % 60) < 10:
        formatTime2 = formatTime2[:-1] + "0" + formatTime2[-1]

    font = pygame.font.SysFont("comicsans", 30)
    try:
        txt = font.render(
            bo.p1Name + "\'s Time: " + str(formatTime2), 1, (255, 255, 255)
            )
        txt2 = font.render(
            bo.p2Name + "\'s Time: " + str(formatTime1), 1, (255, 255, 255)
            )
    except Exception as e:
        log.error(e)
    win.blit(txt, (520, 10))
    win.blit(txt2, (520, 700))

    txt = font.render("Press q to Quit", 1, (255, 255, 255))
    win.blit(txt, (10, 20))

    if color == "s":
        txt3 = font.render("SPECTATOR MODE", 1, (255, 0, 0))
        win.blit(txt3, (width/2-txt3.get_width()/2, 10))

    if not ready:
        show = "Waiting for Player"
        if color == "s":
            show = "Waiting for Players"
        font = pygame.font.SysFont("comicsans", 80)
        txt = font.render(show, 1, (255, 0, 0))
        win.blit(txt, (width/2 - txt.get_width()/2, 300))

    if not color == "s":
        font = pygame.font.SysFont("comicsans", 30)
        if color == "w":
            txt3 = font.render("YOU ARE WHITE", 1, (255, 0, 0))
            win.blit(txt3, (width / 2 - txt3.get_width() / 2, 10))
        else:
            txt3 = font.render("YOU ARE BLACK", 1, (255, 0, 0))
            win.blit(txt3, (width / 2 - txt3.get_width() / 2, 10))

        if bo.turn == color:
            txt3 = font.render("YOUR TURN", 1, (255, 0, 0))
            win.blit(txt3, (width / 2 - txt3.get_width() / 2, 700))
        else:
            txt3 = font.render("THEIR TURN", 1, (255, 0, 0))
            win.blit(txt3, (width / 2 - txt3.get_width() / 2, 700))

    pygame.display.update()


def end_screen(win, text):
    pygame.font.init()
    font = pygame.font.SysFont("comicsans", 80)
    txt = font.render(text, 1, (255, 0, 0))
    win.blit(txt, (width / 2 - txt.get_width() / 2, 300))
    pygame.display.update()

    pygame.time.set_timer(pygame.USEREVENT+1, 3000)

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                run = False
            elif event.type == pygame.KEYDOWN:
                run = False
            elif event.type == pygame.USEREVENT+1:
                run = False


# Function plotting click positions in the game
def click(pos):
    """
    :return: pos (x, y) in range 0-7 0-7
    """
    x = pos[0]
    y = pos[1]
    if rect[0] < x < rect[0] + rect[2]:
        if rect[1] < y < rect[1] + rect[3]:
            divX = x - rect[0]
            divY = y - rect[1]
            i = int(divX / (rect[2]/8))
            j = int(divY / (rect[3]/8))
            return i, j

    return -1, -1

# Client connect


def connect(connection_config):
    global n
    n = Network(**connection_config)
    return n.board

# Main


def main():
    global turn, bo, name

    color = bo.start_user
    count = 0

    bo = n.send("update_moves")
    bo = n.send("name " + name)
    clock = pygame.time.Clock()
    run = True

    while run:
        if not color == "s":
            p1Time = bo.time1
            p2Time = bo.time2
            if count == 60:
                bo = n.send("get")
                count = 0
            else:
                count += 1
            clock.tick(30)

        try:
            redraw_gameWindow(win, bo, p1Time, p2Time, color, bo.ready)
        except Exception as e:
            log.error(e)
            end_screen(win, "Other player left")
            run = False
            break

        if not color == "s":
            if p1Time <= 0:
                bo = n.send("winner b")
            elif p2Time <= 0:
                bo = n.send("winner w")

            if bo.check_mate("b"):
                bo = n.send("winner b")
            elif bo.check_mate("w"):
                bo = n.send("winner w")

        if bo.winner == "w":
            end_screen(win, "White is the Winner!")
            run = False
        elif bo.winner == "b":
            end_screen(win, "Black is the winner")
            run = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                quit()
                pygame.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and color != "s":
                    # quit game
                    if color == "w":
                        bo = n.send("winner b")
                    else:
                        bo = n.send("winner w")

                if event.key == pygame.K_RIGHT:
                    bo = n.send("forward")

                if event.key == pygame.K_LEFT:
                    bo = n.send("back")

            if event.type == pygame.MOUSEBUTTONUP and color != "s":
                if color == bo.turn and bo.ready:
                    pos = pygame.mouse.get_pos()
                    bo = n.send("update moves")
                    i, j = click(pos)
                    bo = n.send("select " + str(i) + " " + str(j) + " " + color)

    n.disconnect()
    bo = 0
    menu_screen(win)


if __name__ == '__main__':
    name = input("Please type your name: ")
    log.info("Profile successfully created!")
    config = createConnectionConfig()
    width = 750  # log-in UI display width
    height = 750  # log-in UI display height
    win = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Chess Game")
    menu_screen(win, name, config)

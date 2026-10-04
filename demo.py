from app import Application
import logging

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt= "%H:%M:%S"
)

def main():
    app = Application("EightCount.db")
    app.run()

if __name__ == "__main__":
    main()
import logging
from pytrade.connector.quik.QuikConnector import QuikConnector


class App:
    """
    Main application. Build strategy and run.
    """

    @staticmethod
    def main():
        """
        Application entry point
        :return: None
        """
        QuikConnector().run()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S")
    App().main()

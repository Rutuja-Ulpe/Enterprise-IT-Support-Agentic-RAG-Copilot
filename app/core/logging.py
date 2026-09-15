import logging 
def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        fomat="%(asctime)s | %(levelname)s | %(name)s |%(message)s", 
    )
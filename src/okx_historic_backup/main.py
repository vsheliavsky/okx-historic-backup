from utilities.helpers import load_defaults, setup_logging
from utilities.input_param_parser import parse_input_args


def main():
    logger = setup_logging()
    logger.info("Starting OKX Historic Backup Tool")

    defaults = load_defaults()

    input_params = parse_input_args(defaults)


if __name__ == "__main__":
    main()

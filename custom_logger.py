import logging

# logging.basicConfig(level=logging.INFO, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

main_logger = logging.getLogger('Main')
backend_logger = logging.getLogger('Backend')
main_logger.setLevel(20)
backend_logger.setLevel(20)

main_handler = logging.FileHandler('main.log')
backend_handler = logging.FileHandler('backend.log')

main_handler.setFormatter(formatter)
backend_handler.setFormatter(formatter)

main_logger.addHandler(main_handler)
backend_logger.addHandler(backend_handler)


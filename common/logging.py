import logging

def decorator(func):
    def wrap(*args, **kwargs):
        # Log the function name and arguments
        print(f"-> {func.__name__.upper()} Started ")
        print(f"-> Calling {func.__name__} with args: {args}, kwargs: {kwargs}")

        # Call the original function
        result = func(*args, **kwargs)

        # Log the return value
        print(f"-> {func.__name__.upper()} returned: \n{result}")
        print(f"-> {func.__name__.upper()} Completed")
        # Return the result
        return result

    return wrap


class Logger:
    _logger = logging.getLogger()
    _logger.setLevel(logging.INFO)

    if not _logger.handlers:
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        _logger.addHandler(stream_handler)

    @staticmethod
    def get_logger():
        return Logger._logger

import os
import inspect

current_file = os.path.basename(__file__)

class Total_Logger():
    def handle_messagee(self, textt):
        print(textt)  # Replace this with actual logging implementation if needed

    def handle_exception(self, error_message):  
        self.handle_messagee(error_message)

    def log_exceptions_decorator(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                current_frame = inspect.currentframe()
                caller_frame = current_frame.f_back
                file_name = caller_frame.f_code.co_filename
                line_number = caller_frame.f_lineno
                exception_message = str(ex)
                self.handle_exception(f"Error occurred in file '{file_name}', line {line_number}: {exception_message}")
                # Optionally re-raise the exception if needed
                # raise
        return wrapper
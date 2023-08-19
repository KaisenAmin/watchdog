import os
import datetime


class Logger:
    @staticmethod
    def create_log_file():
        file_address = os.path.dirname(__file__)
        try:
            with open(file_address + "\\" + "Logger.txt", "a+") as file:
                pass 
        except IOError as error:
            file = open(file_address + "\\" + "Logger.txt", "a+")

    @staticmethod
    def log(log_message, flag = "INFO", file_name = "Logger.txt"):
        try:
            file_address = os.path.dirname(__file__)
            with open(file_address + "\\" + f"{file_name}", "a+") as file:
                file.write(f"<<{flag}>> {datetime.datetime.now().date()} --- {datetime.datetime.now().time()} >>>> {log_message}\n")
        except IOError as error:
            pass 
        except Exception as error:
            print(error)




import subprocess

class Shell:
    def __init__(self):
        self.colors = {
            "black":  subprocess.check_output(["tput", "setaf", "0"]).decode(),
            "red":  subprocess.check_output(["tput", "setaf", "1"]).decode(),
            "green":  subprocess.check_output(["tput", "setaf", "2"]).decode(),
            "yellow":  subprocess.check_output(["tput", "setaf", "3"]).decode(),
            "blue":  subprocess.check_output(["tput", "setaf", "4"]).decode(),
            "magenta":  subprocess.check_output(["tput", "setaf", "5"]).decode(),
            "cyan":  subprocess.check_output(["tput", "setaf", "6"]).decode(),
            "white":  subprocess.check_output(["tput", "setaf", "7"]).decode(),
            "reset":  subprocess.check_output(["tput", "sgr0"]).decode(),
        }

        self.status_colors = {
            "create": self.colors["green"],
            "delete": self.colors["red"],
            "update": self.colors["blue"],
            "download": self.colors["magenta"],
            "exist": self.colors["yellow"],
            "reset": self.colors["reset"]
        }
          
    def say_status(self, status, body, color = None):
        color = (color and self.colors[color]) or self.status_colors.get(status, self.colors["cyan"])
        print(f"{color}{status.rjust(14)} {self.colors['reset']}{body}")

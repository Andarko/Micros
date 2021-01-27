from PyQt5.QtWidgets import QDialog


class ProgramSettings(object):
    def __init__(self):
        self.fullLoadImageMemoryLimit = eval('1024*1024')


class SettingsDialog(QDialog):
    def __init__(self, programSettings: ProgramSettings):
        super().__init__()
import sys
from PyQt5.QtCore import QUrl, Qt, QTime
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QSlider, QLabel
from PyQt5.uic import loadUi
import resources_rc
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from mutagen import File


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.isPlaying = None
        loadUi("new.ui", self)  # Load the UI file

        self.homePushButton.clicked.connect(self.switch_to_home_page)
        self.playlistsPushButton.clicked.connect(self.switch_to_playlists_page)
        self.favoritesPushButton.clicked.connect(self.switch_to_favorites_page)
        self.recentsPushButton.clicked.connect(self.switch_to_recents_page)
        self.settingsPushButton.clicked.connect(self.switch_to_settings_page)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        # Connect UI elements to methods
        self.pushButtonPlayPause.clicked.connect(self.play_pause_song)

        # Connect the media player to the slider and labels
        self.mediaPlayer.positionChanged.connect(self.update_position)
        self.mediaPlayer.durationChanged.connect(self.update_duration)

        # Connect slider to allow seeking in the song
        self.musicSlider.sliderMoved.connect(self.set_position)

        # Handle potential media player errors
        self.mediaPlayer.error.connect(self.handle_media_error)

        # Metadata labels
        self.labelSongName = self.findChild(QLabel, 'labelSongName')
        self.labelArtist = self.findChild(QLabel, 'labelArtist')

    def switch_to_home_page(self):
        self.stackedWidget.setCurrentIndex(0)

    def switch_to_playlists_page(self):
        self.stackedWidget.setCurrentIndex(1)

    def switch_to_favorites_page(self):
        self.stackedWidget.setCurrentIndex(2)

    def switch_to_recents_page(self):
        self.stackedWidget.setCurrentIndex(3)

    def switch_to_settings_page(self):
        self.stackedWidget.setCurrentIndex(4)

    def play_pause_song(self):
        if self.isPlaying:
            self.mediaPlayer.pause()
            self.pushButtonPlayPause.setIcon(QIcon("utils/images/play.svg"))
            self.isPlaying = False
        else:
            if self.mediaPlayer.state() == QMediaPlayer.StoppedState:
                song_url = QUrl.fromLocalFile("C:/Users/deno/OneDrive/Music/Eminem/Kamikaze/10 Fall.mp3")
                content = QMediaContent(song_url)
                self.mediaPlayer.setMedia(content)
                self.extract_metadata("C:/Users/deno/OneDrive/Music/Eminem/Kamikaze/10 Fall.mp3")

            self.mediaPlayer.play()
            self.pushButtonPlayPause.setIcon(QIcon("utils/images/pause.svg"))
            self.isPlaying = True

    def update_position(self, position):
        """
        Update the slider and current time label as the song plays.
        """
        self.musicSlider.setValue(position)
        current_time = QTime(0, 0, 0).addMSecs(position)
        self.labelCurrentDuration.setText(current_time.toString("mm:ss"))

    def update_duration(self, duration):
        """
        Update the slider's range and total duration label when the song starts.
        """
        self.musicSlider.setRange(0, duration)
        total_duration = QTime(0, 0, 0).addMSecs(duration)
        self.labelTotalDuration.setText(total_duration.toString("mm:ss"))

    def set_position(self, position):
        """
        Seek the media player to the new position when the slider is moved.
        """
        self.mediaPlayer.setPosition(position)

    def handle_media_error(self):
        print(f"Error: {self.mediaPlayer.errorString()}")

    def extract_metadata(self, file_path):
        """
        Extract and display metadata from the audio file.
        """
        audio_file = File(file_path)
        if audio_file:
            self.labelSongName.setText(audio_file.tags.get('TIT2', ['Unknown'])[0])
            self.labelArtist.setText(audio_file.tags.get('TPE1', ['Unknown'])[0])
        else:
            self.labelSongName.setText("Unknown")
            self.labelArtist.setText("Unknown")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

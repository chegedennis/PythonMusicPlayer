import os
import sys
import resources_rc
from PyQt5.QtCore import QUrl, QDir, pyqtSignal, Qt, QTime
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import QLabel, QMainWindow, QGridLayout, QApplication, QFileDialog, QFrame, QVBoxLayout
from PyQt5.uic import loadUi
from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import ID3


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StyledLabel(QFrame):
    def __init__(self, parent=None):
        super(StyledLabel, self).__init__(parent)
        self.setFixedSize(200, 200)
        self.setObjectName("styled-label")
        self.vlay = QVBoxLayout(self)
        self.vlay.setContentsMargins(0, 0, 0, 0)
        self.vlay.setSpacing(0)

        self.cover = QLabel(self)
        self.cover.setFixedSize(200, 150)
        self.cover.setStyleSheet("border-radius: 10px;")

        self.title = QLabel(self)
        self.title.setObjectName("track-item-title")
        self.artist = QLabel(self)
        self.artist.setObjectName("track-item-artist")

        self.vlay.addWidget(self.cover, alignment=Qt.AlignCenter)
        self.vlay.addWidget(self.title, alignment=Qt.AlignCenter)
        self.vlay.addWidget(self.artist, alignment=Qt.AlignCenter)

        self.setStyleSheet("""
            #styled-label {
                background-color: rgb(45, 49, 48);
                border-radius: 10px;
                padding: 10px;
            }
            #track-item-title {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            #track-item-artist {
                color: lightgray;
                font-size: 12px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click()

    def on_click(self):
        # Handle click event
        print("StyledLabel clicked")

    def set_cover(self, imgpath):
        try:
            pixmap = QPixmap(imgpath)
            pixmap = pixmap.scaled(self.cover.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.cover.setPixmap(pixmap)
        except Exception as e:
            print(f"Error setting cover: {e}")
            self.cover.setPixmap(QPixmap(":/icons/images/icons8-album-48.png"))

    def set_title(self, title):
        self.title.setText(title)

    def set_artist(self, artist):
        self.artist.setText(artist)


def extract_album_art(file_path):
    image_data = None
    try:
        if file_path.lower().endswith('.mp3'):
            audio_file = ID3(file_path)
            for tag in audio_file.getall('APIC'):
                image_data = tag.data
                break
        elif file_path.lower().endswith('.flac'):
            audio_file = FLAC(file_path)
            for tag in audio_file.pictures:
                image_data = tag.data
                break
        if image_data:
            image = QImage.fromData(image_data)
            if not image.isNull():
                return QPixmap(image)
    except Exception as e:
        print(f"Error extracting album art: {e}")
    return None


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.isPlaying = None
        self.current_file_path = None
        self.current_folder_path = None  # Initialize this to avoid crashes

        loadUi("new.ui", self)

        self.homePushButton.clicked.connect(self.switch_to_home_page)
        self.playlistsPushButton.clicked.connect(self.switch_to_playlists_page)
        self.favoritesPushButton.clicked.connect(self.switch_to_favorites_page)
        self.recentsPushButton.clicked.connect(self.switch_to_recents_page)
        self.settingsPushButton.clicked.connect(self.switch_to_settings_page)

        self.gridLayout = QGridLayout(self.scrollAreaWidgetContents_5)
        self.scrollAreaWidgetContents_5.setLayout(self.gridLayout)

        self.loadFolderButton.clicked.connect(self.load_folder)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.StreamPlayback)
        self.pushButtonPlayPause.clicked.connect(self.toggle_play_pause)

        self.labelSongName = self.findChild(QLabel, 'labelSongName')
        self.labelArtist = self.findChild(QLabel, 'labelArtist')

        # Connect the media player to the slider and labels
        self.mediaPlayer.positionChanged.connect(self.update_position)
        self.mediaPlayer.durationChanged.connect(self.update_duration)

        # Connect slider to allow seeking in the song
        self.musicSlider.sliderMoved.connect(self.set_position)

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

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", QDir.homePath())
        if folder_path:
            self.current_folder_path = folder_path  # Save folder path
            self.load_songs_into_scroll_area(folder_path)

    def load_songs_into_scroll_area(self, folder_path):
        layout = self.gridLayout
        scroll_area_width = self.scrollAreaWidgetContents_5.width()  # Use the contents widget width
        widget_width = 200  # Width of each song widget (adjust as necessary)
        max_columns = max(1, scroll_area_width // widget_width)  # Calculate max columns

        # Ensure the scroll area only scrolls vertically
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Clear existing widgets from the grid layout
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

        supported_formats = ['.mp3', '.flac', '.wav', '.m4a']
        row, col = 0, 0

        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and any(file_name.lower().endswith(ext) for ext in supported_formats):
                self.add_song_label(file_path, row, col)
                col += 1
                if col >= max_columns:
                    col = 0
                    row += 1

    def resizeEvent(self, event):
        # Only reload songs if a folder has been loaded
        if self.current_folder_path:
            self.load_songs_into_scroll_area(self.current_folder_path)  # Reload with new size
        super().resizeEvent(event)

    def add_song_label(self, file_path, row, col):
        try:
            audio_file = File(file_path)
            if audio_file and audio_file.tags:
                song_title = audio_file.tags.get('TIT2', ['Unknown Title'])[0]
                artist_name = audio_file.tags.get('TPE1', ['Unknown Artist'])[0]
            else:
                song_title = os.path.basename(file_path)
                artist_name = "Unknown Artist"

            album_art = extract_album_art(file_path)

            song_label = StyledLabel(self)
            song_label.set_cover(album_art if album_art else ":/icons/images/icons8-album-48.png")
            song_label.set_title(song_title)
            song_label.set_artist(artist_name)

            song_label.setProperty('file_path', file_path)
            song_label.on_click = lambda: self.song_label_clicked(file_path)

            self.gridLayout.addWidget(song_label, row, col)
        except Exception as e:
            print(f"Error adding song label: {e}")

    def song_label_clicked(self, file_path):
        self.current_file_path = file_path
        self.play_song(file_path)

    def play_song(self, file_path):
        song_url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(song_url)
        self.mediaPlayer.setMedia(content)
        self.extract_metadata(file_path)
        self.mediaPlayer.play()
        self.pushButtonPlayPause.setIcon(QIcon("utils/images/pause.svg"))
        self.isPlaying = True

    def toggle_play_pause(self):
        if self.isPlaying:
            self.mediaPlayer.pause()
            self.pushButtonPlayPause.setIcon(QIcon("utils/images/play.svg"))
            self.isPlaying = False
        else:
            if self.current_file_path:
                self.play_song(self.current_file_path)

    def extract_metadata(self, file_path):
        audio_file = File(file_path)
        if audio_file and audio_file.tags:
            song_title = audio_file.tags.get('TIT2', ['Unknown Title'])[0]
            artist_name = audio_file.tags.get('TPE1', ['Unknown Artist'])[0]
        else:
            song_title = os.path.basename(file_path)
            artist_name = "Unknown Artist"
        self.labelSongName.setText(song_title)
        self.labelArtist.setText(artist_name)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

"""Сервис для управления фоновой музыкой"""
import logging
import os
import random
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QTimer

logger = logging.getLogger(__name__)

class MusicService:
    """Класс для управления фоновой музыкой"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.music_folder = os.path.join(base_dir, "music")
        self.music_enabled = True
        self.current_track = None
        self.track_list = []
        self.playback_queue = []
        
        # Создаем плеер для музыки
        self.music_player = QMediaPlayer()
        self.music_output = QAudioOutput()
        self.music_player.setAudioOutput(self.music_output)
        
        # Устанавливаем громкость
        from .constants import Constants
        self.music_output.setVolume(Constants.MUSIC_VOLUME)
        
        # Таймер для проверки окончания трека
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self._check_music_status)
        self.check_timer.start(1000)  # Проверяем каждую секунду
        
        # Загружаем список треков
        self._load_track_list()
        
        # Подключаем сигнал окончания трека
        self.music_player.mediaStatusChanged.connect(self._on_media_status_changed)
    
    def _load_track_list(self):
        """Загружает список доступных музыкальных файлов"""
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder, exist_ok=True)
            return
        
        supported_formats = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
        self.track_list = []
        
        for file in os.listdir(self.music_folder):
            if any(file.lower().endswith(ext) for ext in supported_formats):
                self.track_list.append(file)
        
        # Создаем очередь воспроизведения
        self._create_playback_queue()
    
    def _create_playback_queue(self):
        """Создает случайную очередь воспроизведения без повторов"""
        self.playback_queue = self.track_list.copy()
        random.shuffle(self.playback_queue)
    
    def set_music_enabled(self, enabled: bool):
        """Включает или выключает музыку"""
        self.music_enabled = enabled
        if enabled:
            self.play_random_track()
        else:
            self.stop_music()
    
    def play_random_track(self):
        """Воспроизводит следующий трек из очереди без повторов"""
        if not self.music_enabled or not self.track_list:
            return
        
        # Если очередь пуста, создаем новую
        if not self.playback_queue:
            self._create_playback_queue()
        
        # Берем следующий трек из очереди
        if self.playback_queue:
            track = self.playback_queue.pop(0)  # Берем первый трек и удаляем его из очереди
            track_path = os.path.join(self.music_folder, track)
            
            if os.path.exists(track_path):
                try:
                    self.music_player.stop()
                    self.music_player.setSource(QUrl.fromLocalFile(track_path))
                    self.music_player.play()
                    self.current_track = track
                except Exception as exc:
                    logger.exception("Cannot play music track '%s': %s", track_path, exc)
    
    def stop_music(self):
        """Останавливает музыку"""
        self.music_player.stop()
        self.current_track = None
    
    def _check_music_status(self):
        """Проверяет статус музыки и переключает трек если нужно"""
        if (self.music_enabled and
            self.music_player.playbackState() == QMediaPlayer.StoppedState and
            self.music_player.mediaStatus() == QMediaPlayer.EndOfMedia):
            self.play_random_track()
    
    def _on_media_status_changed(self, status):
        """Обработчик изменения статуса медиа"""
        if status == QMediaPlayer.EndOfMedia:
            # Трек закончился, запускаем следующий
            QTimer.singleShot(100, self.play_random_track)
        elif status == QMediaPlayer.InvalidMedia:
            # Невалидный трек, пробуем следующий
            logger.warning("Invalid music track encountered: %s", self.current_track)
            QTimer.singleShot(10, self.play_random_track)
    
    def get_current_track(self):
        """Возвращает название текущего трека"""
        return self.current_track
    
    def is_playing(self):
        """Проверяет, играет ли музыка"""
        return self.music_player.playbackState() == QMediaPlayer.PlayingState
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.check_timer:
            self.check_timer.stop()
            self.check_timer = None
        if self.music_player:
            self.music_player.stop()
            self.music_player.setSource(QUrl())  # Очищаем источник
        if self.music_output:
            self.music_output = None
        self.playback_queue = []
        self.track_list = []
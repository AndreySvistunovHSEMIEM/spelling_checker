"""Сервис для работы со звуком"""
import logging
import os
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

logger = logging.getLogger(__name__)

class AudioService:
    """Класс для управления воспроизведением звуков"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        
        # Плеер для слов
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Отдельный плеер для системных звуков
        self.sound_player = QMediaPlayer()
        self.sound_output = QAudioOutput()
        self.sound_player.setAudioOutput(self.sound_output)
        
        # Пути к звуковым файлам
        self.correct_sound = os.path.join(base_dir, "correct.mp3")
        self.incorrect_sound = os.path.join(base_dir, "incorrect.mp3")
    
    def play_word_audio(self, audio_file: str, audio_folder: str):
        """Воспроизводит аудио слова"""
        if not audio_file:
            return False
            
        audio_path = os.path.join(audio_folder, audio_file)
        return self._play_audio(self.media_player, audio_path)
    
    def play_correct_sound(self):
        """Воспроизводит звук правильного ответа"""
        return self._play_audio(self.sound_player, self.correct_sound)
    
    def play_incorrect_sound(self):
        """Воспроизводит звук неправильного ответа"""
        return self._play_audio(self.sound_player, self.incorrect_sound)
    
    def _play_audio(self, player: QMediaPlayer, file_path: str) -> bool:
        """Воспроизводит аудиофайл через указанный плеер"""
        if not os.path.exists(file_path):
            logger.warning("Audio file not found: %s", file_path)
            return False
            
        try:
            player.stop()
            player.setSource(QUrl.fromLocalFile(file_path))
            player.play()
            return True
        except FileNotFoundError:
            logger.error("Audio file not found: %s", file_path)
            return False
        except Exception as exc:
            logger.exception("Unexpected error while playing audio '%s': %s", file_path, exc)
            return False
    
    def stop_all(self):
        """Останавливает все воспроизведения"""
        self.media_player.stop()
        self.sound_player.stop()
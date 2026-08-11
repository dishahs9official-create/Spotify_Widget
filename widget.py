import sys
import os
import asyncio
import ctypes
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QProgressBar, QGraphicsDropShadowEffect, QFrame, QAbstractButton,
    QMenu, QColorDialog
)
from PySide6.QtCore import Qt, QPoint, QThread, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QLinearGradient, QBrush, QImage, QPen

from winrt.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as SessionManager,
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
)
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
from PIL import Image
import io

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Custom vector icon button class for crisp, high-DPI Spotify-style icons
class VectorButton(QAbstractButton):
    def __init__(self, icon_type, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type  # 'play_circle', 'pause_circle', 'next', 'prev', 'pin', 'desktop', 'close', 'heart'
        self.hovered = False
        self.pressed_state = False
        self.checked_state = False
        
        if 'circle' in icon_type:
            self.setFixedSize(38, 38)
        elif icon_type in ['pin', 'desktop', 'close', 'heart']:
            self.setFixedSize(24, 24)
        else:
            self.setFixedSize(30, 30)
            
    def enterEvent(self, event):
        self.hovered = True
        self.update()
        
    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.pressed_state = True
            self.update()
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        self.pressed_state = False
        self.update()
        super().mouseReleaseEvent(event)
        
    def setChecked(self, checked):
        self.checked_state = checked
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        cx, cy = rect.center().x(), rect.center().y()
        
        # 1. Circle Buttons (Play / Pause)
        if 'circle' in self.icon_type:
            r = min(rect.width(), rect.height()) // 2 - 1
            bg_color = QColor(255, 255, 255) if not self.hovered else QColor(240, 240, 240)
            if self.pressed_state:
                bg_color = QColor(200, 200, 200)
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            painter.drawEllipse(cx - r, cy - r, r*2, r*2)
            
            painter.setBrush(QColor(0, 0, 0))
            if self.icon_type == 'play_circle':
                path = QPainterPath()
                path.moveTo(cx - 3, cy - 6)
                path.lineTo(cx + 6, cy)
                path.lineTo(cx - 3, cy + 6)
                path.closeSubpath()
                painter.drawPath(path)
            elif self.icon_type == 'pause_circle':
                painter.drawRect(cx - 4, cy - 6, 3, 12)
                painter.drawRect(cx + 1, cy - 6, 3, 12)
                
        # 2. Borderless Vector Buttons
        else:
            if self.hovered:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255, 25))
                painter.drawRoundedRect(rect, 6, 6)
                
            pen_color = QColor(255, 255, 255, 220)
            if not self.isEnabled():
                pen_color = QColor(255, 255, 255, 80)
            elif self.icon_type == 'heart' and self.checked_state:
                pen_color = QColor(29, 185, 84) # Spotify Green
            elif self.icon_type == 'pin' and self.checked_state:
                pen_color = QColor(29, 185, 84) # Active
                
            painter.setPen(QPen(pen_color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            if self.icon_type == 'next':
                path = QPainterPath()
                path.moveTo(cx - 4, cy - 5)
                path.lineTo(cx + 2, cy)
                path.lineTo(cx - 4, cy + 5)
                path.closeSubpath()
                painter.setBrush(pen_color)
                painter.drawPath(path)
                painter.drawRect(cx + 4, cy - 5, 2, 10)
                
            elif self.icon_type == 'prev':
                path = QPainterPath()
                path.moveTo(cx + 4, cy - 5)
                path.lineTo(cx - 2, cy)
                path.lineTo(cx + 4, cy + 5)
                path.closeSubpath()
                painter.setBrush(pen_color)
                painter.drawPath(path)
                painter.drawRect(cx - 6, cy - 5, 2, 10)
                
            elif self.icon_type == 'close':
                painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
                painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)
                
            elif self.icon_type == 'pin':
                painter.drawLine(cx, cy - 5, cx, cy + 3)
                painter.drawLine(cx - 4, cy - 5, cx + 4, cy - 5)
                painter.drawLine(cx - 3, cy, cx + 3, cy)
                painter.drawLine(cx, cy + 3, cx, cy + 7)
                
            elif self.icon_type == 'heart':
                path = QPainterPath()
                path.moveTo(cx, cy + 6)
                path.cubicTo(cx - 7, cy, cx - 7, cy - 6, cx, cy - 3.5)
                path.cubicTo(cx + 7, cy - 6, cx + 7, cy, cx, cy + 6)
                
                if self.checked_state:
                    painter.setBrush(pen_color)
                    painter.drawPath(path)
                else:
                    painter.drawPath(path)

# Helper function to crop and round corners of a QPixmap
def get_rounded_pixmap(pixmap, radius):
    rounded = QPixmap(pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    
    path = QPainterPath()
    path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
    
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return rounded

# Generates a premium dark-gradient placeholder image for cover art
def create_placeholder_pixmap(width, height):
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    path = QPainterPath()
    path.addRoundedRect(0, 0, width, height, 12, 12)
    painter.setClipPath(path)
    
    grad = QLinearGradient(0, 0, 0, height)
    grad.setColorAt(0, QColor(45, 45, 45))
    grad.setColorAt(1, QColor(20, 20, 20))
    painter.fillPath(path, QBrush(grad))
    
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(29, 185, 84, 150))
    
    painter.drawEllipse(int(width * 0.25), int(height * 0.55), int(width * 0.2), int(height * 0.15))
    painter.drawEllipse(int(width * 0.55), int(height * 0.45), int(width * 0.2), int(height * 0.15))
    
    painter.setBrush(QColor(240, 240, 240, 150))
    painter.drawRect(int(width * 0.41), int(height * 0.25), int(width * 0.04), int(height * 0.38))
    painter.drawRect(int(width * 0.71), int(height * 0.15), int(width * 0.04), int(height * 0.38))
    
    beam_path = QPainterPath()
    beam_path.moveTo(int(width * 0.41), int(height * 0.25))
    beam_path.lineTo(int(width * 0.75), int(height * 0.15))
    beam_path.lineTo(int(width * 0.75), int(height * 0.23))
    beam_path.lineTo(int(width * 0.41), int(height * 0.33))
    beam_path.closeSubpath()
    painter.drawPath(beam_path)
    
    painter.end()
    return pixmap

# Extracts the dominant color from image bytes
def get_dominant_color(thumb_bytes):
    try:
        image = Image.open(io.BytesIO(thumb_bytes))
        img_temp = image.resize((1, 1), Image.Resampling.BILINEAR)
        color = img_temp.getpixel((0, 0))
        return int(color[0]), int(color[1]), int(color[2])
    except Exception:
        return 18, 18, 18

# Worker class managing Windows Media API on a background loop
class MediaWorker(QThread):
    media_changed = Signal(str, str, str, bytes)  # title, artist, album, thumbnail_bytes
    playback_changed = Signal(bool)  # is_playing
    session_changed = Signal(bool)  # has_active_session
    timeline_changed = Signal(float, float)  # position_seconds, duration_seconds
    
    def __init__(self):
        super().__init__()
        self.loop = None
        self.manager = None
        self.current_session = None
        self.is_running = True

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.start_listening())
        
    async def start_listening(self):
        self.manager = await SessionManager.request_async()
        
        def session_changed_callback(sender, args):
            asyncio.run_coroutine_threadsafe(self.update_session(), self.loop)
            
        self.manager.add_current_session_changed(session_changed_callback)
        
        await self.update_session()
        
        while self.is_running:
            await asyncio.sleep(1)
            
    async def update_session(self):
        session = self.manager.get_current_session()
        self.current_session = session
        
        if session:
            self.session_changed.emit(True)
            
            def properties_changed_callback(sender, args):
                asyncio.run_coroutine_threadsafe(self.update_properties(), self.loop)
                
            def playback_changed_callback(sender, args):
                asyncio.run_coroutine_threadsafe(self.update_playback(), self.loop)
                
            def timeline_changed_callback(sender, args):
                asyncio.run_coroutine_threadsafe(self.update_timeline(), self.loop)
                
            session.add_media_properties_changed(properties_changed_callback)
            session.add_playback_info_changed(playback_changed_callback)
            session.add_timeline_properties_changed(timeline_changed_callback)
            
            await self.update_properties()
            await self.update_playback()
            await self.update_timeline()
        else:
            self.session_changed.emit(False)
            
    async def update_properties(self):
        if not self.current_session:
            return
        try:
            props = await self.current_session.try_get_media_properties_async()
            title = props.title or "Unknown Track"
            artist = props.artist or "Unknown Artist"
            album = props.album_title or ""
            
            thumb_bytes = b""
            if props.thumbnail:
                try:
                    stream = await props.thumbnail.open_read_async()
                    size = stream.size
                    buffer = Buffer(size)
                    await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
                    reader = DataReader.from_buffer(buffer)
                    byte_data = bytearray(buffer.length)
                    reader.read_bytes(byte_data)
                    thumb_bytes = bytes(byte_data)
                except Exception as e:
                    print(f"Error loading cover art stream: {e}")
            
            self.media_changed.emit(title, artist, album, thumb_bytes)
        except Exception as e:
            print(f"Error fetching media details: {e}")
            
    async def update_playback(self):
        if not self.current_session:
            return
        try:
            info = self.current_session.get_playback_info()
            is_playing = (info.playback_status == PlaybackStatus.PLAYING)
            self.playback_changed.emit(is_playing)
        except Exception as e:
            print(f"Error updating playback status: {e}")
            
    async def update_timeline(self):
        if not self.current_session:
            return
        try:
            timeline = self.current_session.get_timeline_properties()
            pos = timeline.position.total_seconds()
            dur = timeline.end_time.total_seconds()
            self.timeline_changed.emit(pos, dur)
        except Exception:
            pass

    def send_play(self):
        if self.current_session:
            asyncio.run_coroutine_threadsafe(self.current_session.try_play_async(), self.loop)

    def send_pause(self):
        if self.current_session:
            asyncio.run_coroutine_threadsafe(self.current_session.try_pause_async(), self.loop)

    def send_next(self):
        if self.current_session:
            asyncio.run_coroutine_threadsafe(self.current_session.try_skip_next_async(), self.loop)

    def send_previous(self):
        if self.current_session:
            asyncio.run_coroutine_threadsafe(self.current_session.try_skip_previous_async(), self.loop)

# Main Spotify Desktop Widget
class SpotifyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.current_position = 0.0
        self.duration = 1.0
        self.drag_position = QPoint()
        
        # Load user configuration defaults
        self.widget_mode = 1 # 0 = Desktop Mode (Behind apps), 1 = Float Mode (Always on Top)
        self.use_dynamic_color = True
        self.custom_color = QColor(18, 18, 18)
        self.widget_opacity = 0.85
        self.current_artwork_color = (18, 18, 18)
        self.saved_geometry = None
        
        self.load_config()
        self.init_ui()
        self.start_worker()
        
        # Local progress smoother timer
        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(200)
        self.progress_timer.timeout.connect(self.tick_progress)
        self.progress_timer.start()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                    self.widget_mode = config.get("widget_mode", 0)
                    self.use_dynamic_color = config.get("use_dynamic_color", True)
                    cc = config.get("custom_color", [18, 18, 18])
                    self.custom_color = QColor(cc[0], cc[1], cc[2])
                    self.widget_opacity = config.get("opacity", 0.85)
                    self.saved_geometry = config.get("geometry")
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        try:
            config = {
                "widget_mode": self.widget_mode,
                "use_dynamic_color": self.use_dynamic_color,
                "custom_color": [self.custom_color.red(), self.custom_color.green(), self.custom_color.blue()],
                "opacity": self.widget_opacity,
                "geometry": [self.x(), self.y()]
            }
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def init_ui(self):
        self.set_window_mode_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(360, 136)
        
        # Apply loaded position if valid
        if self.saved_geometry:
            screen = QApplication.primaryScreen().availableGeometry()
            if screen.contains(self.saved_geometry[0], self.saved_geometry[1]):
                self.move(self.saved_geometry[0], self.saved_geometry[1])
        
        # Master layout (to allow padding for drop shadow)
        master_layout = QHBoxLayout(self)
        master_layout.setContentsMargins(10, 10, 10, 10)
        
        # Main styled container frame
        self.container = QFrame(self)
        self.container.setObjectName("container")
        
        # Soft premium drop shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 180))
        self.shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(self.shadow)
        
        # Update colors from configuration
        self.update_theme()
        
        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(12)
        
        # 1. Album art thumbnail
        self.album_label = QLabel(self.container)
        self.album_label.setFixedSize(80, 80)
        placeholder = create_placeholder_pixmap(80, 80)
        self.album_label.setPixmap(placeholder)
        container_layout.addWidget(self.album_label)
        
        # 2. Right details section
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(5)
        
        # Header: Title/Artist + Utility buttons
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        
        self.title_label = QLabel("Nothing Playing", self.container)
        self.title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        
        self.artist_label = QLabel("Open Spotify to start", self.container)
        self.artist_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.artist_label.setStyleSheet("color: rgba(255, 255, 255, 0.55); font-size: 11px;")
        
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        header_layout.addLayout(text_layout)
        header_layout.addStretch()
        
        # Tiny header buttons
        self.heart_btn = VectorButton("heart", self.container)
        self.heart_btn.setToolTip("Like Song")
        self.heart_btn.clicked.connect(self.toggle_heart)
        
        self.pin_btn = VectorButton("pin", self.container)
        self.pin_btn.clicked.connect(self.cycle_widget_mode)
        self.update_mode_indicators()
        
        self.close_btn = VectorButton("close", self.container)
        self.close_btn.setToolTip("Close Widget")
        self.close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(self.heart_btn)
        header_layout.addWidget(self.pin_btn)
        header_layout.addWidget(self.close_btn)
        details_layout.addLayout(header_layout)
        
        # Sleek progress bar
        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setRange(0, 1000)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.12);
                border: none;
                border-radius: 1.5px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 1.5px;
            }
        """)
        details_layout.addWidget(self.progress_bar)
        
        # Playback control row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(14)
        controls_layout.addStretch()
        
        self.prev_btn = VectorButton("prev", self.container)
        self.prev_btn.clicked.connect(self.on_prev_clicked)
        
        self.play_btn = VectorButton("play_circle", self.container)
        self.play_btn.clicked.connect(self.on_play_clicked)
        
        self.next_btn = VectorButton("next", self.container)
        self.next_btn.clicked.connect(self.on_next_clicked)
        
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addStretch()
        
        details_layout.addLayout(controls_layout)
        container_layout.addLayout(details_layout)
        
        master_layout.addWidget(self.container)
        
        # Dragging handlers
        self.container.mousePressEvent = self.on_press
        self.container.mouseMoveEvent = self.on_move
        self.container.mouseReleaseEvent = self.on_release

    # Apply window flags based on current widget mode
    def set_window_mode_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        
        if self.widget_mode == 1:
            # Float (Always on Top)
            flags |= Qt.WindowType.WindowStaysOnTopHint
            
        self.setWindowFlags(flags)

    # Cycles: Desktop Mode (0) -> Float Mode (1)
    def cycle_widget_mode(self):
        self.widget_mode = (self.widget_mode + 1) % 2
        
        # Save position, update flags, restore position, show
        pos = self.pos()
        self.set_window_mode_flags()
        self.move(pos)
        self.show()
        
        self.update_mode_indicators()
        self.save_config()

    def update_mode_indicators(self):
        # Update pin button visual and tooltips
        if self.widget_mode == 0:
            self.pin_btn.setChecked(False)
            self.pin_btn.setToolTip("Mode: Desktop (Sits on background, behind tabs)\nRight-click for settings")
            self.shadow.setEnabled(True)
        elif self.widget_mode == 1:
            self.pin_btn.setChecked(True)
            self.pin_btn.setToolTip("Mode: Float (Always on Top)\nRight-click for settings")
            self.shadow.setEnabled(True)

    # Drag window handlers
    def on_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def on_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def on_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = QPoint()
            self.save_config() # Save drag final position

    # Right-click context menu event for custom colors & transparency
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #181818;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 4px 0px;
                font-family: 'Segoe UI', Arial;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #282828;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(255, 255, 255, 0.08);
                margin: 4px 0px;
            }
        """)
        
        # 1. Mode selection
        mode_menu = menu.addMenu("Widget Mode")
        action_desktop = mode_menu.addAction("Desktop Mode (Behind tabs)")
        action_float = mode_menu.addAction("Float Mode (Always on Top)")
        action_desktop.setCheckable(True)
        action_float.setCheckable(True)
        action_desktop.setChecked(self.widget_mode == 0)
        action_float.setChecked(self.widget_mode == 1)
        
        menu.addSeparator()
        
        # 2. Color picker settings
        action_dynamic = menu.addAction("Match Album Color (Dynamic)")
        action_dynamic.setCheckable(True)
        action_dynamic.setChecked(self.use_dynamic_color)
        
        action_custom_color = menu.addAction("Pick Custom Color...")
        action_custom_color.setEnabled(not self.use_dynamic_color)
        
        menu.addSeparator()
        
        # 3. Transparency
        opacity_menu = menu.addMenu("Background Opacity")
        opacities = [15, 30, 50, 70, 85, 100]
        for op in opacities:
            act = opacity_menu.addAction(f"{op}%")
            act.setCheckable(True)
            act.setChecked(int(self.widget_opacity * 100) == op)
            # Use default capture in lambda
            act.triggered.connect(lambda checked=False, val=op: self.set_opacity_value(val))
            
        menu.addSeparator()
        action_close = menu.addAction("Close Widget")
        
        # Trigger
        action = menu.exec(event.globalPos())
        if not action:
            return
            
        if action == action_desktop:
            if self.widget_mode != 0:
                self.cycle_widget_mode()
        elif action == action_float:
            if self.widget_mode != 1:
                self.cycle_widget_mode()
        elif action == action_dynamic:
            self.use_dynamic_color = action_dynamic.isChecked()
            self.update_theme()
            self.save_config()
        elif action == action_custom_color:
            self.pick_custom_color()
        elif action == action_close:
            self.close()

    def set_opacity_value(self, val):
        self.widget_opacity = val / 100.0
        self.update_theme()
        self.save_config()

    def pick_custom_color(self):
        color = QColorDialog.getColor(self.custom_color, self, "Pick Widget Color")
        if color.isValid():
            self.custom_color = color
            self.use_dynamic_color = False
            self.update_theme()
            self.save_config()

    # Themes the background dynamically
    def update_theme(self):
        if self.use_dynamic_color and self.is_playing:
            r, g, b = self.current_artwork_color
        else:
            r, g, b = self.custom_color.red(), self.custom_color.green(), self.custom_color.blue()
            
        self.apply_theme_color(r, g, b, self.widget_opacity)

    def apply_theme_color(self, r, g, b, opacity=0.85):
        self.container.setStyleSheet(f"""
            QFrame#container {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                  stop:0 rgba({r}, {g}, {b}, {opacity:.2f}),
                                                  stop:1 rgba(15, 15, 15, {opacity:.2f}));
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 20px;
            }}
            QLabel {{
                color: white;
                background: transparent;
            }}
        """)

    def toggle_heart(self):
        self.heart_btn.setChecked(not self.heart_btn.checked_state)

    # Worker Thread control
    def start_worker(self):
        self.worker = MediaWorker()
        self.worker.media_changed.connect(self.on_media_changed)
        self.worker.playback_changed.connect(self.on_playback_changed)
        self.worker.session_changed.connect(self.on_session_changed)
        self.worker.timeline_changed.connect(self.on_timeline_changed)
        self.worker.start()

    # Worker signal handlers
    def on_session_changed(self, has_session):
        self.prev_btn.setEnabled(has_session)
        self.play_btn.setEnabled(has_session)
        self.next_btn.setEnabled(has_session)
        self.heart_btn.setEnabled(has_session)
        
        if not has_session:
            self.title_label.setText("Nothing Playing")
            self.artist_label.setText("Open Spotify to start")
            self.album_label.setPixmap(create_placeholder_pixmap(80, 80))
            self.progress_bar.setValue(0)
            self.is_playing = False
            self.play_btn.icon_type = 'play_circle'
            self.play_btn.update()
            self.update_theme()

    def on_media_changed(self, title, artist, album, thumb_bytes):
        if len(title) > 28:
            title = title[:25] + "..."
        if len(artist) > 35:
            artist = artist[:32] + "..."
            
        self.title_label.setText(title)
        self.artist_label.setText(artist)
        
        if thumb_bytes:
            image = QImage.fromData(thumb_bytes)
            pixmap = QPixmap.fromImage(image)
            pixmap = pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.album_label.setPixmap(get_rounded_pixmap(pixmap, 12))
            
            # Extract color
            r, g, b = get_dominant_color(thumb_bytes)
            r = min(int(r * 0.9), 200)
            g = min(int(g * 0.9), 200)
            b = min(int(b * 0.9), 200)
            self.current_artwork_color = (r, g, b)
            self.update_theme()
        else:
            self.album_label.setPixmap(create_placeholder_pixmap(80, 80))
            self.current_artwork_color = (18, 18, 18)
            self.update_theme()

    def on_playback_changed(self, is_playing):
        self.is_playing = is_playing
        self.play_btn.icon_type = 'pause_circle' if is_playing else 'play_circle'
        self.play_btn.update()
        self.update_theme()

    def on_timeline_changed(self, position, duration):
        self.current_position = position
        self.duration = max(duration, 1.0)
        self.update_progressbar_ui()

    def tick_progress(self):
        if self.is_playing:
            self.current_position = min(self.current_position + 0.2, self.duration)
            self.update_progressbar_ui()

    def update_progressbar_ui(self):
        ratio = self.current_position / self.duration
        self.progress_bar.setValue(int(ratio * 1000))

    # Control actions
    def on_play_clicked(self):
        if self.is_playing:
            self.worker.send_pause()
        else:
            self.worker.send_play()

    def on_prev_clicked(self):
        self.worker.send_previous()

    def on_next_clicked(self):
        self.worker.send_next()

    def closeEvent(self, event):
        self.worker.is_running = False
        self.worker.quit()
        self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = SpotifyWidget()
    widget.show()
    sys.exit(app.exec())

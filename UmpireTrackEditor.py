import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QMenu, QPushButton,
    QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QFileDialog, QTextBrowser, QLineEdit, QShortcut
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QPainterPath,
    QTransform, QColor
)
from PyQt5.QtCore import Qt, QPoint, QEvent

# Constants
BUTTON_SIZE = (80, 50)
LINE_SIZE = (110, 70)
SAVE_BUTTON_SIZE = (160, 50)
LINE_COLOR = QColor(0, 0, 255)
LINE_THICKNESS = 3
FONT_SIZES = {
    'label': 17,
    'button': 20,
    'save_button': 18,
    'text_box': 16
}
IMAGE_SIZE = (750, 400)
COMBOBOX_SIZE = (150, 40)
INITIAL_IMAGE = "BlankOval.png"
APP_STYLES = """
/*---------------------------------Background--------------------------------------*/
QWidget {
    background-color: lightgoldenrodyellow;
    color: black;
    font-family: 'Courier New', Courier, monospace, Helvetica, sans-serif;
    font-size: 16px;
    font-weight: bold;
}

/*-------------------------------------Tabs-----------------------------------------*/
QTabWidget::pane {
    border: 2px solid black;
    border-radius: 2px;
} 

QTabBar::tab {
    background-color: blanchedalmond; 
    border: 2px solid black;
    padding: 10% 35% 5% 35%;
} 

QTabBar::tab:selected { 
    background: lightgoldenrodyellow; 
    margin-bottom: -2px;
}

/*---------------------------------Buttons--------------------------------------*/
QPushButton {
    background-color: lightcoral;
    border-radius: 12px;
    border-color: black;
    border-style: solid;
    border-width: 2px;  
    padding: 10px 4px 10px 4px;
}

QPushButton:hover {
    background-color: salmon;
}

QPushButton:disabled {
    background-color: rgb(156, 80, 72);
}

/*---------------------------------Labels--------------------------------------*/
QLabel {
    background-color: burlywood;
    border-color: black;
    border-style: solid;
    border-width: 2px; 
    padding: 4px;
    border-radius: 8px;
}

/*---------------------------------Combo Boxes--------------------------------------*/
QComboBox {
    background: burlywood;
    color: black;
    border: 2px solid black;
    padding: 4px;
}

QComboBox:focus {
    background: burlywood;
    border: 2px solid black;
    color: black;
}

QComboBox QAbstractItemView {
    background: blanchedalmond; 
    border: 2px solid black;
    selection-background-color: burlywood;
    selection-color: black;
}
"""

class DraggableMixin:
    """Mixin class providing draggable functionality"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moving = False
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setFocusPolicy(Qt.StrongFocus)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.moving = True
            self.offset = event.pos()
            self.setFocus()

    def mouseMoveEvent(self, event):
        if self.moving:
            new_pos = self.mapToParent(event.pos() - self.offset)
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        self.moving = False

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self.close()

class DraggableLabel(DraggableMixin, QLabel):
    """Draggable number label with deletion support"""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            font-size: {FONT_SIZES['label']}px;
            font-weight: bold;
            color: black;
            padding: 0;
            margin: 0;
        """)
        self.setFixedSize(35, 30)
        self.setAlignment(Qt.AlignCenter)

class ResizableTextLabel(DraggableMixin, QLabel):
    """Resizable and editable text label with drag support"""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setStyleSheet("""
            background-color: white;
            border: 1px solid black;
            padding: 2px;
            font-size: {FONT_SIZES['text_box']}px;
        """)
        self.setMinimumSize(80, 30)
        self.resize(120, 30)
        self.setAlignment(Qt.AlignCenter)
        self.resizing = False
        
        # Add resize handle
        self.resize_handle = QLabel(self)
        self.resize_handle.setStyleSheet("background-color: #666;")
        self.resize_handle.setFixedSize(8, 8)
        self.resize_handle.move(self.width()-8, self.height()-8)
        self.resize_handle.installEventFilter(self)
        self.resize_handle.setCursor(Qt.SizeFDiagCursor)

    def eventFilter(self, obj, event):
        if obj == self.resize_handle:
            if event.type() == QEvent.MouseButtonPress:
                self.resizing = True
                self.initial_size = self.size()
                self.initial_mouse_pos = event.globalPos()
                return True
            elif event.type() == QEvent.MouseMove and self.resizing:
                current_mouse_pos = event.globalPos()
                delta_x = current_mouse_pos.x() - self.initial_mouse_pos.x()
                delta_y = current_mouse_pos.y() - self.initial_mouse_pos.y()
                
                # Calculate new size based on initial dimensions
                new_width = max(self.minimumWidth(), self.initial_size.width() + delta_x)
                new_height = max(self.minimumHeight(), self.initial_size.height() + delta_y)
                
                # Apply new size
                self.resize(new_width, new_height)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.resizing = False
                return True
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        self.resize_handle.move(self.width()-8, self.height()-8)
        super().resizeEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.start_editing()

    def start_editing(self):
        """Replace label with editable line edit"""
        self.editor = QLineEdit(self.text(), self)
        self.editor.setStyleSheet("""
            border: 2px solid blue;
            font-size: {FONT_SIZES['text_box']}px;
            background: white;
        """)
        self.editor.setGeometry(2, 2, self.width()-4, self.height()-4)
        self.editor.selectAll()
        self.editor.setFocus()
        self.editor.show()
        self.editor.editingFinished.connect(self.finish_editing)

    def finish_editing(self):
        """Update label text from editor"""
        self.setText(self.editor.text())
        self.editor.deleteLater()
        self.update()

class DraggableLine(DraggableMixin, QLabel):
    """Draggable, rotatable line widget with styling"""
    def __init__(self, line_type, parent=None):
        super().__init__(parent)
        self.line_type = line_type
        self.angle = 0
        self.setFixedSize(*LINE_SIZE)
        self.setStyleSheet("background-color: transparent; border: none;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = QPoint(self.width() // 2, self.height() // 2)
        
        transform = QTransform()
        transform.translate(center.x(), center.y())
        transform.rotate(self.angle)
        transform.translate(-center.x(), -center.y())
        painter.setTransform(transform)

        pen = QPen(LINE_COLOR, LINE_THICKNESS)
        painter.setPen(pen)

        if self.line_type == "straight":
            painter.drawLine(0, self.height()//2, self.width(), self.height()//2)
        else:
            path = QPainterPath()
            path.moveTo(0, self.height()//2)
            path.quadTo(self.width()//2, self.height(), self.width(), self.height()//2)
            painter.drawPath(path)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key_R:
            self.angle = (self.angle + 15) % 360
            self.update()

class MyApp(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self._load_styles()
        self._init_ui()
        self.number_labels = []
        self.setFixedSize(960, 540)
        
        # Set up keyboard shortcut
        self.copy_shortcut = QShortcut(Qt.Key_C, self)
        self.copy_shortcut.activated.connect(self._handle_copy_shortcut)

    def _load_styles(self):
        """Load embedded CSS styles"""
        self.setStyleSheet(APP_STYLES)

    def _init_ui(self):
        """Initialize main UI components"""
        self.setWindowTitle("Umpire Track Editor")

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        # Create tabs in order
        self._create_help_tab()
        self._create_view_tab()
        self._create_edit_tab()
        self.show()

    def _create_help_tab(self):
        """Create help/instructions tab"""
        help_tab = QWidget()
        self.tabs.addTab(help_tab, "Help")
        
        layout = QVBoxLayout(help_tab)
        layout.setContentsMargins(10, 5, 10, 10)
        layout.setSpacing(0)
        
        # Program Description
        desc_section = self._create_help_section(
            "Program Description", self._get_description_text()
        )
        layout.addWidget(desc_section)
        
        # View Instructions
        view_section = self._create_help_section(
            "View Tab Instructions", self._get_view_instructions(), top_margin=5
        )
        layout.addWidget(view_section)
        
        # Edit Instructions
        edit_section = self._create_help_section(
            "Edit Tab Instructions", self._get_edit_instructions(), top_margin=5
        )
        layout.addWidget(edit_section)
        
        layout.addStretch(1)

    def _create_help_section(self, title, content, top_margin=0):
        """Create individual help section"""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, top_margin, 0, 0)
        section_layout.setSpacing(0)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold;
            margin-bottom: 1px;
        """)
        
        content_label = QTextBrowser()
        content_label.setHtml(f"""
            <style>
                body {{ 
                    font-size: 12px; 
                    line-height: 0.8;
                    margin: 0;
                    padding: 0;
                }}
                ul, ol {{
                    margin: 2px 0;
                    padding-left: 15px;
                }}
            </style>
            {content}
        """)
        content_label.setStyleSheet("""
            border: none;
            background: transparent;
            padding: 0;
            margin: 0;
        """)
        content_label.setMinimumHeight(80)
        content_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        section_layout.addWidget(title_label)
        section_layout.addWidget(content_label)
        return section

    def _get_description_text(self):
        return """
        <p>Create and customize event diagrams with these features:</p>
        <ul>
            <li>View and copy pre-made event diagrams</li>
            <li>Create custom diagrams with numbers/lines/text</li>
            <li>Save your custom creations</li>
        </ul>
        """

    def _get_view_instructions(self):
        return """
        <p><b>Using the View tab:</b></p>
        <ol>
            <li>Select event type from first dropdown</li>
            <li>Select umpire count from second dropdown</li>
            <li>Right-click image or press 'C' to copy</li>
        </ol>
        """

    def _get_edit_instructions(self):
        return """
        <p><b>Using the Edit tab:</b></p>
        <ol>
            <li>Add numbers with buttons (drag to move)</li>
            <li>Add lines/curves (R to rotate)</li>
            <li>Add resizable text boxes (double-click to edit, enter to submit)</li>
            <li>Backspace deletes selected items</li>
            <li>Save button exports final image</li>
        </ol>
        """

    def _create_view_tab(self):
        """Create the view tab with image and comboboxes"""
        self.view_tab = QWidget()
        self.tabs.addTab(self.view_tab, "View")
        
        layout = QVBoxLayout(self.view_tab)
        self._setup_image_label(layout, "view")
        self._setup_comboboxes(layout)
        self._connect_combobox_signals()

    def _create_edit_tab(self):
        """Create the edit tab with image and controls"""
        self.edit_tab = QWidget()
        self.tabs.addTab(self.edit_tab, "Edit")
        
        layout = QVBoxLayout(self.edit_tab)
        self._setup_image_label(layout, "edit")
        self._setup_number_buttons()
        self._setup_line_buttons()
        self._setup_save_button(layout)

    def _setup_image_label(self, layout, tab_type):
        """Configure image label for specified tab"""
        label = QLabel(self.view_tab if tab_type == "view" else self.edit_tab)
        label.setAlignment(Qt.AlignCenter)
        label.setMinimumSize(*IMAGE_SIZE)
        layout.addWidget(label, alignment=Qt.AlignCenter)
        
        if tab_type == "view":
            self.imageLabel1 = label
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(self._show_image_menu)
        else:
            self.imageLabel2 = label
            
        self._set_initial_image(label, INITIAL_IMAGE)

    def _setup_comboboxes(self, layout):
        """Create and configure comboboxes for view tab"""
        combo_layout = QHBoxLayout()
        
        self.eventComboBox = self._create_combobox(
            "Select an event", [
                "50m", 
                "60m", 
                "60m H", 
                "200m",
                "300m",
                "400m",
                "600m",
                "800m",
                "1000m",
                "1200m",
                "1500m",
                "2000m",
                "3000m",
                "4 x 100m Relay",
                "4 x 200m Relay",
                "4 x 400m Relay",
                "4 x 800m Relay",
                ]
        )
        self.umpireComboBox = self._create_combobox(
            "Select number of umpires", [str(i) for i in range(5, 11)]
        )

        combo_layout.addWidget(self.eventComboBox)
        combo_layout.addWidget(self.umpireComboBox)
        layout.addLayout(combo_layout)

    def _create_combobox(self, placeholder, items):
        """Helper to create configured combobox"""
        combo = QComboBox(self.view_tab)
        combo.addItem(placeholder)
        combo.setItemData(0, 0, Qt.UserRole - 1)
        combo.addItems(items)
        combo.setMinimumSize(*COMBOBOX_SIZE)
        return combo

    def _connect_combobox_signals(self):
        """Connect combobox change signals"""
        self.eventComboBox.currentIndexChanged.connect(self._handle_combobox_changes)
        self.umpireComboBox.currentIndexChanged.connect(self._handle_combobox_changes)

    def _setup_number_buttons(self):
        """Create number buttons in two columns"""
        left_x, right_x = 5, 870
        top_y = self.imageLabel2.y() + 5
        
        for i in range(1, 13):
            btn = QPushButton(str(i), self.edit_tab)
            btn.setFixedSize(*BUTTON_SIZE)
            btn.setStyleSheet(f"font-size: {FONT_SIZES['button']}px; font-weight: bold;")
            btn.clicked.connect(lambda _, num=i: self.add_number(num))
            
            if i <= 6:
                x, y = left_x, top_y + (i-1)*(BUTTON_SIZE[1]+3)
            else:
                x, y = right_x, top_y + (i-7)*(BUTTON_SIZE[1]+3)
                
            btn.move(x, y)

    def _setup_line_buttons(self):
        """Create line/curve/text buttons at column bottoms"""
        left_x, right_x = 5, 870
        base_y = self.imageLabel2.y() + 5 + 6*(BUTTON_SIZE[1]+3)
        
        # Left column buttons
        self._create_line_button("Line", left_x, base_y, self.add_straight_line)
        self._create_line_button("Text", left_x, base_y + BUTTON_SIZE[1] + 3, self.add_text_box)
        
        # Right column buttons
        self._create_line_button("Curve", right_x, base_y, self.add_curved_line)

    def _create_line_button(self, text, x, y, handler):
        """Helper to create line-type buttons"""
        btn = QPushButton(text, self.edit_tab)
        btn.setFixedSize(*BUTTON_SIZE)
        btn.setStyleSheet(f"font-size: {FONT_SIZES['button']}px; font-weight: bold;")
        btn.clicked.connect(handler)
        btn.move(x, y)
        return btn

    def _setup_save_button(self, layout):
        """Configure save button at bottom"""
        btn = QPushButton("Save Image", self.edit_tab)
        btn.setFixedSize(*SAVE_BUTTON_SIZE)
        btn.setStyleSheet(f"font-size: {FONT_SIZES['save_button']}px; font-weight: bold;")
        btn.clicked.connect(self.save_image)
        layout.addWidget(btn, alignment=Qt.AlignCenter)

    def _set_initial_image(self, label, filename):
        """Set initial image for a label"""
        # Get the correct base path
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        image_path = os.path.join(base_path, "images", filename)
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            label.setPixmap(pixmap)
            label.setScaledContents(True)
        else:
            print(f"Warning: Image '{image_path}' not found!")

    def _handle_combobox_changes(self):
        """Handle changes in combobox selections"""
        event_text = self.eventComboBox.currentText()
        umpire_text = self.umpireComboBox.currentText()
        event_index = self.eventComboBox.currentIndex()
        umpire_index = self.umpireComboBox.currentIndex()

        if event_index > 0 and umpire_index > 0:
            filename = f"{event_text}{umpire_text}.png"
            self._update_image(self.imageLabel1, filename)

    def _update_image(self, label, filename):
        """Update displayed image"""
        # Get the correct base path
        if getattr(sys, 'frozen', False):
            # Running as executable
            base_path = sys._MEIPASS
        else:
            # Running as script
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        image_path = os.path.join(base_path, "images", filename)
        print(f"Attempting to load image from: {image_path}")  # Debug print
        
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                label.setPixmap(pixmap)
                print("Image loaded successfully!")  # Debug success
            else:
                print(f"Failed to load image: {image_path}")  # Debug failure
        else:
            print(f"Image file not found: {image_path}")  # Debug missing file

    def _show_image_menu(self, position):
        """Show context menu for image copy"""
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Image")
        action = menu.exec_(self.imageLabel1.mapToGlobal(position))
        if action == copy_action:
            self._copy_image_to_clipboard()

    def _handle_copy_shortcut(self):
        """Handle C key presses for copying"""
        if self.tabs.currentIndex() == 1:  # Only in View tab
            self._copy_image_to_clipboard()

    def _copy_image_to_clipboard(self):
        """Copy current view tab image to clipboard"""
        if hasattr(self, 'imageLabel1') and self.imageLabel1.pixmap():
            pixmap = self.imageLabel1.grab()
            QApplication.clipboard().setPixmap(pixmap)
            print("Current image copied to clipboard!")

    def add_number(self, number):
        """Add draggable number label to edit tab"""
        num_label = DraggableLabel(str(number), self.imageLabel2)
        num_label.move(100, 100)
        num_label.show()
        self.number_labels.append(num_label)

    def add_straight_line(self):
        """Add straight line to edit tab"""
        line = DraggableLine("straight", self.imageLabel2)
        line.move(100, 100)
        line.show()

    def add_curved_line(self):
        """Add curved line to edit tab"""
        line = DraggableLine("curved", self.imageLabel2)
        line.move(100, 100)
        line.show()

    def add_text_box(self):
        """Add resizable text box to edit tab"""
        text_label = ResizableTextLabel("Text", self.imageLabel2)
        text_label.move(100, 100)
        text_label.show()

    def save_image(self):
        """Save current edit tab image to file"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png);;All Files (*)", options=options
        )
        if file_path:
            pixmap = self.imageLabel2.grab()
            pixmap.save(file_path)
            print(f"Saved image as {file_path}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec_())
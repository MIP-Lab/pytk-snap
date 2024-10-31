from PyQt5 import Qt
from PyQt5.QtGui import QFont
from functools import partial

class CaseLoader:
    
    def __init__(self, cases, load_dir='', save_dir='') -> None:
        self.cases = cases
        self.load_dir = load_dir
        self.save_dir = save_dir
        self.cur_case_id = -1
        self.world = None
        self.saved = set()
    
    def build_ui(self):
        layout = Qt.QHBoxLayout()
        button1 = Qt.QPushButton('Previous')
        # button1.setFont(QFont('Times', 11))
        button1.clicked.connect(partial(self._load_previous, dataloader=self))
        
        button2 = Qt.QPushButton('Next')
        # button2.setFont(QFont('Times', 11))
        button2.clicked.connect(partial(self._load_next, dataloader=self))
        
        text_box1 = Qt.QLineEdit()
        text_box1.setFont(QFont('Times', 16))
        text_box1.setFixedWidth(60)
        text_box1.setText('0')
        
        label1 = Qt.QLabel()
        label1.setFont(QFont('Times', 16))
        label1.setText('')
        
        text_box2 = Qt.QLineEdit()
        text_box2.setFont(QFont('Times', 16))
        text_box2.setFixedWidth(200)
        
        button3 = Qt.QPushButton('Go')
        # button3.setFont(QFont('Times', 11))
        button3.clicked.connect(partial(self._goto_case, dataloader=self))
        
        button4 = Qt.QPushButton('Save')
        # button4.setFont(QFont('Times', 11))
        button4.clicked.connect(partial(self._save_cur_case, dataloader=self))
        
        layout.addWidget(button1)
        layout.addWidget(text_box1)
        
        layout.addWidget(button3)
        layout.addStretch()
        
        layout.addWidget(label1)
        
        layout.addStretch()
        
        layout.addWidget(text_box2)
        layout.addWidget(button4)
        layout.addWidget(button2)
        
        self.previous_button = button1
        self.next_button = button2
        self.goto_button = button3
        self.save_button = button4
        self.case_input = text_box1
        self.case_label = label1
        self.comment_input = text_box2
        
        self.update_case_label()
        
        return layout
    
    @property
    def case_stats(self):
        return {'total': len(self.cases), 'saved': len(self.saved)}
    
    @property
    def cur_case(self):
        if self.cur_case_id < 0 or self.cur_case_id >= len(self.cases):
            return ''
        return self.cases[self.cur_case_id]
    
    @property
    def comment(self):
        return self.comment_input.text()
    
    ########################################################## for overwriting start #############################################################
    
    def get_next_case_id(self):
        if self.cur_case_id == len(self.cases):
            return None
        return self.cur_case_id + 1
    
    def get_previous_case_id(self):
        if self.cur_case_id <= 0:
            return None
        return self.cur_case_id - 1
    
    def load_case(self, case, world):
        return
    
    def save_case(self, case, world):
        return
    
    ########################################################## for overwriting end #############################################################
    
    def update_case_label(self):
        label = f'{self.cur_case} ({self.case_stats["saved"]}/{self.case_stats["total"]})'
        self.set_case_label(label)
    
    def get_case_label(self):
        return self.case_label.text()
    
    def get_case_input(self):
        try:
            case_input = int(self.case_input.text())
            case_id = case_input - 1
            if 0 <= case_id < len(self.cases):
                return case_id
        except ValueError:
            return None
        return None
    
    def set_comment(self, comment):
        self.comment_input.setText(comment)
    
    def set_case_input(self, case_id):
        self.case_input.setText(str(self.cur_case_id + 1))

    def set_case_label(self, label):
        self.case_label.setText(label)
    
    def _load(self, case_id):
        if not (0 <= case_id < len(self.cases)):
            return
        self.cur_case_id = case_id
        self.world.clear()
        self.load_case(self.cur_case, self.world)
        self.set_case_input(case_id)
        self.update_case_label()
    
    @staticmethod
    def _load_next(flag, dataloader):
        case_id = dataloader.get_next_case_id()
        if case_id is not None:
            dataloader._load(case_id)
    
    @staticmethod
    def _load_previous(flag, dataloader):
        case_id = dataloader.get_previous_case_id()
        if case_id is not None:
            dataloader._load(case_id)
    
    @staticmethod
    def _goto_case(flag, dataloader):
        case_id = dataloader.get_case_input()
        if case_id is not None:
            dataloader._load(case_id)

    @staticmethod
    def _save_cur_case(flag, dataloader):
        dataloader.save_case(dataloader.cur_case, dataloader.world)
        dataloader.saved.add(dataloader.cur_case)
        dataloader.set_case_label(dataloader.get_case_label() + ' Saved!')
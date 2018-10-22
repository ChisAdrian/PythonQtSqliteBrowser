import pathlib
import sys
from io import StringIO

import pyperclip
from PyQt5 import QtCore, QtSql, QtWidgets
from PyQt5.QtGui import QIcon, QStandardItemModel
from PyQt5.QtWidgets import (QAction, QFileDialog, QInputDialog, QLineEdit,
                             QPushButton)

import QSqlDatabaseV0 as QSQLF
import resources  # pylint: disable=unused-import
import Ui_main


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_main.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":icons/main.ico"))
        self.db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.setingsDbexist('settings.sqlite')
        self.onIni()

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        self.databaseMenu = mainMenu.addMenu('DataBase')
        # Menus
        exportMenu = mainMenu.addMenu('Export')
        editMenu = mainMenu.addMenu('Edit')
        # Menus\

        # Actions
        exportMenu.addAction(self.createAction(self.exportCSV, 'to_CSV', '', 'Close current DB', 'Ctrl+Shift+C'))
        exportMenu.addAction(self.createAction(self.exportClip, 'CopyAll', '', '', 'Ctrl+Shift+A'))
        exportMenu.addAction(self.createAction(self.copySelection, 'Copy', '', '', 'Ctrl+C'))

        fileMenu.addAction(self.createAction(self.doOpendb, 'Open Db', '', 'Close current DB', 'Ctrl+O'))
        fileMenu.addAction(self.createAction(self.closeThis, 'CloseDB', '', 'Close current DB', 'Ctrl+D'))
        fileMenu.addAction(self.createAction(self.close, 'Exit', '', 'Exit application', 'Ctrl+Q'))

        editMenu.addAction(self.createAction(self.doQuery, '_exec_Query', ':icons/st.ico', '', 'Ctrl+E'))

        self.pathDb = ''
        self.queryTXT = ''

        self.treeModel = QStandardItemModel(self)
        self.treeModel_grid = QStandardItemModel(self)
        self.ui.treeView_DB.clicked.connect(self.treeView_DBclicked)
        self.ui.treeView_DB.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.treeView_DB.customContextMenuRequested.connect(self.treeView_DB_RightCick)
        noTrigger = QtWidgets.QAbstractItemView.NoEditTriggers

        self.ui.treeView_DB.setEditTriggers(noTrigger)
        self.ui.tableView.setEditTriggers(noTrigger)

        self.queryButton = QPushButton('_exec', self.ui.plainTextEdit)
        self.queryButton.clicked.connect(self.doQuery)
        self.queryButton.show()

        self.lastDbModel = QStandardItemModel(self)
        self.ui.splitter_2.splitterMoved.connect(self.resizeEventV2)
        self.ui.pushButton_pop_combo.clicked.connect(self.populateCombo)

        self.ui.comboBox.currentIndexChanged.connect(self.selectionchange)

        self.ui.splitter.setSizes([50, 200])
        self.ui.splitter_2.setSizes([50, 200])
        self.createHistMenus()
        self.exportCSV_ = True
        self.resizeEventV2()

    def createAction(self, doTrigDEF, strName, strPathIcon, strTip, strShortCut):
        retAction = QAction(strName, self)
        retAction.triggered.connect(doTrigDEF)
        if strPathIcon:
            retAction.setIcon(QIcon(strPathIcon))
        if strTip:
            retAction.setStatusTip(strTip)
        if strShortCut:
            retAction.setShortcut(strShortCut)
        return retAction

    def selectionchange(self, index):
        tblName = self.ui.comboBox.itemText(index)
        doSelect = 'SELECT rowid,* FROM ' + tblName
        editModel = QSQLF.doQueryRetModel(self.pathDb, doSelect, self.db)
        if editModel:
            self.ui.tableView_Edit.setModel(editModel)

    def populateCombo(self):
        self.ui.comboBox.clear()
        comboModel = QStandardItemModel(self)
        comboModel = QSQLF.doQueryRetModel(self.pathDb, 'SELECT tbl_name  FROM sqlite_master WHERE type="table"', self.db)
        for i in range(comboModel.rowCount()):
            self.ui.comboBox.addItem(comboModel.data(comboModel.index(i, 0)))

    def exportClip(self):
        self.exportCSV_ = False
        self.exportCSV()
        self.exportCSV_ = True

    def copySelection(self):
        if self.focusWidget().__class__.__name__ != 'QTableView':
            print('Not TableView')
            return
        clipboardString = StringIO()
        selectedIndexes = self.focusWidget().selectedIndexes()
        if selectedIndexes:
            countList = len(selectedIndexes)
            for r in range(countList):
                current = selectedIndexes[r]
                displayText = current.data(QtCore.Qt.DisplayRole)
                if r+1 < countList:
                    next_ = selectedIndexes[r+1]
                    if next_.row() != current.row():
                        displayText += ("\n")
                    else:
                        displayText += ("\t") # or choose other separator
                clipboardString.write(displayText)
            pyperclip.copy(clipboardString.getvalue())

    def exportCSV(self):
        if self.focusWidget().__class__.__name__ != 'QTableView':
            print('Not TableView')
            return
        exportModel = QStandardItemModel(self)
        exportModel = self.focusWidget().model()
        if not  exportModel:
            return

        nrOfRows = exportModel.rowCount()
        nrOfCols = exportModel.columnCount()
        exportCSVStr = StringIO()

        for ch in range(nrOfCols):
            exportCSVStr.write(exportModel.horizontalHeaderItem(ch).text())
            exportCSVStr.write('\t')

        exportCSVStr.write('\n')

        for i in range(nrOfRows):
            for c in range(nrOfCols):
                endData = exportModel.data(exportModel.index(i, c)).encode(encoding='iso-8859-1', errors='ignore')
                exportCSVStr.write(str(endData, 'iso-8859-1').replace('\r', ''))
                exportCSVStr.write('\t')

            exportCSVStr.write('\n')

        if not self.exportCSV_:
            pyperclip.copy(exportCSVStr.getvalue())
            return

        text, okPressed = QInputDialog.getText(self, "Get text", "File Name:", QLineEdit.Normal, "")
        if okPressed and text != '':
            file = open(text+'.csv', 'w', encoding='iso-8859-1')
            file.write(exportCSVStr.getvalue())
            file.close()

    def onIni(self):
        lOdir = QStandardItemModel(self)
        selDir = 'SELECT * FROM LAST_DIR'
        lOdir = QSQLF.doQueryRetModel('settings.sqlite', selDir, self.db)
        self.lastOpenDir = lOdir.data(lOdir.index(0, 0))

    def createHistMenus(self):
        self.databaseMenu.clear()
        menuMod = QStandardItemModel(self)
        selLastP = 'SELECT * FROM LAST7PATH'
        menuMod = QSQLF.doQueryRetModel('settings.sqlite', selLastP, self.db)
        for i in range(menuMod.rowCount()):
            self.strMenu = menuMod.data(menuMod.index(i, 0))
            QAct = self.createAction(self.doOpendbPATH, self.strMenu, ":icons/"+str(i+1)+".ico", '', '')
            self.databaseMenu.addAction(QAct)

    def setingsDbexist(self, db_file):
        from pathlib import Path
        my_file = Path(db_file)
        if my_file.is_file():
            return True
        else:
            QSQLF.ini_settings(self.db)
            inQ = 'INSERT INTO LAST_DIR VALUES(" ");'
            QSQLF.doQueryRetModel('settings.sqlite', inQ, self.db)
            createQ = 'CREATE TABLE LAST7PATH (L_PATH TEXT);'
            QSQLF.doQueryRetModel('settings.sqlite', createQ, self.db)

            creaetView = """ CREATE VIEW KEEP7 AS
                            SELECT rowid FROM
                            (SELECT    LP1.rowid ,COUNT(LP2.rowid)  as cnt
                            FROM LAST7PATH as LP1,LAST7PATH as LP2
                            WHERE LP1.rowid<LP2.rowid
                            group by Lp1.rowid)
                            WHERE cnt>6 """

            QSQLF.doQueryRetModel('settings.sqlite', creaetView, self.db)
        return True

    def treeView_DB_RightCick(self):
        rowNum = self.ui.treeView_DB.selectionModel().currentIndex().row()
        tbl_name = str(self.treeModel.data(self.treeModel.index(rowNum, 1)))
        self.ui.plainTextEdit.setPlainText('SELECT * FROM ' + tbl_name)
        self.ui.tabWidget.setCurrentIndex(1)

    def treeView_DBclicked(self):
        rowNum = self.ui.treeView_DB.selectionModel().currentIndex().row()
        tbl_name = str(self.treeModel.data(self.treeModel.index(rowNum, 1)))
        self.treeModel_grid = QSQLF.doQueryRetModel(self.pathDb, 'SELECT sql FROM sqlite_master WHERE tbl_name="'
                                                    + tbl_name + '";', self.db)
        sql_TXT = self.treeModel_grid.data(self.treeModel_grid.index(0, 0))
        self.ui.plainTextEdit_2.setPlainText(sql_TXT)

    def closeThis(self):
        self.pathDb = ''
        self.treeModel.clear()
        self.ui.plainTextEdit_2.clear()

    def doQuery(self):
        mdl = QStandardItemModel(self)
        self.queryTXT = self.ui.plainTextEdit.toPlainText()
        self.ui.statusbar.showMessage('Sqlite Working...')
        mdl = QSQLF.doQueryRetModel(self.pathDb, self.queryTXT, self.db)
        self.ui.tableView.setModel(mdl)
        self.ui.statusbar.showMessage('Sqlite returned:' + str(mdl.rowCount()))

    def doOpendbPATH(self):
        sender = self.sender()
        print(sender.iconText())
        self.pathDb = sender.iconText()
        self.treeModel = QSQLF.doQueryRetModel(self.pathDb,
                                               'SELECT type,tbl_name FROM sqlite_master;', self.db)
        self.ui.treeView_DB.setModel(self.treeModel)
        lastDir = pathlib.Path(self.pathDb).parent
        QSQLF.doQueryRetModel('settings.sqlite', 'UPDATE LAST_DIR SET PATH_DIR="' + str(lastDir) + '";', self.db)
        QSQLF.doQueryRetModel('settings.sqlite', 'INSERT INTO LAST7PATH VALUES("' + self.pathDb + '");', self.db)
        QSQLF.doQueryRetModel('settings.sqlite',
                              'DELETE FROM LAST7PATH WHERE rowid NOT IN (SELECT rowid FROM LAST7PATH GROUP by L_PATH);', self.db)
        QSQLF.doQueryRetModel('settings.sqlite', 'DELETE FROM LAST7PATH WHERE rowid = (SELECT rowid FROM KEEP7);', self.db)

    def doOpendb(self):
        self.onIni()
        fname = QFileDialog.getOpenFileName(self, 'Open file', self.lastOpenDir.replace('\\', '/'), "Db files (*.sqlite *.db)")
        if str(fname[0]) != '':
            self.pathDb = str(fname[0])
            stat = self.statusBar()
            stat.showMessage(self.pathDb, -1)
        self.treeModel = QSQLF.doQueryRetModel(self.pathDb, 'SELECT type,tbl_name FROM sqlite_master;', self.db)
        self.ui.treeView_DB.setModel(self.treeModel)
        lastDir = pathlib.Path(self.pathDb).parent
        QSQLF.doQueryRetModel('settings.sqlite', 'UPDATE LAST_DIR SET PATH_DIR="' + str(lastDir) + '";', self.db)
        QSQLF.doQueryRetModel('settings.sqlite', 'INSERT INTO LAST7PATH VALUES("' + self.pathDb + '");', self.db)
        QSQLF.doQueryRetModel('settings.sqlite', 'DELETE FROM LAST7PATH ' +
                              'WHERE rowid NOT IN (SELECT rowid FROM LAST7PATH GROUP by L_PATH);', self.db)
        QSQLF.doQueryRetModel('settings.sqlite', 'DELETE FROM LAST7PATH WHERE rowid = (SELECT rowid FROM KEEP7);', self.db)
        self.createHistMenus()

    def resizeEvent(self, event):
        sxz = event.size()
        wh = sxz.width()-20
        hh = sxz.height()-40
        hhSplit = hh-45
        whSplit = wh-25
        self.ui.splitter.setGeometry(10, self.ui.splitter.y(), whSplit, hhSplit)
        self.ui.splitter_2.setGeometry(10, self.ui.splitter_2.y(), whSplit, hhSplit)
        self.ui.tabWidget.setGeometry(10, self.ui.tabWidget.y(), wh, hh)
        self.queryButton.setGeometry(self.ui.plainTextEdit.x()+self.ui.plainTextEdit.width()-75,
                                     self.ui.plainTextEdit.y() + self.ui.plainTextEdit.height()-20, 70, 20)
        self.ui.tableView_Edit.setGeometry(self.ui.tableView_Edit.x(), self.ui.tableView_Edit.y(), wh-20, hh-150)

    def resizeEventV2(self):
        self.queryButton.setGeometry(self.ui.plainTextEdit.x()+self.ui.plainTextEdit.width()-75,
                                     self.ui.plainTextEdit.y() + self.ui.plainTextEdit.height()-20, 70, 20)


if __name__ == "__main__":
    AppQt = QtWidgets.QApplication(sys.argv)
    WINDOW = MainWindow()
    WINDOW.show()
    sys.exit(AppQt.exec_())


    # changed 'default' was annoying! :)
    # \Python37-32\Lib\site-packages\pylint\checkers  format.py  options = (('max-line-length',

    # pyrcc5  res.qrc  -o resources.py
    # pyinstaller  --icon=icons/main.ico --onefile --noconsole --path\
    #  "C:\Portables\Python37-32\Lib\site-packages\PyQt5\Qt\bin" \
    #  "C:/Portables/Python37-32/Projects/PythonQtSqliteBrowser/sqliteBrowser.py"

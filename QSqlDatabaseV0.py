
from PyQt5 import QtSql
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QMessageBox

def ini_settings(db):
    db.setConnectOptions("SQLITE_OPEN_READWRITE")
    db.setDatabaseName('settings.sqlite')
    db.open()
    query = QtSql.QSqlQuery()
    query.exec_('BEGIN')
    query.exec_('CREATE TABLE LAST_DIR (PATH_DIR TEXT);')
    query.exec_('COMMIT')
    db.close()



def doQueryRetModel(db_file, exex_srt, db):
    MODEL = QStandardItemModel()
    if not db_file:
        QMessageBox.warning(None, 'Error', 'No connection')
        return MODEL

    db.setConnectOptions("QSQLITE_OPEN_READONLY")
    db.setDatabaseName(db_file)
   
    if not db.open():
        QMessageBox.warning(None, 'Error OPEN', str(db.open()))
        return MODEL

    query = QtSql.QSqlQuery()
    query.setForwardOnly(True)
    err = QtSql.QSqlError()
    if not query.exec_(exex_srt):
        err = query.lastError()
        sqlite_ERR = int(err.nativeErrorCode())
        if sqlite_ERR in(8, 21):
            db.close()
            db.setConnectOptions("SQLITE_OPEN_READWRITE")
            db.open()
            query.exec_('BEGIN')
            str_Queries = exex_srt.split(';')

            for strq in str_Queries:
                if strq:
                    query.exec_(strq)
            query.exec_('COMMIT')
            err = query.lastError()
            db.close()
            return MODEL
        elif sqlite_ERR != 0:
            QMessageBox.warning(None, 'Error', err.text())
            return MODEL
    else:
        coutColums = query.record().count()
        MODEL.setColumnCount(coutColums)
        for c in range(coutColums):
            MODEL.setHorizontalHeaderItem(c, QStandardItem(query.record().fieldName(c)))
            items = []
        while query.next():
            for co in range(coutColums):
                items.append(QStandardItem( str(query.value(co))))
                #print(query.value(c))
            MODEL.appendRow(items)
            items = []  
        db.close()
        #print(MODEL.rowCount())
        return MODEL

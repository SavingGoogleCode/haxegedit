import Configuration
import os
from gi.repository import GObject, Gtk, Gdk, Gedit, Gio, GLib
import string

class OutputPanel(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "OutputPanel"
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self, plugin):
        GObject.Object.__init__(self)
        self.plugin = plugin
        self.dataDir = plugin.plugin_info.get_data_dir()
        self.geditWindow = plugin.window
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.dataDir + "/" + "ui" + "/" + "OutputWindow.glade")
        self.builder.connect_signals(self)
        
        self.scrolledWindow = self.builder.get_object("scrolledWindow")
        
        self.textView = self.builder.get_object("textView")
        self.textView.set_editable (False)
        self.textView.modify_fg(Gtk.StateType.NORMAL, Gdk.Color(red=65535, green=65535, blue=65535))
        self.textView.modify_bg(Gtk.StateType.NORMAL, Gdk.Color(red=11776, green=13312, blue=13824))
        self.textView.modify_bg(Gtk.StateType.SELECTED, Gdk.Color(red=51776, green=0, blue=0))
        self.textView.connect("button-press-event", self.onTextViewClick)

        self.geditBottomPanel = self.geditWindow.get_bottom_panel()
        self.geditBottomPanel.add_item(self.scrolledWindow, "haxe_output_panel", "errors", Gtk.Image.new_from_file(self.dataDir + "/" + "icons" + "/" + "haxe_logo_16.png"))# Gtk.Image.new_from_stock(Gtk.STOCK_YES, Gtk.IconSize.MENU))
        self.geditBottomPanel.activate_item(self.scrolledWindow)
        
    def activate(self):
        self.geditBottomPanel.activate_item(self.scrolledWindow)
        
    def remove(self):
        self.geditBottomPanel.remove_item(self.scrolledWindow)
    
    def setText(self, txt):
        textBuffer = self.textView.get_buffer()
        textBuffer.set_text(txt)
        
    def appendText(self, txt):
        textBuffer = self.textView.get_buffer()
        textBuffer.insert(textBuffer.get_end_iter(), txt)
        self.textView.scroll_mark_onscreen(textBuffer.get_insert())
        #self.textView.scroll_to_mark(textBuffer.get_insert(), 0)    
        
    def onTextViewClick(self, textView, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            errorInfo = self.parseErrorLine()
            if errorInfo == None:
                return True
            characterRange = errorInfo['characterRange']
            if characterRange.find('-') == -1:
                characterRange = characterRange + "-" + characterRange
            charRange = characterRange.split("-")
            charRangeStart = int(charRange[0])
            charRangeEnd = int(charRange[1])
            lineNr = int(errorInfo['lineNumber'])
            offset = charRangeEnd
            if errorInfo['error'].startswith('Unexpected'):
                offset = charRangeStart

            if errorInfo['fileLocation'][0] == "/" :
                path = "/" + errorInfo['fileLocation']
            else:
                hxml = self.plugin.sf(Configuration.getHxml())
                path = os.path.dirname(hxml) + "/" + errorInfo['fileLocation']
                
            gio_file = Gio.file_new_for_path(path)
            tab = self.geditWindow.get_tab_from_location(gio_file)
            if tab == None:
                tab = self.geditWindow.create_tab_from_location(gio_file, None, lineNr, offset+1, False, True )
            else:
                self.geditWindow.set_active_tab(tab)
                view = self.geditWindow.get_active_view()
                buf = view.get_buffer() 
                i = buf.get_iter_at_line_offset(lineNr - 1, offset)
                buf.place_cursor(i)
                view.scroll_to_cursor()

            if errorInfo['error'].find(' should be ') != -1 or errorInfo['error'].startswith('Unknown identifier') or errorInfo['error'].startswith('Class not found'):
                view = self.geditWindow.get_active_view()
                buf = view.get_buffer()
                
                insertMark = buf.get_insert()
                selectionBoundMark = buf.get_selection_bound()
                startIter = buf.get_iter_at_mark(insertMark)
                startIter.backward_chars(charRangeEnd - charRangeStart)
                buf.move_mark(selectionBoundMark, startIter)
                
            if errorInfo['error'].startswith('Unexpected'):
                view = self.geditWindow.get_active_view()
                buf = view.get_buffer()
                
                insertMark = buf.get_insert()
                selectionBoundMark = buf.get_selection_bound()
                startIter = buf.get_iter_at_mark(insertMark)
                startIter.forward_chars(charRangeEnd - charRangeStart)
                buf.move_mark(selectionBoundMark, startIter)
                
            if errorInfo['error'].startswith("Invalid character"):
                view = self.geditWindow.get_active_view()
                buf = view.get_buffer()
                
                insertMark = buf.get_insert()
                selectionBoundMark = buf.get_selection_bound()
                startIter = buf.get_iter_at_mark(insertMark)
                startIter.forward_chars(1)
                buf.move_mark(selectionBoundMark, startIter)

            return True
                        
        if event.type == Gdk.EventType._3BUTTON_PRESS:
            errorInfo = self.parseErrorLine()
            if errorInfo != None and errorInfo['errorLine'].endswith("Missing ;"):
                self.geditWindow.get_active_document().insert_at_cursor (";")
            return True
        
    def parseErrorLine(self):
        doc = self.textView.get_buffer()
        iter = doc.get_iter_at_mark(doc.get_insert())
        lineStart = iter.copy()
        lineEnd = iter.copy()
        lineStart.set_offset (iter.get_offset () - iter.get_line_offset ())
        
        #get the complete line
        lineEnd.forward_to_line_end()
        currentLine = unicode (doc.get_text (lineStart, lineEnd, include_hidden_chars=True))
        if len(currentLine)==0:
            return None
        #print currentLine;
        
        #get the file location
        locationEnd = lineStart.copy()
        while locationEnd.forward_char():
            char = unicode(locationEnd.get_char())
            if char == ":":
                fileLocation = unicode (doc.get_text (lineStart, locationEnd, include_hidden_chars=True))
                lineNumberEnd = locationEnd.copy()
                #print fileLocation
                break
        try:
            lineNumberEnd
        except NameError:
            return None
            
        #get the line number
        locationEnd.forward_char()#skip colon
        while lineNumberEnd.forward_char():
            char = unicode(lineNumberEnd.get_char())
            if char == ":":
                lineNumber = unicode (doc.get_text (locationEnd, lineNumberEnd, include_hidden_chars=True))
                #print lineNumber
                break
        
        #get characters or lines range
        characterRange="0-0"
        lineRange="0-0"
        
        lineNumberEnd.forward_char()#skip colon
        lineNumberEnd.forward_char()#skip space
        
        rangeStart = lineNumberEnd.copy()
        lineNumberEnd.forward_word_end()#skip 'characters'
        rangeType = unicode (doc.get_text (rangeStart, lineNumberEnd.copy(), include_hidden_chars=True))
        
        lineNumberEnd.forward_char()#skip space
        characterRangeEnd = lineNumberEnd.copy()
        while characterRangeEnd.forward_char():
            char = unicode(characterRangeEnd.get_char())
            if char == " ":
                tempRange = unicode (doc.get_text (lineNumberEnd, characterRangeEnd, include_hidden_chars=True))
                if rangeType == "characters":
                    characterRange = tempRange
                elif rangeType == "lines":
                    lineRange = tempRange;
                #print characterRange
                #print lineRange
                break
        
        #get error
        characterRangeEnd.forward_char()#skip space
        characterRangeEnd.forward_char()#skip colon
        characterRangeEnd.forward_char()#skip space
        
        errorEnd = characterRangeEnd.copy()
        errorEnd.forward_sentence_end()
        error = unicode (doc.get_text (characterRangeEnd, errorEnd, include_hidden_chars=True))
        
        return {'errorLine':currentLine, 'fileLocation':fileLocation, 'lineNumber':lineNumber, 'characterRange':characterRange, 'lineRange':lineRange, 'error':error}

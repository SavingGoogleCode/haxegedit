from gi.repository import GObject, Gtk, Gdk, Gedit
import string


class CompletionWindow(Gtk.Window):

    def init_frame(self):
        """Initialize the frame and scroller around the tree view."""
        self.set_size_request(400, 400)
        scroller = Gtk.ScrolledWindow()
        #scroller.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_NEVER)
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.view)
        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.OUT)
        hbox = Gtk.HBox()
        hbox.add(scroller)

        #self.text = Ggtk.TextView()
        #self.text_buffer = Gtk.TextBuffer()
        #self.text.set_buffer(self.text_buffer)
        #self.text.set_size_request(300, 200)
        #self.text.set_sensitive(False)

        #scroller_text = Gtk.ScrolledWindow() 
        #scroller_text.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_AUTOMATIC)
        #scroller_text.add(self.text)
        #hbox.add(scroller_text)
        frame.add(hbox)
        self.add(frame)

    def init_tree_view(self):
        """Initialize the tree view listing the completions."""

        self.store = Gtk.ListStore(GObject.TYPE_STRING)
        self.view = Gtk.TreeView(self.store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("", renderer, text=0)
        self.view.append_column(column)
        self.view.set_enable_search(False)
        self.view.set_headers_visible(False)
        self.view.set_rules_hint(True)
        selection = self.view.get_selection()
        #selection.set_mode(Gtk.SELECTION_SINGLE)
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        self.view.set_size_request(400, 200)
        self.view.connect('row-activated', self.row_activated)
        self.view.connect('cursor-changed', self.row_selected)

    """Window for displaying a list of completions."""

    def __init__(self, parent, plugin):

        Gtk.Window.__init__(self, type=Gtk.WindowType.TOPLEVEL);
        self.connect('key-press-event', self.key_press_event)
        self.set_decorated(False)
        self.store = None
        self.view = None
        self.set_transient_for(parent)

        self.set_border_width(1)
        self.init_tree_view()
        self.init_frame()

        self.connect('focus-out-event', self.focus_out_event) 
        

        self.gedit_window = parent
        self.plugin = plugin

        # temporary string used to filter the possible completions 
        self.tempstr = ""
        self.current_completions = []
        self.completions = None

        #self.grab_focus()


    ################### USEFUL CODE GOES BEYOND THAT LINE ######################

    def insert (self, s):
        """ Insert a character in the active document at the insert mark """
        self.gedit_window.get_active_document ().insert_at_cursor (s)

    def delete (self, quantity):
        """ Deletes a number of characters from the active document,
            starting from the insert mark. """
        doc = self.gedit_window.get_active_document ()
        insert = doc.get_iter_at_mark (doc.get_insert ())
        before = doc.get_iter_at_mark (doc.get_insert ())
        before.set_offset (insert.get_offset () - quantity)
        doc.delete (insert, before)        
    
    def temp_add (self, char):
        """ Adds a character or more to the temporary selection. This inserts it
            on screen as well."""
        self.tempstr += char
        self.gedit_window.get_active_document ().insert_at_cursor (char)
        self.set_completions (self.completions, self.tempstr)

    def temp_clear (self):
        """ Clears the temporary word, both internally and on screen """
        self.delete (len (self.tempstr))
        self.tempstr = ""
        self.set_completions (self.completions)

    def temp_remove (self):
        """ Remove a character in the selection """
        self.tempstr = self.tempstr[:-1]
        self.delete (1)
        self.set_completions (self.completions, self.tempstr)
 
    def key_press_event(self, widget, event):
        #print "popup event.keyval %s" % event.keyval
        #print "self.plugin tempstring %s" plugin.tempstring
        #print "self.plugin islaunching %s" plugin.islaunching
        if self.plugin.islaunching:
            self.tempstr = self.plugin.tempstring
            self.plugin.islaunching = False
        """ Respond to a keyboard event. """
        ctrl_pressed = (event.state & Gdk.ModifierType.CONTROL_MASK) == Gdk.ModifierType.CONTROL_MASK
        # Escape
        if event.keyval == Gdk.KEY_Escape:
            self.destroy ()
        # Backspace
        elif event.keyval == Gdk.KEY_BackSpace:
            if self.tempstr == "":
                self.destroy ()
            else:
                if not ctrl_pressed:
                    self.temp_remove ()
                else:
                    self.temp_clear ()
        # Tab
        elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_Tab):
            self.complete()
        # Space
        elif event.keyval == Gdk.KEY_space:
            if self.complete ():
                self.insert (" ")
        # Dot
        # It completes the word, and launches the completion again for the next word.
        elif event.keyval == Gdk.KEY_period:
            if self.complete ():
                self.plugin.on_view_key_press_event (self.gedit_window.get_active_view (), event)
                self.gedit_window.get_active_document ().insert_at_cursor (event.string)
        # everything else !
        else:
            if len(event.string) > 0:
                self.temp_add (event.string)


    def complete(self, hide=True):
        try:
            completion = self.current_completions[ self.get_selected () ]['abbr']
            completion = completion[len(self.tempstr):]

            self.insert (completion)
            if hide:
                self.destroy ()
            return True
        except:
            return False

    def focus_out_event(self, *args):
        self.destroy ()
    
    def get_selected(self):
        """Get the selected row."""
        selection = self.view.get_selection()
        #return selection.get_selected_rows()[1][0][0]
        return selection.get_selected_rows()[1][0].get_indices()[0]

    def row_selected(self, treeview, data = None):
        selection = self.get_selected ()
        # TODO Display the documentation if any.
        # info = self.current_completions[selection] ['info']
        # self.text_buffer.set_text (info)

    def row_activated(self, tree, path, view_column, data = None):
        """ The user chose a completion, so terminate it. """
        self.complete()

    def set_completions(self, completions, filter=""):
    
        #doc = self.gedit_window.get_active_document ()
        #insert = doc.get_iter_at_mark (doc.get_insert ())
        #curpos = insert.get_offset ()
        #offset =  insert.get_line_offset ()
        #text = unicode (doc.get_text (*doc.get_bounds (),include_hidden_chars=True), 'utf-8')
        #print "-------------------"
        #print "popup set_completions"
        #print "popup curpos=%s" % curpos
        #print "popup offset=%s" % offset
        #print "popup filter=%s" % filter
        #print "-------------------"
        #print "text=%s" % text
        
        """Set the completions to display."""
        self.completions = completions
        self.current_completions = []
        self.resize(1, 1)

        self.store.clear()

        self.tempstr = filter
        for completion in completions:
            if filter == "" or completion['abbr'].startswith (filter):
                self.store.append([unicode(completion['word'])])
                self.current_completions.append (completion)
        self.view.columns_autosize()

        if len (self.current_completions) > 0:
            self.view.get_selection().select_path(0)
        else:
            #print "len (self.current_completions) %s" % len (self.current_completions)
            self.destroy ()

    def set_font_description(self, font_desc):
        """Set the label's font description."""
        self.view.modify_font(font_desc)

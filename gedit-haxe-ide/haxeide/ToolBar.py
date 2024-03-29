import os
from gi.repository import GObject, Gedit, Gtk, Gio
import Configuration

class ToolBar(GObject.Object, Gedit.WindowActivatable):
    __gtype_name__ = "ToolBar"
    window = GObject.property(type=Gedit.Window)
    
    def __init__(self, plugin):
        GObject.Object.__init__(self)
        self.plugin = plugin
        self.dataDir = plugin.plugin_info.get_data_dir()
        self.geditWindow = plugin.window
        self.setup()

    def setup(self):
        vbox = self.geditWindow.get_children()[0]
        self.geditToolbar = vbox.get_children()[1]
        
        self.separator1 = Gtk.SeparatorToolItem()
        
        self.sessionsButton = Gtk.MenuToolButton()

        self.haxeButton = Gtk.ToolButton(icon_widget=Gtk.Image.new_from_file(self.dataDir+"/"+"icons"+"/"+ "haxe_logo_24.png"))
        self.haxeButton.connect("clicked", self.onHaxeButtonClick)
        
        self.debugButton = Gtk.ToolButton(icon_widget=Gtk.Image.new_from_file(self.dataDir+"/"+"icons"+"/"+ "bug_grey_16.png"))
        self.debugButton.connect("clicked", self.onDebugButtonClick)
        
        self.hxmlButton = Gtk.ToolButton(stock_id=Gtk.STOCK_PROPERTIES)
        self.hxmlButton.connect("clicked", self.onHxmlButtonClick)
        
        self.playButton = Gtk.ToolButton(stock_id=Gtk.STOCK_MEDIA_PLAY)
        self.playButton.connect("clicked", self.onPlayButtonClick)
        
        self.buildButton = Gtk.ToolButton(stock_id=Gtk.STOCK_EXECUTE) #Gtk.STOCK_MEDIA_PLAY
        self.buildButton.set_is_important(True)
        self.buildButton.connect("clicked", self.onBuildButtonClick)
        
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.separator1)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.sessionsButton)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.haxeButton)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.hxmlButton)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.debugButton)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.playButton)
        self.geditToolbar.insert(pos = len(self.geditToolbar.get_children()),item = self.buildButton)
        self.geditToolbar.show_all()

        self.h0 = self.geditWindow.connect("active-tab-changed", self.onActiveTabChange)
        self.h1 = self.geditWindow.connect("active-tab-state-changed", self.onActiveTabStateChange)
        self.h2 = self.geditWindow.connect("tab-added", self.onTabAdded)    
        self.h3 = self.geditWindow.connect("tab-removed", self.onTabRemoved)

        Configuration.settings().connect("changed::hxml-uri", self.setHxml)
        Configuration.settings().connect("changed::sessions", self.getSessions)
        Configuration.settings().connect("changed::session-path-offset", self.getSessions)
        
        self.resetButtons()
        self.getSessions(None, None)
        self.onActiveTabStateChange(self.geditWindow)
        
    def getSessions(self, settings, skey):
        item = Gtk.MenuItem("save session")
        item.connect("activate", self.saveSession)
        self.menu = Gtk.Menu()
        self.menu.add(item)
        self.menu.add(Gtk.SeparatorMenuItem())
        self.sessionsHash = Configuration.getSessions()
        for key in self.sessionsHash:
            item = Gtk.MenuItem(os.path.basename(os.path.dirname(key)))
            item.connect("activate", self.onProjectsChange, key)
            self.menu.add(item)
        self.menu.show_all()
        self.sessionsButton.set_menu(self.menu)
        
    def resetButtons(self):
        self.haxeButton.set_tooltip_text('Open haXe panel')
        self.haxeButton.set_sensitive(True)
        
        self.sessionsButton.set_tooltip_text('Open session')
        self.sessionsButton.set_sensitive(True)
        
        self.hxmlButton.set_tooltip_text('Select active document as hxml')
        self.hxmlButton.set_sensitive(False)
        
        self.hxmlButton.set_tooltip_text('Run output')
        self.hxmlButton.set_sensitive(False)
        
        self.hxmlButton.set_tooltip_text('Debug project')
        self.hxmlButton.set_sensitive(False)
        
        self.buildButton.set_tooltip_text('Build project')
        self.buildButton.set_is_important(True)
        self.buildButton.set_label("")
        self.buildButton.set_sensitive(False)

    def remove(self):
        self.geditToolbar.remove(self.separator1)
        self.geditToolbar.remove(self.sessionsButton)
        self.geditToolbar.remove(self.haxeButton)
        self.geditToolbar.remove(self.debugButton)
        self.geditToolbar.remove(self.hxmlButton)
        self.geditToolbar.remove(self.buildButton)

        self.geditWindow.disconnect(self.h0)
        self.geditWindow.disconnect(self.h1)
        self.geditWindow.disconnect(self.h2)
        self.geditWindow.disconnect(self.h3)
    
    def onActiveTabStateChange(self, window):
        doc = window.get_active_document()
        if(doc != None):
            self.hxmlButton.set_sensitive(doc.get_uri_for_display().endswith(".hxml"))
        
    def onTabAdded(self, window, tab):
        doc = window.get_active_document()
        if(doc != None):
            self.hxmlButton.set_sensitive(doc.get_uri_for_display().endswith(".hxml"))
            
    def onTabRemoved(self, window, tab):
        doc = window.get_active_document()
        if(doc == None):
            self.hxmlButton.set_sensitive(False)
        else:
            self.hxmlButton.set_sensitive(doc.get_uri_for_display().endswith(".hxml"))
    
    def onActiveTabChange(self, window, tab):
        doc = window.get_active_document()
        self.hxmlButton.set_sensitive(doc.get_uri_for_display().endswith(".hxml"))

    def saveSession(self, button):
        self.plugin.saveSession()
    
    def onProjectsChange(self, item, data):
        self.handleCloseAllDocuments()
        self.plugin.openSession(data, True, True)
     
    def onHaxeButtonClick(self, button):
        self.plugin.showHaxeWindow()
    
    def onBuildButtonClick(self, button):
        self.plugin.saveAndBuild()
        
    def onHxmlButtonClick(self, button):
        self.plugin.setActiveDocAsHxml()
        
    def onPlayButtonClick(self, button):
        self.plugin.runApplication(Configuration.getHxml())
        
    def onDebugButtonClick(self, button):
        Gedit.App.get_default().get_active_window().get_side_panel().set_property("visible", True)
        self.plugin.debuggerInfoPanel.activate()
        
        Gedit.App.get_default().get_active_window().get_bottom_panel().set_property("visible", True)
        self.plugin.debuggerPanel.activate()
        
    def setHxml(self, settings, key):
        hxml = Configuration.getHxml()
        if hxml=="" or hxml == None:
            self.resetButtons()
            return
        parts = hxml.split("/")
        l = len(parts)
        label = parts[l-2]

        if Configuration.getToolBarShowHxml():
             label = label + "/" + parts[l-1]
        
        self.buildButton.set_label(label)
        self.buildButton.set_sensitive(True)
        self.debugButton.set_sensitive(True)
        self.hxmlButton.set_tooltip_text(hxml)

    def handleCloseAllDocuments(self):
        #if self.builder.get_object("closeTabsCheckBox").get_active():
        unsavedDocuments = self.plugin.window.get_unsaved_documents()
        tabsToClose = []
        for d in self.plugin.window.get_documents():
            if not d in unsavedDocuments or d.is_untouched() or d.is_untitled():
                tabsToClose.append(Gedit.Tab.get_from_document(d));
        self.plugin.window.close_tabs(tabsToClose)    
            
    #sanitize file
    def sf(self, path):
        if path == None or path=="":
            return path
        if path[1]=="/":
            return path[1:]
        return path    
        

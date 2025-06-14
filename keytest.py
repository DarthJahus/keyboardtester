# keytest.py
# version nettoyée : ANSI uniquement, scan codes en hexa, distinction L/R via ext

import wx
import gui
import pyWinhook as pyHook
import maps
import win32con
import win32gui


import os
import sys


def resource_path(relative_path):
    """Get path to resource, works for PyInstaller and normal execution"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)


class KeyTest(gui.keytest):
  def __init__(self, parent):
    gui.keytest.__init__(self, parent)

    self.SetIcon(wx.Icon(resource_path("resources/kade.ico"), wx.BITMAP_TYPE_ICO))

    # Affiche uniquement le clavier ANSI
    self.m_us.Show()
    if hasattr(self, 'm_us_statictext'):
      self.m_us_statictext.SetLabel("ANSI Keyboard")
    if hasattr(self, 'm_uk'):
      self.m_uk.Hide()
    if hasattr(self, 'm_keyboard'):
      self.m_keyboard.Hide()
    if hasattr(self, 'm_speak'):
      self.m_speak.Hide()

    # Load both dicts : ext=0 and ext=1 for extended keys
    self.key_dict_normal = maps.get_key_dictionary(self, ext=0)
    self.key_dict_extended = maps.get_key_dictionary(self, ext=1)

    self.setDummyFocus()

    self.hm = pyHook.HookManager()
    self.hm.KeyDown = self.OnKeyboardEvent
    self.hm.KeyUp = self.OnKeyboardEvent

    # hook only if focused
    self.Bind(wx.EVT_ACTIVATE, self.onActivate)
    if self.IsActive():
      self.hm.HookKeyboard()

    # Disable AlwaysOnTop
    hwnd = self.GetHandle()
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                          win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    self.m_list.InsertColumn(0, 'Key Code')
    self.m_list.InsertColumn(1, 'ASCII Code')
    self.m_list.InsertColumn(2, 'Scan')
    self.m_list.InsertColumn(3, 'Ext')
    self.m_list.InsertColumn(4, 'Window in Focus')
    self.m_list.InsertColumn(5, 'Event')
    self.m_list.SetColumnWidth(0, 128)
    self.m_list.SetColumnWidth(1, 78)
    self.m_list.SetColumnWidth(2, 70)
    self.m_list.SetColumnWidth(3, 28)
    self.m_list.SetColumnWidth(4, 200)
    self.m_list.SetColumnWidth(5, 70)

    self.last_event = None
    self.height = self.Size[1]

    self.UI(initial=True)

  @staticmethod
  def setFontSize(field, size):
    font = field.GetFont()
    font.SetPointSize(size)
    field.SetFont(font)

  def OnKeyboardEvent(self, event):
    # Block key events if the window has focus
    fg_window = win32gui.GetForegroundWindow()
    my_window = self.GetHandle()
    block_event = (fg_window == my_window)
    gui_object = self.getGUIObject(event.ScanCode, event.Extended)
    if gui_object:
      if "down" in event.MessageName:
        gui_object.SetBackgroundColour(wx.GREEN)
      else:
        gui_object.SetBackgroundColour(wx.NullColour)

    if self.last_event != (event.ScanCode, event.MessageName):
      if not hasattr(self, 'm_show_up') or self.m_show_up.GetValue() or "down" in event.MessageName:
        try:
          idx = self.m_list.InsertItem(0, f"{event.Key} ({event.KeyID})")
          self.m_list.SetItem(idx, 1, f"{chr(event.Ascii)} ({event.Ascii})")
          self.m_list.SetItem(idx, 2, f"0x{event.ScanCode:02X} ({event.ScanCode})")
          self.m_list.SetItem(idx, 3, str(event.Extended))
          self.m_list.SetItem(idx, 4, event.WindowName or "")
          self.m_list.SetItem(idx, 5, event.MessageName.title().replace("Sys ", ""))

          self.m_last_key.SetValue(f"{event.Key} (0x{event.ScanCode:02X})")

        except Exception as e:
          print(f"Error logging event: {e}")

    self.last_event = (event.ScanCode, event.MessageName)
    return not block_event

  def getGUIObject(self, scan_code, extended):
    key_dict = self.key_dict_extended if extended else self.key_dict_normal
    for item in key_dict:
      if item[0] == scan_code:
        return item[1]
    return None

  def setDummyFocus(self):
    self.m_dummy.SetFocus()

  def clearGUI(self, clear_log=False):
    if clear_log:
      self.m_list.DeleteAllItems()
    for obj in self.key_dict_normal + self.key_dict_extended:
      obj[1].SetBackgroundColour(wx.NullColour)
    self.setDummyFocus()

  def UI(self, initial=False):
    if initial or self.height != self.Size[1]:
      self.height = self.Size[1]
      if hasattr(self, 'm_show_up') and hasattr(self, 'm_clear_list') and hasattr(self, 'm_show_log'):
        if self.height < 360:
          self.m_show_up.Disable()
          self.m_clear_list.Disable()
          self.m_show_log.SetLabel("Show Activity Log")
          self.m_show_log.SetToolTip("Show the keyboard activity log")
        else:
          self.m_show_up.Enable()
          self.m_clear_list.Enable()
          self.m_show_log.SetLabel("Hide Activity Log")
          self.m_show_log.SetToolTip("Hide the keyboard activity log")
      self.Layout()

  def onLog(self, event):
    if self.Size[1] < 372:
      self.SetSize((800, 597))
    else:
      self.SetSize((800, 330))
    self.m_dummy.SetFocus()

  def onUI(self, event):
    self.UI()

  def onButton(self, event):
    self.setDummyFocus()

  def onGUIClick(self, event):
    self.setDummyFocus()

  def onClear(self, event):
    self.clearGUI(clear_log=True)

  def onAbout(self, event):
    about = AboutBox(None)
    about.ShowModal()
    about.Destroy()

  def onActivate(self, event):
    if event.GetActive():
      self.hm.HookKeyboard()
    else:
      self.hm.UnhookKeyboard()
    event.Skip()

  def onClose(self, event):
    self.Destroy()


class AboutBox(gui.AboutBox):
  def __init__(self, parent):
    gui.AboutBox.__init__(self, parent)

  def onOK(self, event):
    self.Close()
    self.Destroy()


def main():
  app = wx.App()
  KeyTest(None).Show()
  app.MainLoop()
  app.Destroy()


if __name__ == "__main__":
  main()

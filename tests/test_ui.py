"""Integration checks against a real Tk event loop (requires a display)."""
from pathlib import Path
import tempfile
import tkinter as tk
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from main import TriangleApp
from config_manager import ConfigStore


class UITests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f'No graphical display: {exc}')
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.errors = []
        self.root.report_callback_exception = lambda *args: self.errors.append(args)
        self.app = TriangleApp(self.root, ConfigStore(self.path/'settings.json', self.path/'absent.json'))
        self.root.update()

    def tearDown(self):
        if hasattr(self, 'app'):
            for job in self.root.tk.call('after', 'info'):
                self.root.after_cancel(job)
            self.app.overlay.destroy()
            self.root.destroy()
            self.tmp.cleanup()
            self.assertEqual(self.errors, [])

    def test_invalid_entry_keeps_valid_shape(self):
        before = self.app.state.to_dict()
        self.app.vars['width'].set('abc')
        self.assertFalse(self.app.controls_changed())
        self.assertEqual(self.app.state.to_dict(), before)
        self.assertIn('số nguyên', self.app.status_label.cget('text'))
        self.app.quick_preset(400,300,False)
        self.assertEqual(self.app.state.width,400)

    def test_sync_updates_dimensions_and_preview_statistics(self):
        self.app.quick_preset(400,300,False)
        self.app.vars['sync'].set(True)
        self.app.controls_changed()
        self.assertEqual((self.app.state.width,self.app.state.height),(400,400))
        self.assertEqual(self.app.height_entry.cget('state'),'disabled')
        self.assertEqual(self.app.stat_labels['area'].cget('text'),'80,000 px²')

    def test_undo_redo_and_new_branch(self):
        old=self.app.state.to_dict()
        self.app.quick_preset(400,300,False)
        changed=self.app.state.to_dict()
        self.app.undo()
        self.assertEqual(self.app.state.to_dict(),old)
        self.app.redo()
        self.assertEqual(self.app.state.to_dict(),changed)
        self.app.undo()
        self.app.change(color='#FF7897')
        self.app.commit_history()
        self.assertEqual(self.app.future,[])

    def test_overlay_reuse_move_resize_lock_and_hide(self):
        app=self.app
        app.quick_preset(200,150,False)
        app.toggle_overlay();self.root.update()
        first=app.overlay.window
        self.assertTrue(app.overlay.visible)
        app.toggle_overlay();self.root.update()
        self.assertFalse(app.overlay.visible)
        app.toggle_overlay();self.root.update()
        self.assertIs(app.overlay.window,first)
        start=list(app.overlay.anchor)
        e=SimpleNamespace(x_root=100,y_root=100)
        app.overlay.start_move(e)
        app.overlay.move(SimpleNamespace(x_root=120,y_root=130))
        app.overlay.finish_move()
        self.assertEqual(app.overlay.anchor,[start[0]+20,start[1]+30])
        app.overlay.start_resize(e)
        app.overlay.resize(SimpleNamespace(x_root=150,y_root=80))
        app.overlay.finish_resize()
        self.assertEqual((app.state.width,app.state.height),(250,170))
        app.change(locked=True)
        before=app.state.to_dict()
        anchor=list(app.overlay.anchor)
        app.overlay.start_move(e)
        app.overlay.move(SimpleNamespace(x_root=400,y_root=400))
        app.overlay.wheel(SimpleNamespace(delta=120))
        self.assertEqual(app.state.to_dict(),before)
        self.assertEqual(app.overlay.anchor,anchor)
        app.overlay.hide()
        self.assertTrue(self.root.winfo_exists())

    def test_import_export_and_named_preset(self):
        app=self.app
        with patch('main.simpledialog.askstring',return_value='Mẫu Nguyễn'):
            app.save_preset()
        self.assertIn('Mẫu Nguyễn',app.presets)
        config=self.path/'export.json'
        with patch('main.filedialog.asksaveasfilename',return_value=str(config)):
            app.export_config()
        saved=app.state.to_dict()
        app.quick_preset(560,240,False)
        with patch('main.filedialog.askopenfilename',return_value=str(config)), patch('main.messagebox.askyesno',return_value=True):
            app.import_config()
        self.assertEqual(app.state.to_dict(),saved)
        self.assertTrue((self.path/'before-import.json').exists())
        app.persist()
        self.assertEqual(app.store.load()['presets'],app.presets)

    def test_minimum_window_and_tabs_render(self):
        self.root.geometry('980x680')
        for index in range(3):
            self.app.notebook.select(index)
            self.root.update()
            self.assertGreater(self.app.canvas.winfo_width(),500)
            self.assertGreater(self.app.canvas.winfo_height(),200)


if __name__=='__main__':
    unittest.main()

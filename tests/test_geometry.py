import math
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from triangle_logic import TriangleState, vertices, bounded_vertices, measurements, export_png, export_svg
from config_manager import ConfigStore, normalize_payload


class GeometryTests(unittest.TestCase):
    def test_345_triangle(self):
        result = measurements(TriangleState(width=400, height=300))
        self.assertAlmostEqual(result['area'], 60000)
        self.assertAlmostEqual(result['perimeter'], 1200)
        self.assertAlmostEqual(result['hypotenuse'], 500)
        self.assertAlmostEqual(result['angle_a']+result['angle_b']+result['angle_c'], 180)
        self.assertAlmostEqual(result['angle_a'], 53.13010235415598)

    def test_rotation_flip_preserve_lengths_and_area(self):
        for angle in (0, 17, 90, 180, 270, 359):
            for flip_x in (False, True):
                for flip_y in (False, True):
                    s = TriangleState(width=400, height=300, rotation=angle, flip_x=flip_x, flip_y=flip_y)
                    a,b,c = vertices(s)
                    self.assertAlmostEqual(math.dist(a,b),300)
                    self.assertAlmostEqual(math.dist(b,c),400)
                    self.assertAlmostEqual(math.dist(a,c),500)
                    area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
                    self.assertAlmostEqual(area,60000)
                    pts,w,h=bounded_vertices(s)
                    self.assertTrue(all(0 <= x <= w and 0 <= y <= h for x,y in pts))

    def test_reject_bad_input(self):
        for data in ({'width':0}, {'height':3001}, {'width':float('nan')}, {'rotation':float('inf')},
                     {'width':30.5}, {'width':True}, {'color':'red'}, {'opacity':0},
                     {'topmost':'false'}, {'line_width':50}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                TriangleState.from_dict(data)

    def test_sync_and_rotation_normalization(self):
        s=TriangleState.from_dict({'width':250,'height':100,'sync':True,'rotation':-90})
        self.assertEqual((s.width,s.height,s.rotation),(250,250,270))

    def test_transparent_exports(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            for filled in (True, False):
                state=TriangleState(width=400,height=300,opacity=.5,filled=filled,rotation=37)
                png,svg=Path(folder)/'image.png',Path(folder)/'image.svg'
                export_png(state,png);export_svg(state,svg)
                with Image.open(png) as im:
                    self.assertEqual(im.mode,'RGBA')
                    self.assertEqual(im.getpixel((0,0))[3],0)
                    pts,w,h=bounded_vertices(state)
                    self.assertEqual(im.size,(w,h))
                    middle=(round(sum(p[0] for p in pts)/3),round(sum(p[1] for p in pts)/3))
                    self.assertEqual(im.getpixel(middle)[3],128 if filled else 0)
                polygon=ET.parse(svg).getroot().find('{http://www.w3.org/2000/svg}polygon')
                self.assertEqual(polygon.get('fill'),state.color if filled else 'none')
                self.assertEqual(float(polygon.get('opacity')),.5)


class ConfigTests(unittest.TestCase):
    def test_legacy_migration_preserves_dimensions_anchor(self):
        old={'chieu_cao':970,'chieu_rong':970,'dong_bo':True,'anchor_x':706,'anchor_y':897,'opacity':1.}
        new=normalize_payload(old)
        self.assertEqual(new['state']['width'],970)
        self.assertEqual(new['anchor'],[706,897])
        self.assertTrue(new['state']['sync'])
        self.assertEqual(new['state']['color'],'#008000')

    def test_legacy_minimum_opacity_upgrades(self):
        self.assertEqual(normalize_payload({'chieu_cao':200,'opacity':.1})['state']['opacity'],.15)

    def test_atomic_roundtrip_and_unicode_presets(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'nested'/'settings.json'
            store=ConfigStore(path,Path(folder)/'absent.json')
            data=store.load()
            data['presets']['Mẫu của Nguyễn']=TriangleState(width=120).to_dict()
            store.save(data)
            self.assertEqual(store.load(),data)
            self.assertEqual(list(path.parent.glob('*.tmp')),[])

    def test_invalid_file_falls_back_and_keeps_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'settings.json'
            path.write_text('{bad json',encoding='utf-8')
            store=ConfigStore(path,Path(folder)/'absent.json')
            self.assertEqual(store.load()['state'],TriangleState().to_dict())
            self.assertTrue(store.warning)
            store.save(normalize_payload({}))
            self.assertEqual(path.with_name('settings.json.invalid.bak').read_text(),'{bad json')

    def test_bad_import_does_not_overwrite_valid_config(self):
        with tempfile.TemporaryDirectory() as folder:
            store=ConfigStore(Path(folder)/'s.json',Path(folder)/'none')
            original=normalize_payload({})
            store.save(original)
            for bad in ({'version':99},{'anchor':[1,'x']},{'presets':{'bad':{'width':-1}}},[]):
                with self.subTest(bad=bad),self.assertRaises((ValueError,TypeError)):
                    store.save(bad)
                self.assertEqual(store.load(),original)


if __name__=='__main__':
    unittest.main()

"""Offline checks of UI refactoring boundaries without requiring Flet installation.

Usage: python tools/check_ui_structure.py
Does not validate rendering or Flet runtime compatibility.
"""
import ast
import importlib
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def structural_checks():
    ui_modules = list((ROOT / 'ui').rglob('*.py'))
    assert len(ui_modules) >= 40, 'UI modules unexpectedly missing'
    for file in [*ui_modules, ROOT/'main.py', ROOT/'app/bootstrap.py']:
        ast.parse(file.read_text(encoding='utf-8'),filename=str(file))

    # Every mixin method must exist in the public coordinator's inheritance chain.
    main_ast = ast.parse((ROOT/'ui/views/main_view.py').read_text(encoding='utf-8'))
    main_cls = next(n for n in main_ast.body if isinstance(n, ast.ClassDef) and n.name == 'MainView')
    required_bases = {'NavigationMixin', 'QuoteSheetMixin', 'QuoteHistoryMixin',
                      'QuoteListingMixin', 'QuoteDetailMixin', 'InventoryScreenMixin',
                      'SummaryScreenMixin', 'EstimateActionsMixin'}
    assert required_bases <= {n.id for n in main_cls.bases if isinstance(n,ast.Name)}

    # Public compatibility shims protect older imports.
    for path, name in [('ui/components/input_panel.py','InputPanel'),
                       ('ui/views/auth_login_view.py','AuthLoginView'),
                       ('ui/views/profile_view.py','ProfileView'),
                       ('ui/views/brand_loading_view.py','BrandLoadingView')]:
        data = (ROOT/path).read_text(encoding='utf-8')
        assert f'import {name}' in data

    # No old monolithic API imports; network requests are isolated from UI.
    assert not (ROOT/'api').exists(), 'Removed legacy API folder has reappeared'
    assert not any('import httpx' in p.read_text(encoding='utf-8')
                   for p in (ROOT/'ui').rglob('*.py'))
    assert not any('from api' in p.read_text(encoding='utf-8')
                   for p in (ROOT/'ui').rglob('*.py'))
    assert (ROOT/'app/fastbusiness/client.py').exists()

    req = (ROOT/'requirements.txt').read_text(encoding='utf-8')
    assert 'flet==1.1.2' in req
    return len(ui_modules)


def import_smoke_check():
    # Import class definitions without starting Flutter or creating controls.
    # This does not emulate Flet or test actual UI instantiation.
    class Names:
        def __getattr__(self, name):
            return name
    class FletStub(ModuleType):
        def __getattr__(self, name):
            return type(name, (), {})
    fake = FletStub('flet')
    fake.Page = type('Page', (), {})
    fake.Container = type('Container', (), {})
    fake.Icons = Names()
    fake.Colors = Names()
    fake.dropdown = Names()
    original = sys.modules.get('flet')
    try:
        sys.modules['flet'] = fake
        main = importlib.import_module('ui.views.main_view').MainView
        form = importlib.import_module('ui.components.input_panel').InputPanel
        login = importlib.import_module('ui.views.auth_login_view').AuthLoginView
        loading = importlib.import_module('ui.views.brand_loading_view').BrandLoadingView
        profile = importlib.import_module('ui.views.profile_view').ProfileView
        assert all(callable(getattr(main, name, None)) for name in (
            'open_history','open_profile','_open_selected_summary_sheet',
            '_build_inventory_view','_build_summary_view','_build_list_view',
            '_build_detail_view','recalculate','reset'))
        assert all(callable(getattr(form, name, None)) for name in (
            '_build_layout','_init_module_options','get_values','set_values','_field_style'))
        assert callable(login._handle_login)
        assert callable(loading.start)
        assert callable(profile._handle_save_profile)
    finally:
        if original is not None:
            sys.modules['flet'] = original
        else:
            sys.modules.pop('flet',None)


if __name__=='__main__':
    count=structural_checks()
    import_smoke_check()
    print(f'PASS: syntax, {count} UI modules, import graph, public methods, version pin.')
    print('NOTE: Rendering and runtime Flet 1.1.2 still require an installed Flet environment.')

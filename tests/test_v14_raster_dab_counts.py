import ast, pathlib, numpy as np

def load_dab(path):
    src = pathlib.Path(path).read_text()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'dab':
            start, end = node.lineno - 1, node.end_lineno
            return '\n'.join(src.splitlines()[start:end])
    raise RuntimeError('dab not found')

def test_dab():
    n = 12
    xs = np.linspace(-18, 18, n)
    ys = np.linspace(-18, 18, n)
    zs = np.linspace(-1, 50, n)
    field = np.zeros((n, n, n), np.float32)
    ns = {'np': np, 'n': n, 'xs': xs, 'ys': ys, 'zs': zs,
          'field': field, 'raster_points': 0,
          'raster_attempted': 0, 'raster_skipped': 0}
    exec(load_dab('experiments/sdf-exterior-2026-11-22/build_v14_nonperiodic_tears.py'), ns)
    dab = ns['dab']
    init = field.copy()
    dab([0.0, 0.0, 10.0], 100.0, 3.0)
    assert not np.array_equal(field, init)
    for q in ([100.0, 100.0, 100.0], [-100.0, -100.0, -100.0],
              [0.0, 0.0, -5.0], [0.0, 0.0, 60.0]):
        before = field.copy()
        prev = ns['raster_attempted']
        dab(q, 100.0, 3.0)
        assert np.array_equal(field, before)
        assert ns['raster_attempted'] == prev + 1
    assert ns['raster_attempted'] == ns['raster_points'] + ns['raster_skipped']

if __name__ == '__main__':
    test_dab()

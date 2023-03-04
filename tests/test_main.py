"""Test the __main__ module."""

import unittest.mock as mock

import pytest

from data_morph import __main__
from data_morph.data.dataset import Dataset


def test_main_bad_shape():
    """Test that invalid target shapes raise a ValueError."""
    with pytest.raises(ValueError, match='No valid target shapes were provided.'):
        __main__.main(['dino', '--target-shape=does-not-exist'])


@pytest.mark.bad_input_to_argparse
@pytest.mark.parametrize(
    ['decimals', 'reason'],
    [
        (-1, 'invalid choice'),
        (0.5, 'invalid int value'),
        (10, 'invalid choice'),
        ('s', 'invalid int value'),
    ],
)
def test_main_bad_input_decimals(decimals, reason, capsys):
    """Test that invalid input for decimals is handled correctly."""
    with pytest.raises(SystemExit):
        __main__.main(['dino', f'--decimals={decimals}'])
    assert f'error: argument --decimals: {reason}:' in capsys.readouterr().err


@pytest.mark.bad_input_to_argparse
@pytest.mark.parametrize('value', [True, False, 0.1, 's'])
@pytest.mark.parametrize('field', ['iterations', 'freeze', 'seed'])
def test_main_bad_input_integers(field, value, capsys):
    """Test that invalid input for integers is handled correctly."""
    with pytest.raises(SystemExit):
        __main__.main(['dino', f'--{field}={value}'])
    assert f'error: argument --{field}: invalid int value:' in capsys.readouterr().err


@pytest.mark.bad_input_to_argparse
@pytest.mark.parametrize('value', [1, 0, 's', -1, 0.5, True, False])
@pytest.mark.parametrize(
    'field', ['ramp-in', 'ramp-out', 'forward-only', 'keep-frames']
)
def test_main_bad_input_boolean(field, value, capsys):
    """Test that invalid input for Boolean switches are handled correctly."""
    with pytest.raises(SystemExit):
        __main__.main(['dino', f'--{field}={value}'])
    assert (
        f'error: argument --{field}: ignored explicit argument'
        in capsys.readouterr().err
    )


@pytest.mark.bad_input_to_argparse
@pytest.mark.parametrize(
    ['bounds', 'reason'],
    [
        (['-1'], 'expected 2 arguments'),
        (['10', 's'], 'invalid float value'),
    ],
)
def test_main_bad_input_bounds(bounds, reason, capsys):
    """Test that invalid input for bounds is handled correctly."""
    with pytest.raises(SystemExit):
        __main__.main(['--bounds', *bounds, '--', 'dino'])
    assert f'error: argument --bounds: {reason}' in capsys.readouterr().err


@pytest.mark.bad_input_to_argparse
@pytest.mark.parametrize(
    ['bounds', 'reason'],
    [
        (['-1'], 'expected 4 arguments'),
        (['10', '90', '300', 's'], 'invalid float value'),
    ],
)
def test_main_bad_input_xy_bounds(bounds, reason, capsys):
    """Test that invalid input for xy_bounds is handled correctly."""
    with pytest.raises(SystemExit):
        __main__.main(['--xy-bounds', *bounds, '--', 'dino'])
    assert f'error: argument --xy-bounds: {reason}' in capsys.readouterr().err


def test_main_mutually_exclusive_bounds(capsys):
    """Test that bounds options are mutually exclusive."""
    with pytest.raises(SystemExit):
        __main__.main(['--bounds', '10', '90', '--xy-bounds', '10', '90', '300', '380', '--', 'dino'])
    assert 'error: argument --xy-bounds: not allowed with argument --bounds' in capsys.readouterr().err


@pytest.mark.parametrize(
    ['start_shape', 'bounds'],
    [['dino', [10, 100]], ['dino', [10, 100, 200, 290]], ['dino', None]],
)
def test_main_dataloader(start_shape, bounds, mocker):
    """Check that the DataLoader is being used correctly."""

    if bounds is None or len(bounds) == 2:
        arg = '--bounds'
        x_bounds = y_bounds = bounds
    else:
        arg = '--xy-bounds'
        x_bounds = bounds[:2]
        y_bounds = bounds[2:]
    bound_args = [arg, *[str(value) for value in bounds]] if bounds else []

    load = mocker.patch.object(__main__.DataLoader, 'load_dataset', autospec=True)
    _ = mocker.patch.object(__main__.DataMorpher, 'morph')
    argv = [
        start_shape,
        '--target-shape=circle',
        *bound_args,
    ]
    __main__.main([arg for arg in argv if arg])
    load.assert_called_once_with(start_shape, x_bounds=x_bounds, y_bounds=y_bounds)


@pytest.mark.parametrize('flag', [True, False])
def test_main_one_shape(flag, mocker, tmp_path):
    """Check that the proper values are passed to morph a single shape."""
    init_args = {
        'decimals': 3 if flag else None,
        'seed': 1,
        'output_dir': tmp_path,
        'write_data': flag,
        'keep_frames': flag,
        'ramp_in': flag,
        'ramp_out': flag,
        'forward_only_animation': flag,
        'freeze': 3 if flag else None,
        'num_frames': 100,
        'in_notebook': False,
    }
    morph_args = {
        'start_shape_name': 'dino',
        'target_shape': 'circle',
        'iterations': 1000,
    }

    @mock.create_autospec
    def morph_value_check(morpher, **kwargs):
        """Replace the morph() method; first arg is the DataMorpher object."""
        # check how the DataMorpher object was created
        for arg, value in init_args.items():
            assert getattr(morpher, arg) == value

        # check the values passed to morph()
        for arg, value in morph_args.items():
            if arg == 'target_shape':
                assert str(kwargs[arg]) == value
            elif arg == 'start_shape':
                assert isinstance(value, Dataset)
            else:
                assert kwargs[arg] == value

    mocker.patch.object(__main__.DataMorpher, 'morph', morph_value_check)
    argv = [
        morph_args['start_shape_name'],
        f'--target-shape={morph_args["target_shape"]}',
        f'--iterations={morph_args["iterations"]}',
        f'--decimals={init_args["decimals"]}' if init_args['decimals'] else '',
        f'--freeze={init_args["freeze"]}' if init_args['freeze'] else '',
        f'--seed={init_args["seed"]}',
        f'--output-dir={init_args["output_dir"]}',
        '--write-data' if init_args['write_data'] else '',
        '--keep-frames' if init_args['keep_frames'] else '',
        '--ramp-in' if init_args['ramp_in'] else '',
        '--ramp-out' if init_args['ramp_out'] else '',
        '--forward-only' if init_args['forward_only_animation'] else '',
    ]
    __main__.main([arg for arg in argv if arg])
    morph_value_check.assert_called_once()


@pytest.mark.parametrize(
    ['target_shape', 'patched_options'],
    [
        (['star', 'bullseye'], None),
        (None, ['dots', 'x']),
    ],
    ids=['two shapes', 'all shapes'],
)
def test_main_multiple_shapes(
    target_shape, patched_options, monkeypatch, mocker, capsys
):
    """Check that multiple morphing is working."""
    start_shape_name = 'dino'

    if patched_options:
        monkeypatch.setattr(
            __main__.ShapeFactory,
            'AVAILABLE_SHAPES',
            {
                shape: cls
                for shape, cls in __main__.ShapeFactory.AVAILABLE_SHAPES.items()
                if shape in patched_options
            },
        )

    shapes = (
        target_shape if target_shape else __main__.ShapeFactory.AVAILABLE_SHAPES.keys()
    )

    shapes_completed = []

    @mock.create_autospec
    def mock_morph(_, **kwargs):
        """Mock the DataMorpher.morph() method to check input and track progress."""
        assert isinstance(kwargs['start_shape'], Dataset)
        assert kwargs['start_shape'].name == start_shape_name
        shapes_completed.append(str(kwargs['target_shape']))

    mocker.patch.object(__main__.DataMorpher, 'morph', mock_morph)
    __main__.main(
        [start_shape_name, *(['--target-shape', *target_shape] if target_shape else [])]
    )
    assert mock_morph.call_count == len(shapes)
    assert set(shapes_completed).difference(shapes) == set()
    assert (
        ''.join(
            [f'Morphing shape {i + 1} of {len(shapes)}\n' for i in range(len(shapes))]
        )
        == capsys.readouterr().err
    )

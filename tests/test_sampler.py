from unittest import TestCase
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest

from sdv.sampler import Sampler


class TestSampler(TestCase):

    def test___init__default(self):
        """Test create a default instance of Sampler class"""
        # Run
        sampler = Sampler(None, None)

        # Asserts
        assert sampler.primary_key == dict()
        assert sampler.remaining_primary_key == dict()

    def test__square_matrix(self):
        """Test fill zeros a triangular matrix"""
        # Run
        matrix = [[0.1, 0.5], [0.3]]

        result = Sampler._square_matrix(matrix)

        # Asserts
        expect = [[0.1, 0.5], [0.3, 0.0]]

        assert result == expect

    def test__prepare_sampler_covariance(self):
        """Test prepare_sampler_covariante"""
        # Run
        sampler = Mock()
        sampler._square_matrix.return_value = [[0.4, 0.1], [0.1, 0.0]]
        covariance = [[0.4, 0.1], [0.1]]

        result = Sampler._prepare_sampled_covariance(sampler, covariance)

        # Asserts
        expect = np.array([[0.4, 0.2], [0.2, 0.0]])

        np.testing.assert_equal(result, expect)

    @patch('exrex.getone')
    def test__fill_test_columns(self, mock_exrex):
        """Test fill text columns"""
        # Setup
        mock_exrex.side_effect = ['fake id 1', 'fake id 2']

        metadata_field_meta = [
            {'type': 'id', 'ref': {'table': 'ref_table', 'field': 'ref_field'}},
            {'type': 'id', 'regex': '^[0-9]{10}$'},
            {'type': 'text', 'regex': '^[0-9]{10}$'}
        ]

        sample_rows = {'ref_field': 'some value'}

        # Run
        sampler = Mock()
        sampler.metadata.get_field_meta.side_effect = metadata_field_meta
        sampler.sample_rows.return_value = sample_rows

        data = pd.DataFrame({'tar': ['a', 'b', 'c']})
        columns = ['foo', 'bar', 'tar']
        table_name = 'test'

        result = Sampler._fill_text_columns(sampler, data, columns, table_name)

        # Asserts
        expect = pd.DataFrame({
            'foo': ['some value', 'some value', 'some value'],
            'bar': ['fake id 1', 'fake id 1', 'fake id 1'],
            'tar': ['fake id 2', 'fake id 2', 'fake id 2'],
        })

        pd.testing.assert_frame_equal(result.sort_index(axis=1), expect.sort_index(axis=1))

    def test__reset_primary_keys_generators(self):
        """Test reset values"""
        # Run
        sampler = Mock()
        sampler.primary_key = 'something'
        sampler.remaining_primary_key = 'else'

        Sampler._reset_primary_keys_generators(sampler)

        # Asserts
        assert sampler.primary_key == dict()
        assert sampler.remaining_primary_key == dict()

    def test__transform_synthesized_rows(self):
        """Test transform synthesized rows"""
        # Setup
        metadata_field_names = ['foo', 'bar']
        metadata_reverse_transform = pd.DataFrame({'foo': [0, 1], 'bar': [2, 3], 'tar': [4, 5]})

        # Run
        sampler = Mock()
        sampler.metadata.get_field_names.return_value = metadata_field_names
        sampler.metadata.reverse_transform.return_value = metadata_reverse_transform
        synthesized = None
        table_name = 'test'

        result = Sampler._transform_synthesized_rows(sampler, synthesized, table_name)

        # Asserts
        expect = pd.DataFrame({'foo': [0, 1], 'bar': [2, 3]})

        pd.testing.assert_frame_equal(result.sort_index(axis=1), expect.sort_index(axis=1))

    def test__get_primary_keys_none(self):
        """Test returns a tuple of none when a table doesn't have a primary key"""
        # Run
        sampler = Mock()
        sampler.metadata.get_primary_key.return_value = None

        table_name = 'test'
        num_rows = 5

        result = Sampler._get_primary_keys(sampler, table_name, num_rows)

        # Asserts
        expect = (None, None)
        assert result == expect

    def test__get_primary_keys_raise_value_error(self):
        """Test a ValueError is raised trying to get the primary keys"""
        # Setup
        metadata_primary_key = 'pk'
        metadata_field_meta = {'regex': '^[0-9]{10}$'}
        primary_key = {'test': 'pk'}
        remaining_primary_key = {'test': 4}

        # Run & asserts
        sampler = Mock()
        sampler.metadata.get_primary_key.return_value = metadata_primary_key
        sampler.metadata.get_field_meta.return_value = metadata_field_meta
        sampler.primary_key = primary_key
        sampler.remaining_primary_key = remaining_primary_key

        table_name = 'test'
        num_rows = 5

        with pytest.raises(ValueError):
            Sampler._get_primary_keys(sampler, table_name, num_rows)

    @patch('exrex.count')
    @patch('exrex.generate')
    def test__get_primary_keys_with_values(self, mock_exrex_generate, mock_exrex_count):
        """Test return a tuple with a string and a pandas.Series"""
        # Setup
        metadata_primary_key = 'pk'
        metadata_field_meta = {
            'regex': '^[0-9]{10}$',
            'type': 'number',
            'subtype': 'integer'
        }
        primary_key = {}
        remaining_primary_key = {}

        mock_exrex_count.return_value = 7
        mock_exrex_generate.return_value = [11, 22, 33, 44, 55]

        # Run & asserts
        sampler = Mock()
        sampler.metadata.get_primary_key.return_value = metadata_primary_key
        sampler.metadata.get_field_meta.return_value = metadata_field_meta
        sampler.primary_key = primary_key
        sampler.remaining_primary_key = remaining_primary_key

        table_name = 'test'
        num_rows = 5

        result = Sampler._get_primary_keys(sampler, table_name, num_rows)

        # Asserts
        expect = ('pk', pd.Series([11, 22, 33, 44, 55]))

        assert result[0] == expect[0]
        pd.testing.assert_series_equal(result[1], expect[1])

    def test__setdefault_key_in_dict(self):
        """Test setdefault with key in dict"""
        # Run
        a_dict = {'foo': 'bar'}
        key = 'foo'
        a_type = None

        result = Sampler._setdefault(a_dict, key, a_type)

        # Asserts
        expect = 'bar'

        assert result == expect

    def test__setdefault_key_not_in_dict(self):
        """Test setdefault with key not in dict"""
        # Run
        a_dict = {}
        key = 'foo'
        a_type = int

        result = Sampler._setdefault(a_dict, key, a_type)

        # Asserts
        expect = 0

        assert result == expect

    def test__key_order(self):
        """Test key order"""
        # Run
        key_value = ['foo__0__1']

        result = Sampler._key_order(key_value)

        # Asserts
        expect = ['foo', 0, 1]

        assert result == expect

    def test__unflatten_dict_raises_error_row_index(self):
        """Test unflatten dict raises error row_index"""
        # Setup
        setdefault = [1, 2, 3, 4, 5]

        # Run & asserts
        sampler = Mock()
        sampler._key_order = None
        sampler._setdefault.return_value = setdefault

        flat = {
            'foo__0__1': 'some value'
        }

        with pytest.raises(ValueError):
            Sampler._unflatten_dict(sampler, flat)

    def test__unflatten_dict_raises_error_column_index(self):
        """Test unflatten dict raises error column_index"""
        # Setup
        setdefault = []

        # Run & asserts
        sampler = Mock()
        sampler._key_order = None
        sampler._setdefault.return_value = setdefault

        flat = {
            'foo__0__1': 'some value'
        }

        with pytest.raises(ValueError):
            Sampler._unflatten_dict(sampler, flat)

    def test__unflatten_dict_no_error(self):
        """Test unflatten dict doesn't raise an error and return unflatten data"""
        # Setup
        setdefault = [
            [[], [1]],  # bar__1__1
            [{}], {}  # foo__0__foo
        ]

        # Run
        sampler = Mock()
        sampler._key_order = None
        sampler._setdefault.side_effect = setdefault

        flat = {
            'foo__0__foo': 'some value',
            'bar__1__1': 'some value',
            'tar': 'some value'
        }

        result = Sampler._unflatten_dict(sampler, flat)

        # Asserts
        expect = {'tar': 'some value'}

        assert result == expect

    def test__make_positive_definite(self):
        """Test find the nearest positive-definite matrix"""
        # Run
        sampler = Mock()
        sampler._check_matrix_symmetric_positive_definite.return_value = True

        matrix = np.array([[0, 1], [1, 0]])

        result = Sampler._make_positive_definite(sampler, matrix)

        # Asserts
        expect = np.array([[0.5, 0.5], [0.5, 0.5]])

        np.testing.assert_equal(result, expect)
        assert sampler._check_matrix_symmetric_positive_definite.call_count == 1

    def test__make_positive_definite_iterate(self):
        """Test find the nearest positive-definite matrix iterating"""
        # Setup
        check_matrix = [False, False, True]
        # Run
        sampler = Mock()
        sampler._check_matrix_symmetric_positive_definite.side_effect = check_matrix

        matrix = np.array([[-1, -5], [-3, -7]])

        result = Sampler._make_positive_definite(sampler, matrix)

        # Asserts
        expect = np.array([[0.8, -0.4], [-0.4, 0.2]])

        np.testing.assert_array_almost_equal(result, expect)
        assert sampler._check_matrix_symmetric_positive_definite.call_count == 3

    def test__check_matrix_symmetric_positive_definite_shape_error(self):
        """Test check matrix shape error"""
        # Run
        sampler = Mock()
        matrix = np.array([])

        result = Sampler._check_matrix_symmetric_positive_definite(sampler, matrix)

        # Asserts
        expect = False

        assert result is expect

    def test__check_matrix_symmetric_positive_definite_np_error(self):
        """Test check matrix numpy raise error"""
        # Run
        sampler = Mock()
        matrix = np.array([[-1, 0], [0, 0]])

        result = Sampler._check_matrix_symmetric_positive_definite(sampler, matrix)

        # Asserts
        expect = False

        assert result is expect

    def test__check_matrix_symmetric_positive_definite(self):
        """Test check matrix numpy"""
        # Run
        sampler = Mock()
        matrix = np.array([[0.5, 0.5], [0.5, 0.5]])

        result = Sampler._check_matrix_symmetric_positive_definite(sampler, matrix)

        # Asserts
        expect = True

        assert result is expect

    def test__unflatten_gaussian_copula(self):
        """Test unflatte gaussian copula"""
        # Setup
        model_kwargs = {
            'distribution': 'Gaussian'
        }
        sampled_covariance = None
        check_matrix = False
        make_positive = np.array([[0.5, 0.5], [0.5, 0.5]])

        # Run
        sampler = Mock()
        sampler.modeler.model_kwargs = model_kwargs
        sampler._prepare_sampled_covariance.return_value = sampled_covariance
        sampler._check_matrix_symmetric_positive_definite.return_value = check_matrix
        sampler._make_positive_definite.return_value = make_positive

        model_parameters = {
            'distribs': {
                'foo': {'std': 0.5}
            },
            'covariance': None
        }

        result = Sampler._unflatten_gaussian_copula(sampler, model_parameters)

        # Asserts
        expect = {
            'distribs': {
                'foo': {
                    'fitted': True,
                    'std': 1.6487212707001282,
                    'type': 'Gaussian'
                }
            },
            'distribution': 'Gaussian',
            'covariance': [[0.5, 0.5], [0.5, 0.5]]
        }

        assert result == expect

    def test__get_extension(self):
        """Test get extension"""
        # Run
        sampler = Mock()

        parent_row = pd.Series([[0, 1], [1, 0]], index=['__foo__field', '__foo__field2'])
        table_name = 'foo'
        parent_name = 'bar'

        result = Sampler._get_extension(sampler, parent_row, table_name, parent_name)

        # Asserts
        expect = {'field': [0, 1], 'field2': [1, 0]}

        assert result == expect

    @patch('sdv.sampler.get_qualified_name')
    def test__get_model(self, mock_qualified_name):
        """Test get model"""
        # Setup
        unflatten_dict = {'unflatten': 'dict'}
        unflatten_gaussian = {'unflatten': 'gaussian'}

        mock_qualified_name.return_value = 'copulas.multivariate.gaussian.GaussianMultivariate'

        # Run
        sampler = Mock()
        sampler._unflatten_dict.return_value = unflatten_dict
        sampler._unflatten_gaussian_copula.return_value = unflatten_gaussian

        extension = {'extension': 'dict'}

        Sampler._get_model(sampler, extension)

        # Asserts
        expect_unflatten_dict_call = {'extension': 'dict'}
        expect_qualified_name_call_count = 1
        expect_unflatten_gaussian_call = {
            'unflatten': 'dict',
            'fitted': True,
            'type': 'copulas.multivariate.gaussian.GaussianMultivariate'
        }
        expect_from_dict_call = {'unflatten': 'gaussian'}

        sampler._unflatten_dict.assert_called_once_with(expect_unflatten_dict_call)
        assert mock_qualified_name.call_count == expect_qualified_name_call_count
        sampler._unflatten_gaussian_copula.assert_called_once_with(expect_unflatten_gaussian_call)
        sampler.modeler.model.from_dict.assert_called_once_with(expect_from_dict_call)

    def test__sample_rows(self):
        """Test sample rows from model"""
        # Setup
        primary_keys = ('pk', [1, 2, 3, 4])
        model_sample = dict()

        # Run
        sampler = Mock()
        sampler._get_primary_keys.return_value = primary_keys

        model = Mock()
        model.sample.return_value = model_sample
        num_rows = 5
        table_name = 'test'

        result = Sampler._sample_rows(sampler, model, num_rows, table_name)

        # Asserts
        expect = {'pk': [1, 2, 3, 4]}

        assert result == expect
        sampler._get_primary_keys.assert_called_once_with('test', 5)
        model.sample.called_once_with(5)

    def test__sample_children(self):
        """Test sample children"""
        # Setup
        metadata_children = ['child A', 'child B', 'child C']

        # Run
        sampler = Mock()
        sampler.metadata.get_children.return_value = metadata_children

        table_name = 'test'
        sampled = {
            'test': pd.DataFrame({'field': [11, 22, 33]})
        }

        Sampler._sample_children(sampler, table_name, sampled)

        # Asserts
        expect_sample_table_call_args = [
            ['child A', 'test', pd.Series([11], index=['field'], name=0), sampled],
            ['child A', 'test', pd.Series([22], index=['field'], name=1), sampled],
            ['child A', 'test', pd.Series([33], index=['field'], name=2), sampled],
            ['child B', 'test', pd.Series([11], index=['field'], name=0), sampled],
            ['child B', 'test', pd.Series([22], index=['field'], name=1), sampled],
            ['child B', 'test', pd.Series([33], index=['field'], name=2), sampled],
            ['child C', 'test', pd.Series([11], index=['field'], name=0), sampled],
            ['child C', 'test', pd.Series([22], index=['field'], name=1), sampled],
            ['child C', 'test', pd.Series([33], index=['field'], name=2), sampled],
        ]

        sampler.metadata.get_children.assert_called_once_with('test')

        for result_call, expect_call in zip(
                sampler._sample_table.call_args_list, expect_sample_table_call_args):
            assert result_call[0][0] == expect_call[0]
            assert result_call[0][1] == expect_call[1]
            assert result_call[0][3] == expect_call[3]
            pd.testing.assert_series_equal(result_call[0][2], expect_call[2])

    def test__sample_table_sampled_tablename_none(self):
        """Test sample table with sampled table_name None"""
        # Setup
        get_extension = {
            'child_rows': 5
        }

        get_model = dict()

        sample_rows = dict()
        metadata_foreign_keys = {('test', 'test_parent'): ('parent_id', 'foreign_key')}

        # Run
        sampler = Mock()
        sampler._get_extension.return_value = get_extension
        sampler._get_model.return_value = get_model
        sampler._sample_rows.return_value = sample_rows
        sampler.metadata.foreign_keys = metadata_foreign_keys

        table_name = 'test'
        parent_name = 'test_parent'
        parent_row = {'parent_id': 'value parent id'}
        sampled = dict()

        Sampler._sample_table(sampler, table_name, parent_name, parent_row, sampled)

        # Asserts
        sampler._sample_rows.assert_called_once_with(dict(), 5, 'test')
        sampler._sample_children.assert_called_once_with(
            'test', {'test': {'foreign_key': 'value parent id'}}
        )

    def test__sample_table_sampled_tablename_not_none(self):
        """Test sample table with sampled table_name not None"""
        # Setup
        get_extension = {
            'child_rows': 5
        }

        get_model = dict()

        sample_rows = pd.Series()
        metadata_foreign_keys = {('test', 'test_parent'): ('parent_id', 'foreign_key')}

        # Run
        sampler = Mock()
        sampler._get_extension.return_value = get_extension
        sampler._get_model.return_value = get_model
        sampler._sample_rows.return_value = sample_rows
        sampler.metadata.foreign_keys = metadata_foreign_keys

        table_name = 'test'
        parent_name = 'test_parent'
        parent_row = {'parent_id': 69}
        sampled = {'test': pd.Series([9, 8, 7])}

        Sampler._sample_table(sampler, table_name, parent_name, parent_row, sampled)

        # Asserts
        sampler._sample_rows.assert_called_once_with(dict(), 5, 'test')
        assert sampler._sample_children.call_count == 1
        assert sampler._sample_children.call_args_list[0][0][0] == 'test'

        pd.testing.assert_series_equal(
            sampler._sample_children.call_args_list[0][0][1]['test'],
            pd.Series([9, 8, 7, 69])
        )

    def test_sample_table(self):
        """Test sample table"""
        # Run
        sampler = Mock()
        table_name = 'test'

        result = Sampler.sample_table(sampler, table_name)

        # Asserts
        sampler.sample_rows.assert_called_once_with(
            'test', 5, sample_children=False, reset_primary_keys=False)

        assert result == sampler.sample_rows.return_value

    def test_sample_all(self):
        """Test sample all regenerating the primary keys"""
        # Setup
        def sample_rows_side_effect(table, num_rows, sampled_data):
            sampled_data[table] = pd.DataFrame({'foo': range(num_rows)})

        metadata_parents_side_effect = [False, True, False]

        metadata_table_names = ['table a', 'table b', 'table c']

        # Run
        sampler = Mock()
        sampler.metadata.get_table_names.return_value = metadata_table_names
        sampler.metadata.get_parents.side_effect = metadata_parents_side_effect
        sampler.sample_rows.side_effect = sample_rows_side_effect

        num_rows = 3
        reset_primary_keys = True

        result = Sampler.sample_all(
            sampler, num_rows=num_rows, reset_primary_keys=reset_primary_keys)

        # Asserts
        assert sampler.metadata.get_parents.call_count == 3
        assert sampler._reset_primary_keys_generators.call_count == 1
        pd.testing.assert_frame_equal(result['table a'], pd.DataFrame({'foo': range(num_rows)}))
        pd.testing.assert_frame_equal(result['table c'], pd.DataFrame({'foo': range(num_rows)}))

    @pytest.mark.skip(reason="WIP, make the result deterministic")
    def test_sample_rows_with_parents(self):
        """Test sample rows with parents"""
        # Setup
        models = {
            'test': 'Model'
        }

        metadata_get_parents = {'parent a', 'parent b'}

        metadata_foreign_key = {
            ('test', 'parent a'): (None, 'foreign_a'),
            ('test', 'parent b'): (None, 'foreign_b')
        }

        primary_keys = [None, [1]]

        sample_rows = dict()

        # Run
        sampler = Mock()
        sampler.modeler.models = models
        sampler.metadata.get_parents.return_value = metadata_get_parents
        sampler.metadata.foreign_keys = metadata_foreign_key
        sampler._sample_rows.return_value = sample_rows
        sampler._get_primary_keys.return_value = primary_keys

        table_name = 'test'
        num_rows = 5
        reset_primary_keys = True
        sample_children = True
        sampled_data = None

        Sampler.sample_rows(
            sampler,
            table_name,
            num_rows,
            reset_primary_keys=reset_primary_keys,
            sample_children=sample_children,
            sampled_data=sampled_data
        )

        # Asserts
        assert sampler._reset_primary_keys_generators.call_count == 1
        sampler._sample_rows.assert_called_once_with('Model', 5, 'test')
        sampler.metadata.get_parents.assert_called_once_with('test')
        sampler._get_primary_keys.assert_called_once_with('parent b', 1)
        sampler._transform_synthesized_rows.call_count == 2

    def test_sample_rows_no_sample_children(self):
        """Test sample_rows no sample children"""
        # Setup
        models = {'test': 'model'}

        # Run
        sampler = Mock()
        sampler.modeler.models = models
        sampler.metadata.get_parents.return_value = None

        table_name = 'test'
        num_rows = 5
        sample_children = False

        Sampler.sample_rows(sampler, table_name, num_rows, sample_children=sample_children)

        # Asserts

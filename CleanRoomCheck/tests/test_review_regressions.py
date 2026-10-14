import unittest
from tests.helpers import base_model, fact
from cleanroomcheck.model import validate_model, ModelError
from cleanroomcheck.io import parse_json

class ReviewRegressionTests(unittest.TestCase):
    def test_enormous_integer_is_a_model_error_not_an_overflow(self):
        for field in ['retention_days','rto_hours']:
            with self.subTest(field=field):
                with self.assertRaises(ModelError):
                    validate_model(fact(base_model(), field, 10**400))

    def test_json_integer_decoder_limit_is_normalized(self):
        with self.assertRaises(ModelError):
            parse_json('{"n":'+('9'*5000)+'}')

    def test_unpaired_surrogate_in_label_is_rejected_before_report(self):
        m=base_model();m['project']['name']='bad\ud800label'
        with self.assertRaises(ModelError):validate_model(m)

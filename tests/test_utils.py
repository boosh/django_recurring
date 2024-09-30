import unittest

from src.recurring.utils import (
    _camel_to_snake,
    recursive_camel_to_snake,
    _snake_to_camel,
    recursive_snake_to_camel,
)


class TestUtils(unittest.TestCase):
    def test_camel_to_snake(self):
        """Test the _camel_to_snake function"""
        self.assertEqual(_camel_to_snake("camelCase"), "camel_case")
        self.assertEqual(_camel_to_snake("ThisIsATest"), "this_is_a_test")
        self.assertEqual(_camel_to_snake("ABC"), "abc")
        self.assertEqual(_camel_to_snake("alreadySnakeCase"), "already_snake_case")
        self.assertEqual(_camel_to_snake(""), "")
        self.assertEqual(_camel_to_snake("with123Numbers"), "with123_numbers")

    def test_recursive_camel_to_snake(self):
        """Test the recursive_camel_to_snake function"""
        input_data = {
            "topLevel": {
                "secondLevel": {
                    "thirdLevelArray": [
                        {"fourthLevel": "value"},
                        {"anotherFourthLevel": "anotherValue"},
                    ]
                },
                "anotherSecondLevel": "value",
            },
            "topLevelArray": [
                {"nestedInArray": "value"},
                {"anotherNestedInArray": "anotherValue"},
            ],
        }
        expected_output = {
            "top_level": {
                "second_level": {
                    "third_level_array": [
                        {"fourth_level": "value"},
                        {"another_fourth_level": "anotherValue"},
                    ]
                },
                "another_second_level": "value",
            },
            "top_level_array": [
                {"nested_in_array": "value"},
                {"another_nested_in_array": "anotherValue"},
            ],
        }
        self.assertEqual(recursive_camel_to_snake(input_data), expected_output)

    def test_snake_to_camel(self):
        """Test the _snake_to_camel function"""
        self.assertEqual(_snake_to_camel("snake_case"), "snakeCase")
        self.assertEqual(_snake_to_camel("this_is_a_test"), "thisIsATest")
        self.assertEqual(_snake_to_camel("abc"), "abc")
        self.assertEqual(_snake_to_camel("already_camel_case"), "alreadyCamelCase")
        self.assertEqual(_snake_to_camel(""), "")
        self.assertEqual(_snake_to_camel("with_123_numbers"), "with123Numbers")

    def test_recursive_snake_to_camel(self):
        """Test the recursive_snake_to_camel function"""
        input_data = {
            "top_level": {
                "second_level": {
                    "third_level_array": [
                        {"fourth_level": "value"},
                        {"another_fourth_level": "another_value"},
                    ]
                },
                "another_second_level": "value",
            },
            "top_level_array": [
                {"nested_in_array": "value"},
                {"another_nested_in_array": "another_value"},
            ],
        }
        expected_output = {
            "topLevel": {
                "secondLevel": {
                    "thirdLevelArray": [
                        {"fourthLevel": "value"},
                        {"anotherFourthLevel": "another_value"},
                    ]
                },
                "anotherSecondLevel": "value",
            },
            "topLevelArray": [
                {"nestedInArray": "value"},
                {"anotherNestedInArray": "another_value"},
            ],
        }
        self.assertEqual(recursive_snake_to_camel(input_data), expected_output)

    def test_edge_cases(self):
        """Test edge cases for all functions"""
        # Empty input
        self.assertEqual(recursive_camel_to_snake({}), {})
        self.assertEqual(recursive_snake_to_camel({}), {})

        # Non-dict, non-list input
        self.assertEqual(recursive_camel_to_snake("notADict"), "notADict")
        self.assertEqual(recursive_snake_to_camel("not_a_dict"), "not_a_dict")

        # Mixed case input
        self.assertEqual(_camel_to_snake("mixedCASeInput"), "mixed_ca_se_input")
        self.assertEqual(_snake_to_camel("mixed_ca_se_input"), "mixedCaSeInput")

        # Single letter input
        self.assertEqual(_camel_to_snake("a"), "a")
        self.assertEqual(_snake_to_camel("a"), "a")

    def test_nested_structures(self):
        """Test nested structures with mixed types"""
        input_data = {
            "topLevel": [
                {"nestedDict": {"deeperKey": "value"}},
                ["listItem1", {"dictInList": "value"}],
                42,
                "stringValue",
            ]
        }
        expected_camel_to_snake = {
            "top_level": [
                {"nested_dict": {"deeper_key": "value"}},
                ["listItem1", {"dict_in_list": "value"}],
                42,
                "stringValue",
            ]
        }
        expected_snake_to_camel = {
            "topLevel": [
                {"nestedDict": {"deeperKey": "value"}},
                ["listItem1", {"dictInList": "value"}],
                42,
                "stringValue",
            ]
        }
        self.assertEqual(recursive_camel_to_snake(input_data), expected_camel_to_snake)
        self.assertEqual(
            recursive_snake_to_camel(expected_camel_to_snake), expected_snake_to_camel
        )


if __name__ == "__main__":
    unittest.main()

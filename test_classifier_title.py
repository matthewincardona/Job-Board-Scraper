import pandas as pd
import unittest
from utils.classifier import classify_and_filter_jobs

class TestClassifier(unittest.TestCase):

    def test_filter_jobs_by_title(self):
        # Create a sample DataFrame
        data = {
            'title': [
                'Senior Software Engineer',
                'Junior Developer',
                'Software Engineer',
                'Staff Engineer',
                'Lead Developer',
                'Intern',
                'Product Manager'
            ],
            'description': ['' for _ in range(7)]
        }
        df = pd.DataFrame(data)

        # Apply the filter
        filtered_df = classify_and_filter_jobs(df)

        # Expected titles to remain
        expected_titles = [
            'Junior Developer',
            'Software Engineer',
            'Intern'
        ]
        
        # Check that the filtered DataFrame contains only the expected titles
        self.assertListEqual(list(filtered_df['title']), expected_titles)
        self.assertEqual(len(filtered_df), 3)

if __name__ == '__main__':
    unittest.main()

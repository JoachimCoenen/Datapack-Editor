import os

colorSchemesPath = os.path.abspath(os.path.dirname(__file__) + '/../colorSchemes/scheme_*.py')
colorSchemesMinimizerPath = os.path.abspath(os.path.dirname(__file__) + '/../colorSchemes/minimizer.py')

datas = [
    (colorSchemesPath, 'base/model/colorSchemes/'),
    (colorSchemesMinimizerPath, 'base/model/colorSchemes/'),
]

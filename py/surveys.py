import pandas as pd

SURVEYS_PATH = "data/surveys_v5.xlsx"
DELIBERATIVE_CASES = "data/deliberative_cases.csv"


def get_survey_names(file_path=SURVEYS_PATH, no_template=False):
    xls = pd.ExcelFile(file_path)
    survey_names = xls.sheet_names
    if no_template:
        survey_names.remove("template")
    return survey_names


def get_surveys_data(file_path=SURVEYS_PATH, deliberative_cases=False):
    xls = pd.ExcelFile(file_path)
    sheets = {}
    sheet_names = xls.sheet_names

    if deliberative_cases:
        deliberative_cases = pd.read_csv(DELIBERATIVE_CASES)
        sheet_names = filter(
            lambda survey: survey in set(deliberative_cases["survey"]), sheet_names
        )

    for sheet_name in sheet_names:
        sheets[sheet_name] = pd.read_excel(xls, sheet_name)
    return sheets


def sort_statements(statements, order):

    if len(statements) != len(order):
        raise ValueError("The lengths of 'statements' and 'order' must be equal.")

    # Combine the statements and order lists into a list of tuples
    statement_order_pairs = list(zip(statements, order))

    # Sort the pairs based on the order values
    sorted_statement_order_pairs = sorted(statement_order_pairs, key=lambda x: x[1])

    # Separate the sorted statements from their corresponding order values
    sorted_statements = [x[0] for x in sorted_statement_order_pairs]

    return sorted_statements


def get_policies_and_considerations(sheet):

    policies = sheet["policies"].dropna().tolist()
    considerations = sheet["considerations"].dropna().tolist()

    policies_order = sheet["policies_order"].dropna().tolist()
    policies_order = [int(i) for i in policies_order]
    considerations_order = sheet["considerations_order"].dropna().tolist()
    considerations_order = [int(i) for i in considerations_order]

    # sort policies and considerations based on
    policies = sort_statements(policies, policies_order)
    considerations = sort_statements(considerations, considerations_order)

    # read optional params
    scale_max = sheet["scale_max"].dropna().tolist()
    q_method = sheet["q-method"].dropna().tolist()

    # print(scale_max)
    # print(q_)

    # convert to scale_max to value -- default: 10
    if len(scale_max) > 0:
        scale_max = int(scale_max[0])
    else:
        scale_max = 10

    # convert to q_methof to value -- default: False
    if len(q_method) > 0:
        q_method = bool(q_method[0])
    else:
        q_method = False

    return policies, considerations, scale_max, q_method

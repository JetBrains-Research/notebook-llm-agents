import os

from dotenv import load_dotenv

from src.router.proxy_agent import ProxyAgent

env = load_dotenv()


message = """Here's a Jupyter notebook. Totally notebook contains 9 cells. Note that cell starting enumerate from 0.  It uses `\n#%% --\n` as a separator between cells. #import libraries<line_sep>import pandas as pd<line_sep>import numpy as np<line_sep>#%% --<line_sep>#import dataset<line_sep>data = pd.read_csv('../Data/data_cleaned.csv')<line_sep>data.shape<line_sep>#%% --<line_sep># Seperate dependent and independent variable<line_sep>x = data.drop(['Survived'], axis = 1)<line_sep>y = data['Survived']<line_sep>#%% --<line_sep># import train_test_split<line_sep>from sklearn.model_selection import train_test_split<line_sep>#%% --<line_sep>train_x, test_x, train_y, test_y = train_test_split(x, y, random_state = 45)<line_sep>#%% --<line_sep>print(train_y.value_counts(normalize=True))<line_sep>print(test_y.value_counts(normalize=True))<line_sep>#%% --<line_sep># With Statify<line_sep>train_X, test_X, train_Y, test_Y = train_test_split(X, y, random_state = 56, stratify = y)<line_sep>#%% --<line_sep>print(train_Y.value_counts(normalize = True))<line_sep>print(test_Y.value_counts(normalize = True))<line_sep>#%% --<line_sep><line_sep>----- Error occurred in cell with num 6. The error trace is the following: ---------------------------------------------------------------------------<line_sep>NameError                                 Traceback (most recent call last)<line_sep>Cell In[7], line 2<line_sep>      1 # With Statify<line_sep>----> 2 train_X, test_X, train_Y, test_Y = train_test_split(X, y, random_state = 56, stratify = y)<line_sep><line_sep>NameError: name 'X' is not defined ----- Use defined functions for solving the error. You must not execute cell with cell number 6 After you perform actions which should solve the error, use function "finish" to indicate that. Executing the existing cell to solve errors is more preferable than changing the source of existing cells. You can either propose a new code for any of already existing cells, immediately execute it and got its output or create new cell with the following source code, immediately execute it and got its output or execute any of the cells without changing its code and got its output or execute finish function if you sure that error in needed self will not produce.<line_sep>
"""

if __name__ == "__main__":
    agent = ProxyAgent(token=os.environ["GRAZIE_TOKEN"])
    response = agent.interact(prompt=message)
    print(response)
    response = agent.interact(prompt="error solved")
    print(response)

#import dataset
import pandas as pd

df = pd.read_csv('../Data/loan_train.csv')
df.head()
#%% --
# Average Income of males and females
df.groupby(['Gender'])[['ApplicantIncome']].mean()

#%% --
# Average loan amount for different property areas like urban, rural
df.groupby(['Property_Area'])[['LoanAmount']].mean()
#%% --
# Compare loan status of different education backgrounds
df.groupby(['Education'])[['Loan_Status']].count()
#%% --

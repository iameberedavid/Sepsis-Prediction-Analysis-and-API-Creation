# Importations
from fastapi import FastAPI
import uvicorn
from typing import Union, Literal
import pandas as pd
import pickle, os
from pydantic import BaseModel

# Additional information to include in app description
additional_info = """
- PRG: Plasma Glucose
- PL: Blood Work Result-1 (mu U/ml)
- PR: Blood Pressure (mm Hg)
- SK: Blood Work Result-2 (mm)
- TS: Blood Work Result-3 (mu U/ml)
- M11: Body Mass Index (weight in kg/(height in m)^2)
- BD2: Blood Work Result-4 (mu U/ml)
- Age: Patient's Age (years)
- Insurance: If a patient holds a valid insurance card

Output:
- Sepsis: Positive if a patient in ICU will develop sepsis, Negative if a patient in ICU will not develop sepsis.
"""

# APP
app = FastAPI(
    title='Sepsis Prediction App',
    description='This app was built to predict if patients are Sepsis Positive or Sepsis Negative. '
                'It uses a machine learning model to make predictions based on patient data. '
                'Below is the kind of patient data required for the prediction, and the meaning of the prediction output.'
                + additional_info
)

@app.get('/')
async def root():
    return {
        'This app was built to predict if patients are Sepsis Positive or Sepsis Negative.'
    }

# Useful functions
def load_ml_components(fp):
    'Load the ML component to re-use in app'
    with open(fp, 'rb') as f:
        object = pickle.load(f)
        return object

# Variables and Constants
DIRPATH = os.path.dirname(os.path.realpath(__file__))
ml_core_fp = os.path.join(DIRPATH, 'export', 'ml_components.pkl')

# Load the Machine Learning components
ml_components_dict = load_ml_components(fp=ml_core_fp)
# end2end_pipeline = ml_components_dict['pipeline']

# Display execution
print(f'\n[Info] ML components loaded: {list(ml_components_dict.keys())}')

# Extract the ML components
model = ml_components_dict['model']
scaler = ml_components_dict['scaler']

# Input Modelling
class Sepsis(BaseModel):
    ## Input features
    PRG: float
    PL: float
    PR: float
    SK: float
    TS: float
    M11: float
    BD2: float
    Age: float
    Insurance: float

@app.post('/classify')
async def sepsis_prediction(sepsis: Sepsis):
    try:
        # Creation of Dataframe
        df = pd.DataFrame(
            {
                'PRG': [sepsis.PRG],
                'PL': [sepsis.PL],
                'PR': [sepsis.PR],
                'SK': [sepsis.SK],
                'TS': [sepsis.TS],
                'M11': [sepsis.M11],
                'BD2': [sepsis.BD2],
                'Age': [sepsis.Age],
                'Insurance': [sepsis.Insurance]
            }
        )
        print(f'[Info] Input data as DataFrame:\n{df.to_markdown()}')
        
        # Scale the input features
        scaled_df = scaler.transform(df)

        # Make prediction using the loaded model
        prediction = model.predict(scaled_df)

        # Extract the predicted label
        df['Sepsis'] = prediction

        # Define a mapping from class labels to human-readable labels (Positive and Negative)
        mapping = {0: 'Negative', 1: 'Positive'}

        # Add Sepsis column to the original test dataset using the mapping to identify Sepsis Positive and Sepsis Negative patients
        df['Sepsis'] = [mapping[x] for x in df['Sepsis']]

        # Print results
        print(f"The Patient has been predicted as : {df['Sepsis'].values[0]}")
        msg = 'Execution went fine'
        code = 1
        pred = df.to_dict('records')

    except Exception as e:
        print(f'Something went wrong during the Sepsis prediction: {str(e)}')
        msg = 'Execution went wrong'
        code = 0
        pred = None

    result = {'execution_msg': msg, 'execution_code': code, 'predictions': pred}
    return result

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
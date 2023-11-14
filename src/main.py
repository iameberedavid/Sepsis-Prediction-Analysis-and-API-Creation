# Importations
from fastapi import FastAPI
import uvicorn
from typing import Union, Literal
import pandas as pd
import pickle, os
from pydantic import BaseModel

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

# APP
app = FastAPI(title='Sepsis Prediction App')

@app.get('/')
async def root():
    return {
        'This app was built using streamlit to predict if patients are Sepsis Positive or Sepsis Negative'
    }

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

        # Make prediction
        predict = model.predict(scaled_df)
        
        # Calculate the confidence score by taking the maximum probability among predicted classes
        confidence_score = predict.max(axis=-1)

        # Calculate confidence score percentage and round to 2 decimal places
        confidence_score_percentage = round(confidence_score[0]*100),2
        print(f'The confidence score is {confidence_score_percentage}%')

        # Extract the class label with the highest probability as the predicted label
        df['predicted_label'] = predict.argmax(axis=-1)

        # Define a mapping from class labels to human-readable labels
        mapping = {0: 'Sepsis Negative', 1: 'Sepsis Positive'}

        # Replace the numeric predicted labels with human-readable labels using the mapping
        df['predicted_label'] = [mapping[x] for x in df['predicted_label']]

        # Store the confidence score percentage in the 'confidence_score' column
        df['confidence_score'] = f'{confidence_score_percentage}%'


        # Print results
        print(f'The Patient has been predicted as : {df["predicted_label"].values[0]}')
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
# AEGIS Data Portal

 - Front end - https://aegis-fe-1091670130981.europe-west2.run.app
 - Back end - https://aegis-be-1091670130981.europe-west2.run.app

How to run locally:
```
git clone https://github.com/EMBL-EBI-ABC/AEGIS.git

# Run BE
cd AEGIS/be
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080

# Run FE
cd AEGIS/fe
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
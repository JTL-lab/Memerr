# Memerr
A cloud-based social media application that allows users to effectively view, post, and interact with curated memes!

### Group Members 
- Julia Lewandowski (jtl2189)
- Robert Chang (rc3398)
- Uttam Gurram (ug2146)
- Kanishk Singh (ks4038)

### Architecture Diagram 
![alt text](https://github.com/JTL-lab/Memerr/blob/main/Memerr-Architecture.png?raw=true)

---
### Python venv Instructions
Run at the Project root folder.
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install --upgrade pip
```
To deactivate the venv: deactivate
---
#### Set Environment Variables
```
export FLASK_APP=app.py
export FLASk_ENV=development
```

#### Start Server
```
python3 -m flask run
```

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
#### Set Environment Variables - 
```
export FLASK_APP=app
export FLASk_ENV=development
```

#### Start Server
```
python3 -m flask run --host=0.0.0.0 --port=5001
```
---
#### ngrok Setup with Brew and Use
AWS App Client only allows for https and localhost in Callback URLs, so you may need to use ngrok to tunnel http traffic to https via ngrok.
```
brew install --cask ngrok
ngrok http https://127.0.0.1:5000
```
---
#### Instructions for Updating the code manually on EC2
Go to the parent directory of your frontend/
Ensure that the pem file is also in this directory
```
zip frontend.zip frontend/
scp -i "memerr-kp.pem" "frontend.zip" ec2-user@ec2-54-86-68-35.compute-1.amazonaws.com:/home/ec2-user
ssh -i "memerr-kp.pem" ec2-user@ec2-54-86-68-35.compute-1.amazonaws.com
unzip frontend.zip -d tmp/ # replace All
cd /home/ec2-user/frontend
source .venv/bin/activate
pip3 install -r requirements.txt
export FLASK_APP=app
export FLASk_ENV=development
python3 -m flask run --host=0.0.0.0 --port=5000
```
#### Instructions for running Gunicorn
After running the above. Run this
```
gunicorn --workers 3 --bind unix:/home/ec2-user/frontend/app.sock -m 007 app:app
```
Frontend App URL: http://ec2-54-86-68-35.compute-1.amazonaws.com:5000/
---
#### Instructions for NGINX setup
```
sudo yum update
sudo yum install nginx
sudo systemctl start nginx
sudo systemctl enable nginx
sudo vim /etc/nginx/nginx.conf
```
Update this file by adding a server block (see nginx.config). For Debug/Testing you will use Flask default server; for PROD, you will switch to Gunicorn and swap the proxy_pass line below and restart NGINX.
Then run
```
sudo nginx -t
sudo systemctl restart nginx
```
---
#### Instructions for Self-signed cert on EC2
```
sudo mkdir -p /etc/nginx/ssl/
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt
```
unzip frontend.zip -d tmp/
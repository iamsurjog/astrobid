import mysql.connector
from dotenv import dotenv_values

config = dotenv_values(".env")
print(config)
mydb = mysql.connector.connect(
  host=config["host"],
  user=config["user"],
  password=config["password"],
  database=config["database"]
)

print(mydb) 

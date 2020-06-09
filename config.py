import mysql.connector

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format('mysql', 'mysqldb','Scrubshrub', 'sse1881ess','scrubshrub.ciu4ws9ihfad.ap-southeast-2.rds.amazonaws.com', '3306', 'scrubshrub')
SQLALCHEMY_TRACK_MODIFICATIONS = True

MAPBOX_ACCESS_KEY = 'pk.eyJ1Ijoid2VpbSIsImEiOiJja2Ewd3VzbDUwNmc2M2ZwZDV6N3pwdmhvIn0.EJHXebn_BEqc2lzZU6KrRQ'

HOST = 'scrubshrub.ciu4ws9ihfad.ap-southeast-2.rds.amazonaws.com'
DB = 'scrubshrub'
USER = 'Scrubshrub'
PW = 'sse1881ess'
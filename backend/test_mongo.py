from pymongo import MongoClient

client = MongoClient('mongodb+srv://kavin88701:nR1Cc1SOsgRiXedQ@cluster0.01myarq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['Newpy']
print(db.list_collection_names())
